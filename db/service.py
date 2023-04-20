import datetime

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

import utils.web3
from db.models import Bytecode, UserOp


async def add_user_op(session: AsyncSession, user_op, **extra_data):
    user_op = dict(user_op)
    user_op.update(extra_data)
    user_op = UserOp(**user_op)
    session.add(user_op)

    return user_op


async def add_user_op_bytecodes(
    session: AsyncSession, user_op: UserOp, bytecode_hashes: list[str]
):
    for bytecode_hash in bytecode_hashes:
        bytecode = (
            await session.execute(
                select(Bytecode).where(Bytecode.hash == bytecode_hash)
            )
        ).scalar()

        if bytecode is None:
            bytecode = Bytecode(hash=bytecode_hash)
            session.add(bytecode)
            await session.flush()

        user_op.bytecodes.append(bytecode)


async def delete_user_op_by_sender(
    session: AsyncSession, sender: str
) -> UserOp:
    await session.execute(delete(UserOp).where(UserOp.sender == sender))


async def get_last_user_ops(session: AsyncSession, count: int) -> list[UserOp]:
    result = await session.execute(select(UserOp).limit(count))
    return result.scalars().all()


async def get_user_op_by_hash(session: AsyncSession, hash_: str) -> UserOp:
    result = await session.execute(select(UserOp).where(UserOp.hash == hash_))
    return result.scalar()


async def all_trusted_bytecodes(
    session: AsyncSession, bytecode_hashes: list[str]
) -> bool:
    result = await session.execute(
        select(Bytecode)
        .where(Bytecode.hash.in_(bytecode_hashes))
        .where(Bytecode.is_trusted == True)
    )
    return bool(len(result.all()) == len(bytecode_hashes))


async def any_banned_bytecodes(
    session: AsyncSession, bytecode_hashes: list[str]
) -> bool:
    result = await session.execute(
        select(Bytecode)
        .where(Bytecode.hash.in_(bytecode_hashes))
        .where(Bytecode.is_trusted == False)
        .limit(1)
    )
    return result.fetchone() is not None


async def any_user_op_with_another_sender_using_bytecodes(
    session: AsyncSession, bytecode_hashes: list[str], sender: str
) -> bool:
    now = datetime.datetime.now()
    result = await session.execute(
        select(UserOp)
        .where(UserOp.bytecodes.any(Bytecode.hash.in_(bytecode_hashes)))
        .where(UserOp.bytecodes.any(Bytecode.is_trusted.is_(None)))
        .where(UserOp.sender != sender)
        .where(UserOp.expires_at > now)
        .where(UserOp.tx_hash.is_(None))
        .limit(1)
    )
    return result.fetchone() is not None


async def update_bytecode_from_address(
    session: AsyncSession, address: str, is_trusted: bool
):
    hash_ = utils.web3.get_bytecode_hash(address)
    bytecode = (
        await session.execute(select(Bytecode).where(Bytecode.hash == hash_))
    ).scalar()
    if bytecode:
        bytecode.is_trusted = is_trusted
    else:
        bytecode = Bytecode(hash=hash_, is_trusted=is_trusted)
        session.add(bytecode)
