from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Bytecode, UserOp


async def add_user_op(session: AsyncSession, user_op, **extra_data):
    user_op = dict(user_op)
    user_op.update(extra_data)
    user_op = UserOp(**user_op)
    session.add(user_op)

    return user_op


async def get_user_op_by_hash(session: AsyncSession, hash_: str) -> UserOp:
    result = await session.execute(select(UserOp).where(UserOp.hash == hash_))
    return result.scalar()


async def add_user_op_bytecodes(
    session: AsyncSession, user_op: UserOp, bytecode_hashes: list[str]
):
    for bytecode_hash in bytecode_hashes:
        bytecode = (
            await session.execute(
                select(Bytecode).where(Bytecode.bytecode_hash == bytecode_hash)
            )
        ).scalar()

        if bytecode is None:
            bytecode = Bytecode(bytecode_hash=bytecode_hash)
            session.add(bytecode)
            await session.flush()

        user_op.bytecodes.append(bytecode)


async def update_bytecode(
    session: AsyncSession, bytecode_hash: str, is_trusted: bool
):
    bytecode = (
        await session.execute(
            select(Bytecode).where(Bytecode.bytecode_hash == bytecode_hash)
        )
    ).scalar()
    if bytecode:
        bytecode.is_trusted = is_trusted
    else:
        bytecode = Bytecode(bytecode_hash=bytecode_hash, is_trusted=is_trusted)
        session.add(bytecode)


async def delete_user_op_by_sender(
    session: AsyncSession, sender: str
) -> UserOp:
    await session.execute(delete(UserOp).where(UserOp.sender == sender))


async def get_last_user_ops(session: AsyncSession, count: int) -> list[UserOp]:
    result = await session.execute(select(UserOp).limit(count))
    return result.scalars().all()
