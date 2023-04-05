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

TEST_SEND_REQUEST = {
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


class AppClient:
    def __init__(self, client: AsyncClient):
        self.client = client

    async def send_user_op(self, request: dict, status_code=None) -> str:
        return await self._make_request(
            "eth_sendUserOperation", json=request, status_code=status_code
        )

    async def get_user_op(self, hash_: str, status_code=None) -> dict:
        return await self._make_request(
            "eth_getUserOperationByHash",
            json={"hash": hash_},
            status_code=status_code,
        )

    async def _make_request(self, method: str, json: dict, status_code=None):
        url = f"/api/{method}"
        response = await self.client.post(url, json=json)

        if status_code is not None:
            assert response.status_code == status_code

        return response.json()


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
async def client() -> AppClient:
    async with AsyncClient(app=app, base_url="https://localhost") as client:
        yield AppClient(client)


@pytest.fixture(scope="function")
def test_request():
    yield copy.deepcopy(TEST_SEND_REQUEST)
