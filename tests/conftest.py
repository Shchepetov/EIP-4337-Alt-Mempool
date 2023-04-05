import asyncio
import copy
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from db.base import engine, async_session, Base
from db.utils import init_models

SEND_DATA = {
    "user_op": {
        "sender": "0x4CDbDf63ae2215eDD6B673F9DABFf789A13D4270",
        "nonce": "0x00000000001000000000001000000",
        "init_code": "0x000000000001",
        "call_data": "0x000000000001",
        "call_gas_limit": "0x000000000001",
        "verification_gas_limit": "0x000000000001",
        "pre_verification_gas": "0x000000000001",
        "max_fee_per_gas": "0x000000000001",
        "max_priority_fee_per_gas": "0x000000000001",
        "paymaster_and_data": "0x000000000001",
        "signature": "0x000000000001",
    },
    "entry_point": "0xE40FdeB78BD64E7ab4BB12FA8C4046c85642eD6f",
}


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def init_test_models():
    await init_models(engine)


@pytest_asyncio.fixture(autouse=True)
async def session(
    init_test_models,
) -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

        # delete all data from all tables after test
        for name, table in Base.metadata.tables.items():
            await session.execute(delete(table))
        await session.commit()


@pytest_asyncio.fixture(scope="session")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="https://localhost") as client:
        yield client


@pytest.fixture(scope="function")
def test_request():
    yield copy.deepcopy(SEND_DATA)
