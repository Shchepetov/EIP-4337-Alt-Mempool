import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from brownie import (
    accounts,
    chain,
    web3,
    DepositPaymaster,
    EntryPoint,
    SimpleAccountFactory,
)
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

import app.config as config
import db.utils
from app.config import Settings
import app.constants as constants
from db.base import engine, async_session, Base


class AppClient:
    def __init__(self, client: AsyncClient):
        self.client = client

    async def send_user_op(self, request: dict, **kwargs) -> str:
        return await self._make_request(
            "eth_sendUserOperation", json=request, **kwargs
        )

    async def get_user_op(self, hash_: str, **kwargs) -> dict:
        return await self._make_request(
            "eth_getUserOperationByHash", json={"hash": hash_}, **kwargs
        )

    async def _make_request(
        self,
        method: str,
        json: dict,
        status_code=None,
        expected_error_message=None,
    ):
        url = f"/api/{method}"
        response = await self.client.post(url, json=json)
        response_json = response.json()

        if status_code is not None:
            assert response.status_code == status_code

        if expected_error_message is not None:
            assert "detail" in response_json
            assert expected_error_message in response_json["detail"]

        return response_json


class TestContracts:
    def __init__(self):
        self.entry_point = accounts[0].deploy(EntryPoint)
        self.simple_account_factory = accounts[0].deploy(
            SimpleAccountFactory, self.entry_point.address
        )
        self.paymaster = accounts[0].deploy(
            DepositPaymaster, self.entry_point.address
        )

        self.entry_point.depositTo(
            self.paymaster.address, {"value": "10 ether"}
        )

        chain.mine()
        chain.snapshot()


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def init_models():
    await db.utils.init_models(engine)


@pytest_asyncio.fixture(scope="session")
def contracts() -> dict:
    return TestContracts()


@pytest_asyncio.fixture(scope="session")
async def client(contracts) -> AppClient:
    config.settings = Settings(
        supported_entry_points=[contracts.entry_point.address],
        rpc_server=web3.provider.endpoint_uri,
    )

    from app.main import app

    async with AsyncClient(app=app, base_url="https://localhost") as client:
        yield AppClient(client)


@pytest_asyncio.fixture(autouse=True)
async def session(
    init_models,
) -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

        # reset test network state
        chain.revert()

        # delete all data from all tables after test
        for name, table in Base.metadata.tables.items():
            await session.execute(delete(table))
        await session.commit()


@pytest.fixture(scope="function")
def test_request(contracts):
    return {
        "user_op": {
            "sender": "0x4CDbDf63ae2215eDD6B673F9DABFf789A13D4270",
            "nonce": "0x00000000001000000000001000000",
            "init_code": contracts.simple_account_factory.address,
            "call_data": "0x000000000001",
            "call_gas_limit": hex(constants.CALL_GAS),
            "verification_gas_limit": "0x000000000001",
            "pre_verification_gas": hex(50000),
            "max_fee_per_gas": hex(100),
            "max_priority_fee_per_gas": hex(10),
            "paymaster_and_data": "0x00",
            "signature": "0x000000000001",
        },
        "entry_point": contracts.entry_point.address,
    }
