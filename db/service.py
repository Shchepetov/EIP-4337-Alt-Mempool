from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import UserOp


async def get_all(session: AsyncSession) -> list[UserOp]:
    result = await session.execute(select(UserOp).limit(20))
    return result.scalars().all()


async def add_user_op(session: AsyncSession, **user_op_schema) -> int:
    user_op_schema = UserOp(**user_op_schema)
    session.add(user_op_schema)
    return user_op_schema
