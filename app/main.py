from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, validator
from sqlalchemy.ext.asyncio import AsyncSession

import app.constants as constants
import db.service
import utils.user_op
import utils.web3
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
        if v == "0x":
            return 0

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
        if v == "0x":
            return b""

        validate_hex(v)
        if not (len(v) % 2 == 0):
            raise HTTPException(
                status_code=422, detail="Incorrect bytes string."
            )
        return bytes.fromhex(v[2:])


class SendRequest(BaseModel):
    user_op: UserOp
    entry_point: str

    _validate_address = validator("entry_point", allow_reuse=True)(
        validate_address
    )


class UserOpHash(BaseModel):
    @validator("hash")
    def bytes32_hash(cls, v):
        validate_hex(v)
        if len(v) != 66:
            raise HTTPException(
                status_code=422, detail="Not a 32-bytes hex value."
            )
        return v

    hash: str


class UserOpReceipt(BaseModel):
    accepted: bool
    tx_hash: str


class UserOpGasEstimation(BaseModel):
    pre_verification_gas: int
    verification_gas: int
    call_gas_limit: int


app = FastAPI()


@app.post("/api/eth_sendUserOperation", response_model=str)
async def send_user_operation(
    request: SendRequest, session: AsyncSession = Depends(get_session)
):
    await utils.validation.validate_entry_point(session, request.entry_point)
    entry_point = utils.web3.EntryPoint(request.entry_point)
    request.user_op.fill_hash(entry_point)
    (
        simulation_result,
        is_trusted,
        helper_contracts_bytecode_hashes,
    ) = await validate_user_op(session, request.user_op, entry_point)

    await db.service.delete_user_op_by_sender(session, request.user_op.sender)
    user_op = await db.service.add_user_op(
        session,
        request.user_op,
        entry_point=request.entry_point,
        pre_op_gas=simulation_result.pre_op_gas,
        is_trusted=is_trusted,
        valid_after=datetime.fromtimestamp(simulation_result.valid_after),
        valid_until=datetime.fromtimestamp(
            min(simulation_result.valid_until, constants.MAX_TIMESTAMP)
        ),
        expires_at=datetime.fromtimestamp(simulation_result.expires_at),
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
    await utils.validation.validate_entry_point(session, request.entry_point)
    entry_point = utils.web3.EntryPoint(request.entry_point)
    simulation_result = utils.validation.run_simulation(
        request.user_op, entry_point
    )
    call_gas_limit = utils.web3.estimate_gas(
        from_=entry_point.address,
        to=request.user_op.sender,
        data=request.user_op.call_data,
    )
    pre_verification_gas = request.user_op.get_calldata_gas()

    return UserOpGasEstimation(
        pre_verification_gas=pre_verification_gas,
        verification_gas=simulation_result.pre_op_gas,
        call_gas_limit=call_gas_limit,
    )


@app.post("/api/eth_getUserOperationByHash")
async def get_user_op_by_hash(
    request: UserOpHash, session: AsyncSession = Depends(get_session)
):
    user_op = await db.service.get_user_op_by_hash(session, request.hash)
    if not user_op:
        raise HTTPException(
            status_code=422, detail="The UserOp does not exist."
        )
    await db.service.refresh_user_op_receipt(user_op)
    return user_op.serialize()


@app.post("/api/eth_getUserOperationReceipt")
async def get_user_op_receipt(
    request: UserOpHash, session: AsyncSession = Depends(get_session)
):
    user_op = await db.service.get_user_op_by_hash(session, request.hash)
    if not user_op:
        raise HTTPException(
            status_code=422, detail="The UserOp does not exist."
        )

    tx_hash, accepted = await db.service.get_user_op_receipt(user_op)
    if tx_hash:
        return UserOpReceipt(tx_hash=tx_hash, accepted=accepted)


@app.post("/api/eth_supportedEntryPoints")
async def supported_entry_points(session: AsyncSession = Depends(get_session)):
    entry_points = await db.service.get_supported_entry_points(session)
    return [entry_point.address for entry_point in entry_points]


@app.post("/api/eth_lastUserOperations")
async def last_user_ops(session: AsyncSession = Depends(get_session)):
    user_ops = await db.service.get_last_user_ops(
        session, settings.last_user_ops_count
    )
    return [user_op.serialize() for user_op in user_ops]
