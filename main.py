import re
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, BaseSettings, validator, HttpUrl
from web3 import Web3

import utils


class Settings(BaseSettings):
    rpc_server: HttpUrl = "https://eth-goerli.public.blastapi.io"
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
        if not utils.is_hex(v):
            raise ValueError("Must be hexadecimal string")
        return bytes.fromhex(v)


settings = Settings()
app = FastAPI()


@app.get("/api/get_all")
async def get_all():
    return {"message": f"Hello!"}


@app.post("/api/user_op")
async def create_item(user_op: UserOperation):
    simulate_user_op(user_op)
    return {"message": f"Hello! {user_op}"}


def simulate_user_op(user_op: UserOperation):
    # abi = Path(settings.entry_point_abi_path).read_text()
    # w3 = Web3(Web3.HTTPProvider(settings.rpc_server))
    # entry_point = w3.eth.contract(address=settings.entry_point_address, abi=abi)
    # try:
    #     entry_point.functions.SimulateValidation().call()
    # except Exception as e:
    #     s = str(e)
    # else:
    #     raise HTTPException(status_code=500)
    pass
