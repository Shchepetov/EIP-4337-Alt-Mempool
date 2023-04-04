from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import UserOp


async def add_user_op(session: AsyncSession, user_op, **extra_data):
    user_op = dict(user_op)
    user_op.update(extra_data)
    user_op_schema = UserOp(**user_op)
    session.add(user_op_schema)


async def get_last_user_ops(session: AsyncSession, count: int) -> list[UserOp]:
    result = await session.execute(select(UserOp).limit(count))
    return result.scalars().all()
