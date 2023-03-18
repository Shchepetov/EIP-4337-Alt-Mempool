from sqlalchemy import Boolean
from sqlalchemy import BigInteger
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import LargeBinary
from sqlalchemy import String
from sqlalchemy import TIMESTAMP
from sqlalchemy.orm import relationship

from .base import Base


class UserOp(Base):
    __tablename__ = "user_ops"

    id = Column(Integer, autoincrement=True, primary_key=True)
    hash = Column(LargeBinary(length=32), unique=True, index=True)
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
    entry_point = Column(LargeBinary(length=20))
    signature = Column(LargeBinary)
    valid_after = Column(TIMESTAMP, index=True)
    valid_until = Column(TIMESTAMP)
    expires_at = Column(TIMESTAMP, index=True)
    is_trusted = Column(Boolean)
    tx_hash = Column(LargeBinary(length=32))
    user_operations_bytecodes = relationship('UserOpBytecode',
                                             back_populates='user_ops')


class Bytecode(Base):
    __tablename__ = 'bytecodes'

    id = Column(Integer, primary_key=True)
    bytecode_hash = Column(LargeBinary(length=32), unique=True, index=True)
    is_trusted = Column(Boolean)
    user_operations_bytecodes = relationship('UserOpBytecode',
                                             back_populates='bytecodes')


class UserOpBytecode(Base):
    __tablename__ = 'user_ops_bytecodes'

    id = Column(Integer, primary_key=True)
    user_op_id = Column(Integer, ForeignKey('user_ops.id'), index=True)
    bytecode_id = Column(Integer, ForeignKey('bytecodes.id'), index=True)
    user_operations_bytecodes = relationship('UserOp',
                                             back_populates='user_ops_bytecodes')
    user_operations_bytecodes = relationship('Bytecode',
                                             back_populates='user_ops_bytecodes')


class EntryPoint(Base):
    __tablename__ = 'entry_points'

    id = Column(Integer, primary_key=True)
    sender = Column(LargeBinary(length=20))


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, autoincrement=True, primary_key=True)
    token_hash = Column(LargeBinary(length=32), index=True)
    token_expires_at = Column(TIMESTAMP, index=True)
    requests_last_minute_count = Column(Integer)
    requests_last_day_count = Column(Integer)
    counter_updated_at = Column(TIMESTAMP)


class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50))
    ip_address = Column(String(15), unique=True, index=True)
