import os

os.environ["ENVIRONMENT"] = "TEST"

import asyncio
from collections.abc import AsyncGenerator

import brownie
import eth_abi
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from web3 import Web3

import db.service
import db.utils
import utils.web3
from db.base import engine, async_session, Base
from tests.utils.common_classes import TestClient, SendRequest


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def init_models():
    await db.utils.init_models(engine)


@pytest_asyncio.fixture(autouse=True)
async def session(init_models, contracts) -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        for name, table in Base.metadata.tables.items():
            await session.execute(delete(table))
        await db.service.update_entry_point(
            session, contracts.entry_point.address, True
        )
        await session.commit()

        yield session


@pytest_asyncio.fixture(scope="function")
async def client() -> TestClient:
    utils.web3.w3 = Web3(Web3.HTTPProvider(brownie.web3.provider.endpoint_uri))
    from app.main import app

    async with AsyncClient(app=app, base_url="https://localhost") as client:
        yield TestClient(client)


@pytest.fixture(scope="function")
def send_request(contracts, signer):
    return SendRequest(
        contracts.entry_point,
        contracts.simple_account_factory,
        contracts.test_paymaster_accept_all,
        signer,
        1,
    )


@pytest.fixture(scope="function")
def send_request2(contracts, signer):
    return SendRequest(
        contracts.entry_point,
        contracts.simple_account_factory,
        contracts.test_paymaster_accept_all,
        signer,
        2,
    )


@pytest.fixture(scope="function")
def send_request_with_expire_paymaster(contracts, signer, send_request):
    def f(valid_after: int, valid_until: int):
        time_range = eth_abi.encode(
            ["uint48", "uint48"], [valid_after, valid_until]
        )
        send_request.user_op.paymaster_and_data = (
            contracts.test_expire_paymaster.address + time_range.hex()
        )
        send_request.user_op.sign(signer, contracts.entry_point)

        return send_request

    return f
