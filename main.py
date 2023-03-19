import asyncio
from datetime import datetime

import typer
from fastapi import Depends, FastAPI
from pydantic import BaseModel, BaseSettings, HttpUrl, validator
from sqlalchemy.ext.asyncio import AsyncSession

import utils
from db.base import init_models, get_session
from db import service


class Settings(BaseSettings):
    rpc_server: HttpUrl = "https://goerli.blockpi.network/v1/rpc/public"
    supported_entry_points: list = ["0xE40FdeB78BD64E7ab4BB12FA8C4046c85642eD6f"]
    chain_id: int = 5
    expires_soon_interval: int = 10


class UserOp(BaseModel):
    sender: bytes
    nonce: int
    init_code: bytes
    call_data: bytes
    call_gas_limit: int
    verification_gas_limit: int
    pre_verification_gas: int
    max_fee_per_gas: int
    max_priority_fee_per_gas: int
    paymaster_and_data: bytes
    signature: bytes

    @validator("sender", pre=True)
    def address(cls, v):
        if isinstance(v, bytes):
            return f"0x{v.hex()}"

        if not utils.is_address(v):
            raise ValueError("Must be Ethereum address")

        return bytes.fromhex(v[2:])

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

    @validator("init_code", "call_data", "paymaster_and_data", "signature", pre=True)
    def hex(cls, v):
        return bytes.fromhex(v) if isinstance(v, str) else v.hex()


class UserOpSchema(UserOp):
    id: int
    sig_failed: bool
    valid_after: datetime
    valid_until: datetime
    validated_at: datetime

    @classmethod
    def from_db(cls, user_op_schema):
        d = user_op_schema.__dict__
        d.pop("_sa_instance_state")
        return cls(**d)

class SendRequest(BaseModel):
    user_op: UserOp
    entry_point: str

    @validator("entry_point", pre=True)
    def entry_point(cls, v):
        if v not in settings.supportedEntryPoints:
            raise ValueError("Must be in range [0, 2**256)")

class UserOpHash(BaseModel):
    hash: int

settings = Settings()
app = FastAPI()
cli = typer.Typer()


@cli.command()
def db_init_models():
    asyncio.run(init_models())
    print("Models initialized")


@app.get("/api/eth_getUserOperations")
async def get_all(session: AsyncSession = Depends(get_session)):
    user_op_schemes = await service.get_all(session)
    return [UserOpSchema.from_db(user_op_schema) for user_op_schema in user_op_schemes]


@app.post("/api/eth_sendUserOperation", response_model=int)
async def send_user_operation(user_op: UserOp, session: AsyncSession = Depends(get_session)):
    validation_result, validated_at = utils.validate_user_op(
        user_op,
        settings.rpc_server,
        settings.entry_point_address,
        settings.expires_soon_interval,
        check_forbidden_opcodes=True,
    )
    # TODO: Повторить пункт Client behavior upon receiving a UserOp
    user_op_schema = await service.add_user_op(
        session,
        **dict(user_op),
        sig_failed=validation_result.sig_failed,
        valid_after=datetime.fromtimestamp(validation_result.valid_after),
        valid_until=datetime.fromtimestamp(validation_result.valid_until),
        validated_at=datetime.fromtimestamp(validated_at),
    )
    try:
        await session.commit()
        return user_op_schema.id
    except:
        await session.rollback()
        raise ValueError(f"Can't save to the DB.")


@app.get("/api/eth_estimateUserOperationGas")
async def estimate_user_op(request: SendRequest,
                           session: AsyncSession = Depends(get_session)):
    pass


@app.get("/api/eth_getUserOperationByHash")
async def get_user_op_by_hash(request: UserOpHash,
                              session: AsyncSession = Depends(get_session)):
    pass


@app.get("/api/eth_getUserOperationReceipt")
async def get_user_op_receipt(request: UserOpHash,
                              session: AsyncSession = Depends(get_session)):
    pass


@app.get("/api/eth_supportedEntryPoints")
async def supported_entry_points(session: AsyncSession = Depends(get_session)):
    pass


if __name__ == "__main__":
    cli()
