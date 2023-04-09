import hashlib
from datetime import datetime

import web3
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Extra, validator
from sqlalchemy.ext.asyncio import AsyncSession

import db.service
from app.config import settings
from db.utils import get_session
from utils.validation import validate_address, validate_hex, validate_user_op
from utils.user_op import UserOpBase


class UserOp(BaseModel, UserOpBase):
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

    _validate_address = validator("sender", allow_reuse=True)(validate_address)

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
        validate_hex(v)
        v = int(v, 16)
        if not 0 <= v < 2**256:
            raise HTTPException(
                status_code=422, detail="Must be in range [0, 2**256)."
            )
        return v

    @validator(
        "init_code", "call_data", "paymaster_and_data", "signature", pre=True
    )
    def bytes_(cls, v):
        validate_hex(v)
        if not (len(v) % 2 == 0 or v == "0x0"):
            raise HTTPException(
                status_code=422, detail="Incorrect bytes string."
            )
        return v

    def fill_hash(self) -> None:
        data = "".join(
            (hex(v) if isinstance(v, int) else v)[2:].zfill(64)
            for v in self.values()[:-1]
        )

        self.hash = "0x" + hashlib.sha3_256(bytes.fromhex(data)).digest().hex()


class SendRequest(BaseModel):
    user_op: UserOp
    entry_point: str

    _validate_address = validator("entry_point", allow_reuse=True)(
        validate_address
    )

    @validator("entry_point")
    def supported_entry_point(cls, v):
        if v.lower() not in map(str.lower, settings.supported_entry_points):
            raise HTTPException(
                status_code=422, detail="EntryPoint is not supported."
            )
        return v


class UserOpHash(BaseModel):
    _validate_hash = validator("hash", allow_reuse=True)(validate_hex)
    hash: str


app = FastAPI()


@app.post("/api/eth_sendUserOperation", response_model=str)
async def send_user_operation(
    request: SendRequest, session: AsyncSession = Depends(get_session)
):
    request.user_op.fill_hash()

    validation_result = await validate_user_op(
        session,
        settings.rpc_server,
        request.user_op,
        request.entry_point,
        settings.expires_soon_interval,
        check_forbidden_opcodes=True,
    )

    if request.user_op.sender != web3.constants.ADDRESS_ZERO:
        await db.service.delete_user_op_by_sender(
            session, request.user_op.sender
        )

    await db.service.add_user_op(
        session,
        request.user_op,
        entry_point=request.entry_point,
        valid_after=datetime.fromtimestamp(validation_result.valid_after),
        valid_until=datetime.fromtimestamp(validation_result.valid_until),
    )

    await session.commit()
    return request.user_op.hash


@app.post("/api/eth_estimateUserOperationGas")
async def estimate_user_op(
    request: SendRequest, session: AsyncSession = Depends(get_session)
):
    return request


@app.post("/api/eth_getUserOperationByHash")
async def get_user_op_by_hash(
    request: UserOpHash, session: AsyncSession = Depends(get_session)
):
    user_op_schema = await db.service.get_user_op_by_hash(session, request.hash)
    return user_op_schema


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
    user_op_schemes = await db.service.get_last_user_ops(
        session, settings.last_user_ops_count
    )
    return [user_op_schema for user_op_schema in user_op_schemes]
