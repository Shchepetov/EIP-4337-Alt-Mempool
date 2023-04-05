import hashlib
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from db.service import add_user_op, get_last_user_ops
from db.utils import get_session
from utils.validation import validate_address, validate_hex, validate_user_op


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
        allow_mutation = False

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
                status_code=422, detail="Must be in range [0, 2**256)"
            )
        return v

    @validator(
        "init_code", "call_data", "paymaster_and_data", "signature", pre=True
    )
    def bytes_(cls, v):
        validate_hex(v)
        if not (len(v) % 2 == 0 or v == "0x0"):
            raise HTTPException(
                status_code=422, detail="Incorrect bytes string"
            )
        return v

    def hash(self) -> str:
        data = "".join(
            (hex(v) if isinstance(v, int) else v)[2:].zfill(64)
            for v in [
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
            ]
        )

        return "0x" + hashlib.sha3_256(bytes.fromhex(data)).digest().hex()


class SendRequest(BaseModel):
    user_op: UserOp
    entry_point: str

    class Config:
        allow_mutation = False

    _validate_address = validator("entry_point", allow_reuse=True)(
        validate_address
    )

    @validator("entry_point")
    def supported_entry_point(cls, v):
        if v.lower() not in map(str.lower, settings.supported_entry_points):
            raise HTTPException(
                status_code=422, detail="EntryPoint is not supported"
            )
        return v


class UserOpHash(BaseModel):
    hash: int


app = FastAPI()


@app.post("/api/eth_sendUserOperation", response_model=str)
async def send_user_operation(
    request: SendRequest, session: AsyncSession = Depends(get_session)
):
    validation_result = validate_user_op(
        request.user_op,
        settings.rpc_server,
        request.entry_point,
        settings.expires_soon_interval,
        check_forbidden_opcodes=True,
    )

    user_op_hash = request.user_op.hash()
    await add_user_op(
        session,
        request.user_op,
        entry_point=request.entry_point,
        hash=user_op_hash,
        valid_after=datetime.fromtimestamp(validation_result.valid_after),
        valid_until=datetime.fromtimestamp(validation_result.valid_until),
    )

    await session.commit()
    return user_op_hash
    # try:
    #     await session.commit()
    #     return user_op_hash
    # except Exception as e:
    #     print(f"Exception: {e}")
    #     await session.rollback()
    #     raise HTTPException(status_code=500, detail="Can't save to the DB.")


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
