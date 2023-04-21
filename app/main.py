from datetime import datetime

from brownie import EntryPoint
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, validator
from sqlalchemy.ext.asyncio import AsyncSession

import app.constants as constants
import db.service
import utils.user_op
from app.config import settings
from db.utils import get_session
from utils.validation import validate_address, validate_hex, validate_user_op


class UserOp(utils.user_op.UserOp):
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
    entry_point = EntryPoint.at(request.entry_point)
    request.user_op.fill_hash(entry_point)
    (
        validation_result,
        is_trusted,
        expires_at,
        helper_contracts_bytecode_hashes,
    ) = await validate_user_op(session, request.user_op, entry_point)

    await db.service.delete_user_op_by_sender(session, request.user_op.sender)
    user_op = await db.service.add_user_op(
        session,
        request.user_op,
        is_trusted=is_trusted,
        entry_point=request.entry_point,
        valid_after=datetime.fromtimestamp(validation_result.valid_after),
        valid_until=datetime.fromtimestamp(
            min(validation_result.valid_until, constants.MAX_TIMESTAMP)
        ),
        expires_at=datetime.fromtimestamp(expires_at),
    )
    await db.service.add_user_op_bytecodes(
        session, user_op, helper_contracts_bytecode_hashes
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
    return await db.service.get_last_user_ops(
        session, settings.last_user_ops_count
    )
