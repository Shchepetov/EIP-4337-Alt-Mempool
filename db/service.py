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
    last_user_ops = []
    result = (await session.execute(select_valid_user_ops())).scalars()

    for user_op in result:
        processed = await refresh_user_op_status(user_op)
        if not processed:
            last_user_ops.append(user_op)
            count -= 1
        if count == 0:
            break

    return last_user_ops


def select_valid_user_ops():
    now = datetime.datetime.now()
    return (
        select(UserOp)
        .where(UserOp.expires_at > now)
        .where(UserOp.tx_hash.is_(None))
    )


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


async def any_forbidden_bytecodes(
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
    result = await session.execute(
        select_valid_user_ops()
        .where(UserOp.bytecodes.any(Bytecode.hash.in_(bytecode_hashes)))
        .where(UserOp.bytecodes.any(Bytecode.is_trusted.is_(None)))
        .where(UserOp.sender != sender)
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

    if not is_trusted:
        await session.execute(
            delete(UserOp).where(UserOp.bytecodes.any(Bytecode.hash == hash_))
        )


async def refresh_user_op_status(user_op: UserOp) -> bool:
    tx_hash = utils.web3.get_execution_tx_hash(
        user_op.hash, user_op.entry_point
    )
    if tx_hash:
        user_op.tx_hash = tx_hash.hex()
        return True

    return False
