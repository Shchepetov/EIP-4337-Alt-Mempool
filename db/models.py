from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import BigInteger
from sqlalchemy import LargeBinary
from sqlalchemy import Boolean
from sqlalchemy import TIMESTAMP

from .base import Base


class UserOp(Base):
    __tablename__ = "user_ops"

    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    sender = Column(LargeBinary(length=20))
    nonce = Column(BigInteger)
    init_code = Column(LargeBinary)
    call_data = Column(LargeBinary)
    call_gas_limit = Column(BigInteger)
    verification_gas_limit = Column(BigInteger)
    pre_verification_gas = Column(BigInteger)
    max_fee_per_gas = Column(BigInteger)
    max_priority_fee_per_gas = Column(BigInteger)
    paymaster_and_data = Column(LargeBinary)
    signature = Column(LargeBinary)
    sig_failed = Column(Boolean)
    valid_after = Column(TIMESTAMP)
    valid_until = Column(TIMESTAMP)
    validated_at = Column(TIMESTAMP)
