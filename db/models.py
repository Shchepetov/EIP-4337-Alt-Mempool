from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import LargeBinary
from sqlalchemy import String
from sqlalchemy import TIMESTAMP
from sqlalchemy import Table
from sqlalchemy import TypeDecorator
from sqlalchemy.orm import Relationship

from .base import Base


class Uint256(TypeDecorator):
    impl = LargeBinary(32)

    def process_bind_param(self, value, dialect):
        if value is not None:
            if not isinstance(value, bytes):
                value = value.to_bytes(32, byteorder="big")
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = int.from_bytes(value, byteorder="big")
        return value


user_ops_bytecodes = Table(
    "user_ops_bytecodes",
    Base.metadata,
    Column(
        "user_op_id", Integer, ForeignKey("user_ops.id", ondelete="CASCADE")
    ),
    Column(
        "bytecode_id", Integer, ForeignKey("bytecodes.id", ondelete="CASCADE")
    ),
)


class UserOp(Base):
    __tablename__ = "user_ops"

    id = Column(Integer, autoincrement=True, primary_key=True)
    hash = Column(String(length=66), unique=True, index=True)
    sender = Column(String(length=42))
    nonce = Column(Uint256)
    init_code = Column(String)
    call_data = Column(String)
    call_gas_limit = Column(Uint256)
    verification_gas_limit = Column(Uint256)
    pre_verification_gas = Column(Uint256)
    max_fee_per_gas = Column(Uint256)
    max_priority_fee_per_gas = Column(Uint256)
    paymaster_and_data = Column(String)
    entry_point = Column(String(length=42))
    signature = Column(String)
    valid_after = Column(TIMESTAMP, index=True)
    valid_until = Column(TIMESTAMP)
    expires_at = Column(TIMESTAMP, index=True)
    is_trusted = Column(Boolean)
    tx_hash = Column(String(length=66))
    bytecodes = Relationship(
        "Bytecode",
        secondary=user_ops_bytecodes,
        back_populates="user_ops",
        lazy="noload",
    )


class Bytecode(Base):
    __tablename__ = "bytecodes"

    id = Column(Integer, primary_key=True)
    bytecode_hash = Column(String(length=66), unique=True, index=True)
    is_trusted = Column(Boolean)
    user_ops = Relationship(
        "UserOp",
        secondary=user_ops_bytecodes,
        back_populates="bytecodes",
        lazy="noload",
    )


class EntryPoint(Base):
    __tablename__ = "entry_points"

    id = Column(Integer, primary_key=True)
    sender = Column(String(length=42))


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, autoincrement=True, primary_key=True)
    token_hash = Column(String(length=66), index=True)
    token_expires_at = Column(TIMESTAMP, index=True)
    requests_last_minute_count = Column(Integer)
    requests_last_day_count = Column(Integer)
    counter_updated_at = Column(TIMESTAMP)
