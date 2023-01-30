from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, BaseSettings, validator, HttpUrl
from web3 import Web3
from web3.constants import ADDRESS_ZERO

import utils


class Settings(BaseSettings):
    rpc_server: HttpUrl = "https://goerli.blockpi.network/v1/rpc/public"
    entry_point_address: str = "0xE40FdeB78BD64E7ab4BB12FA8C4046c85642eD6f"
    entry_point_abi_path: str = "EntryPoint.abi"


class UserOperation(BaseModel):
    sender: str
    nonce: int
    init_code: str
    call_data: str
    call_gas_limit: int
    verification_gas_limit: int
    pre_verification_gas: int
    max_fee_per_gas: int
    max_priority_fee_per_gas: int
    paymaster_and_data: str
    signature: str

    @validator("sender")
    def address(cls, v):
        if not utils.is_address(v):
            raise ValueError("Must be Ethereum address")
        return v

    @validator(
        "nonce",
        "call_gas_limit",
        "verification_gas_limit",
        "pre_verification_gas",
        "max_fee_per_gas",
        "max_priority_fee_per_gas",
    )
    def uint256(cls, v):
        if not utils.is_uint256(v):
            raise ValueError("Must be in range [0, 2**256)")
        return v

    @validator("init_code", "call_data", "paymaster_and_data", "signature")
    def hex(cls, v):
        return bytes.fromhex(v)


class ValidationResult:
    pre_op_gas: int
    prefund: int
    sig_failed: bool
    valid_after: int
    valid_until: int
    paymaster_context: bytes = bytes()
    sender_stake: int
    sender_unstake_delay_sec: int
    factory_stake: int
    factory_unstake_delay_sec: int
    actual_aggregator: str
    aggregator_stake: int
    aggregator_unstake_delay_sec: int

    def __init__(self, simulation_return_data: bytes, with_aggregation=False):
        data = (
            simulation_return_data[32 * k : 32 * (k + 1)]
            for k in range(len(simulation_return_data) // 32)
        )

        for field in [
            "pre_op_gas",
            "prefund",
            "sig_failed",
            "valid_after",
            "valid_until",
        ]:
            setattr(self, field, int.from_bytes(next(data), byteorder="big"))

        n_bytes = int.from_bytes(next(data), byteorder="big")
        for _ in range(n_bytes):
            self.paymaster_context += next(data)

        for field in [
            "sender_stake",
            "sender_unstake_delay_sec",
            "factory_stake",
            "factory_unstake_delay_sec",
        ]:
            setattr(self, field, int.from_bytes(next(data), byteorder="big"))

        if with_aggregation:
            self.actual_aggregator = "0x" + next(data).hex()[-40:]
            for field in ["aggregator_stake", "aggregator_unstake_delay_sec"]:
                setattr(self, field, int.from_bytes(next(data), byteorder="big"))


settings = Settings()
app = FastAPI()


@app.get("/api/get_all")
async def get_all():
    return {"message": f"Hello!"}


@app.post("/api/user_op")
async def create_item(user_op: UserOperation):
    validation_result = validate_user_op(user_op, check_forbidden_opcodes=True)
    return {"message": f"Result: {validation_result}"}


def validate_user_op(
    user_op: UserOperation, check_forbidden_opcodes=False
) -> ValidationResult:
    w3 = Web3(Web3.HTTPProvider(settings.rpc_server))
    abi = Path(settings.entry_point_abi_path).read_text()
    entry_point = w3.eth.contract(address=settings.entry_point_address, abi=abi)
    call_data = entry_point.encodeABI("simulateValidation", [v for k, v in user_op])
    result = w3.provider.make_request(
        "debug_traceCall",
        [
            {
                "from": ADDRESS_ZERO,
                "to": settings.entry_point_address,
                "data": call_data,
            },
            "latest",
        ],
    )["result"]

    return_value = result["returnValue"]
    selector = return_value[:8]
    if selector == "f04297e9":  # ValidationResult
        validation_result = ValidationResult(bytes.fromhex(return_value[8:]))
    elif selector == "356877a3":  # ValidationResultWithAggregation
        validation_result = ValidationResult(
            bytes.fromhex(return_value[8:]), with_aggregation=True
        )
    else:
        raise ValueError(f"Simulation failed with return data: {return_value}")

    if check_forbidden_opcodes and utils.have_forbidden_opcodes(
        result["result"], initializing=True if len(user_op.init_code) else False
    ):
        raise ValueError("UserOp have forbidden opcodes")

    return validation_result
