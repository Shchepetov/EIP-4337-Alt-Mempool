import asyncio
from datetime import datetime

import typer
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, BaseSettings, HttpUrl, validator
from sqlalchemy.ext.asyncio import AsyncSession

from db.base import init_models, get_session
from db.service import add_user_op, get_last_user_ops
from utils.validation import is_address, is_hex, validate_user_op


class Settings(BaseSettings):
    rpc_server: HttpUrl = "https://goerli.blockpi.network/v1/rpc/public"
    supported_entry_points: list = [
        "0xE40FdeB78BD64E7ab4BB12FA8C4046c85642eD6f",
    ]
    chain_id: int = 5
    expires_soon_interval: int = 10
    last_user_ops_count: int = 100


def address(v):
    if not is_address(v):
        raise HTTPException(status_code=422, detail="Must be Ethereum address")

    return v


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

    _validate_sender = validator("sender", allow_reuse=True)(address)

    @validator(
        "nonce",
        "call_gas_limit",
        "verification_gas_limit",
        "pre_verification_gas",
        "max_fee_per_gas",
        "max_priority_fee_per_gas",
        pre=True,
    )
    def uint256(cls, v):
        v = int(v, 16)
        if not 0 <= v < 2**256:
            raise HTTPException(
                status_code=422, detail="Must be in range [0, 2**256)"
            )
        return v

    @validator(
        "init_code", "call_data", "paymaster_and_data", "signature", pre=True
    )
    def bytes_(cls, v):
        if not (is_hex(v) and (len(v) % 2 == 0 or v == "0x0")):
            raise HTTPException(
                status_code=422, detail="Incorrect bytes string"
            )
        return v


class SendRequest(BaseModel):
    user_op: UserOp
    entry_point: str

    _validate_entry_point = validator("entry_point", allow_reuse=True)(address)

    @validator("entry_point", pre=True)
    def supported_entry_point(cls, v):
        if v.lower() not in map(str.lower, settings.supported_entry_points):
            raise HTTPException(
                status_code=422, detail="EntryPoint is not supported"
            )
        return v


class UserOpHash(BaseModel):
    hash: int


settings = Settings()
app = FastAPI()
cli = typer.Typer()


@cli.command()
def db_init_models():
    asyncio.run(init_models())
    print("Models initialized")


@app.post("/api/eth_sendUserOperation", response_model=str)
async def send_user_operation(
    request: SendRequest, session: AsyncSession = Depends(get_session)
):
    validation_result, validated_at = validate_user_op(
        request.user_op,
        settings.rpc_server,
        request.entry_point,
        settings.expires_soon_interval,
        check_forbidden_opcodes=True,
    )
    # TODO: Повторить пункт Client behavior upon receiving a UserOp
    user_op_hash = await add_user_op(
        session,
        **dict(request.user_op),
        sig_failed=validation_result.sig_failed,
        valid_after=datetime.fromtimestamp(validation_result.valid_after),
        valid_until=datetime.fromtimestamp(validation_result.valid_until),
        validated_at=datetime.fromtimestamp(validated_at),
    )
    try:
        await session.commit()
        return user_op_hash
    except:
        await session.rollback()
        raise HTTPException(status_code=422, detail="Can't save to the DB.")


@app.post("/api/eth_estimateUserOperationGas")
async def estimate_user_op(
    request: SendRequest, session: AsyncSession = Depends(get_session)
):
    return request


@app.post("/api/eth_getUserOperationByHash")
async def get_user_op_by_hash(
    request: UserOpHash, session: AsyncSession = Depends(get_session)
):
    pass


@app.post("/api/eth_getUserOperationReceipt")
async def get_user_op_receipt(
    request: UserOpHash, session: AsyncSession = Depends(get_session)
):
    pass


@app.post("/api/eth_supportedEntryPoints")
async def supported_entry_points(session: AsyncSession = Depends(get_session)):
    pass


@app.post("/api/eth_lastUserOperations")
async def last_user_ops(session: AsyncSession = Depends(get_session)):
    user_op_schemes = await get_last_user_ops(
        session, settings.last_user_ops_count
    )
    return [user_op_schema for user_op_schema in user_op_schemes]


if __name__ == "__main__":
    cli()
