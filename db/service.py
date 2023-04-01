from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import UserOp


async def add_user_op(session: AsyncSession, **user_op_schema) -> str:
    user_op_schema = UserOp(**user_op_schema)
    session.add(user_op_schema)
    return user_op_schema.hash


async def get_last_user_ops(session: AsyncSession, count: int) -> list[UserOp]:
    result = await session.execute(select(UserOp).limit(count))
    return result.scalars().all()
