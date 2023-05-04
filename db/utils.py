import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import settings
from db.base import Base, async_session


async def create_database(db_name):
    try:
        await asyncpg.connect(database=db_name)
    except asyncpg.InvalidCatalogNameError:
        sys_conn = await asyncpg.connect(
            database="template1",
        )
        await sys_conn.execute(f"CREATE DATABASE {db_name}")
        await sys_conn.close()


async def init_models(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def create_and_init(db_name):
    await create_database(db_name)
    engine = create_async_engine(f"{settings.get_db_url()}/{db_name}")
    await init_models(engine)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
        await session.commit()
