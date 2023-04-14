import eth_abi
from brownie import web3
from pydantic import BaseModel, Extra

from app.config import settings

DEFAULTS_FOR_USER_OP = {
    "sender": "0x4CDbDf63ae2215eDD6B673F9DABFf789A13D4270",
    "nonce": 1,
    "init_code": "0x",
    "call_data": "0x",
    "call_gas_limit": 200000000,
    "verification_gas_limit": settings.max_verification_gas_limit,
    "pre_verification_gas": 21000,
    "max_fee_per_gas": settings.min_max_fee_per_gas,
    "max_priority_fee_per_gas": settings.min_max_priority_fee_per_gas,
    "paymaster_and_data": "0x",
    "signature": "0x0",
}


class UserOp(BaseModel):
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

    class Config:
        extra = Extra.allow

    def get_calldata_gas(self) -> int:
        calldata_bytes = self.encode()
        zero_bytes_count = calldata_bytes.count(0)

        return 4 * zero_bytes_count + 16 * (
            len(calldata_bytes) - zero_bytes_count
        )

    def get_required_prefund(self, with_paymaster=False):
        return self.max_fee_per_gas * (
            self.pre_verification_gas
            + self.verification_gas_limit * (3 if with_paymaster else 1)
            + self.call_gas_limit
        )

    def fill_hash(self) -> None:
        self.hash = web3.keccak(self.encode(with_signature=False)).hex()

    def encode(self, with_signature=True) -> bytes:
        types = [
            "address",  # sender
            "uint256",  # nonce
            "bytes",  # init_code
            "bytes",  # call_data
            "uint256",  # call_gas_limit
            "uint256",  # verification_gas_limit
            "uint256",  # pre_verification_gas
            "uint256",  # max_fee_per_gas
            "uint256",  # max_priority_fee_per_gas
            "bytes",  # paymaster_and_data
        ]
        values = [
            self.sender,
            self.nonce,
            web3.toBytes(hexstr=self.init_code),
            web3.toBytes(hexstr=self.call_data),
            self.call_gas_limit,
            self.verification_gas_limit,
            self.pre_verification_gas,
            self.max_fee_per_gas,
            self.max_priority_fee_per_gas,
            web3.toBytes(hexstr=self.paymaster_and_data),
        ]

        if with_signature:
            types.append("bytes")
            values.append(web3.toBytes(hexstr=self.signature))

        return eth_abi.encode(types, values)

    def sign(self, owner_address, entry_point):
        self.signature = (
            web3.eth.sign(
                owner_address, data=entry_point.getUserOpHash(self.values())
            ).hex()[:-2]
            + "1c"
        )

    def values(self) -> list:
        return [
            self.sender,
            self.nonce,
            self.init_code,
            self.call_data,
            self.call_gas_limit,
            self.verification_gas_limit,
            self.pre_verification_gas,
            self.max_fee_per_gas,
            self.max_priority_fee_per_gas,
            self.paymaster_and_data,
            self.signature,
        ]
