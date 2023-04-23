import datetime

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

import utils.web3
from db.models import Bytecode, UserOp, EntryPoint


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
    await session.execute(
        where_user_op_valid(delete(UserOp).where(UserOp.sender == sender))
    )


async def get_last_user_ops(session: AsyncSession, count: int) -> list[UserOp]:
    last_user_ops = []
    result = (
        await session.execute(where_user_op_valid(select(UserOp)))
    ).scalars()

    for user_op in result:
        processed = await refresh_user_op_receipt(user_op)
        if not processed:
            last_user_ops.append(user_op)
            count -= 1
        if count == 0:
            break

    return last_user_ops


def where_user_op_valid(expression):
    now = datetime.datetime.now()
    return expression.where(UserOp.expires_at > now).where(
        UserOp.tx_hash.is_(None)
    )


async def get_user_op_by_hash(session: AsyncSession, hash_: str) -> UserOp:
    result = await session.execute(select(UserOp).where(UserOp.hash == hash_))
    return result.scalar()


async def get_user_op_receipt(user_op: UserOp) -> (str, bool):
    await refresh_user_op_receipt(user_op)
    return user_op.tx_hash, user_op.accepted


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
        where_user_op_valid(
            select(UserOp)
            .where(UserOp.bytecodes.any(Bytecode.hash.in_(bytecode_hashes)))
            .where(UserOp.bytecodes.any(Bytecode.is_trusted.is_(None)))
            .where(UserOp.sender != sender)
        ).limit(1)
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
            delete(UserOp)
            .where(UserOp.bytecodes.any(Bytecode.hash == hash_))
            .where(UserOp.tx_hash == None)
        )


async def refresh_user_op_receipt(user_op: UserOp) -> bool:
    if user_op.tx_hash:
        return True

    tx_hash, accepted = utils.web3.get_user_op_receipt(
        user_op.hash, user_op.entry_point
    )
    if tx_hash:
        user_op.accepted = accepted
        user_op.tx_hash = tx_hash.hex()
        return True

    return False


async def get_supported_entry_points(session: AsyncSession) -> list[EntryPoint]:
    result = await session.execute(select(EntryPoint))
    return result.scalars().all()


async def is_entry_point_supported(
    session: AsyncSession, entry_point_address: str
) -> bool:
    result = await session.execute(
        select(EntryPoint)
        .where(func.lower(EntryPoint.address) == entry_point_address.lower())
        .limit(1)
    )
    return result.fetchone() is not None


async def update_entry_point(
    session: AsyncSession, entry_point_address: str, is_supported: bool
):
    if is_supported:
        is_already_supported = await is_entry_point_supported(
            session, entry_point_address
        )
        if not is_already_supported:
            session.add(EntryPoint(address=entry_point_address))
    else:
        await session.execute(
            delete(EntryPoint).where(
                func.lower(EntryPoint.address) == entry_point_address.lower()
            )
        )
