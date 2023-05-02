import asyncio
from collections.abc import AsyncGenerator

import eth_abi
import pytest
import pytest_asyncio
from brownie import chain
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

import db.service
import db.utils
import utils.deployments
from db.base import engine, async_session, Base
from tests.utils.common_classes import SendRequest


class AppClient:
    def __init__(self, client: AsyncClient):
        self.client = client

    async def send_user_op(self, request: dict, **kwargs) -> str:
        return await self._make_request(
            "eth_sendUserOperation", json=request, **kwargs
        )

    async def estimate_user_op(self, request: dict, **kwargs) -> dict:
        return await self._make_request(
            "eth_estimateUserOperationGas", json=request, **kwargs
        )

    async def get_user_op(self, hash_: str, **kwargs) -> dict:
        return await self._make_request(
            "eth_getUserOperationByHash", json={"hash": hash_}, **kwargs
        )

    async def get_user_op_receipt(self, hash_: str, **kwargs) -> dict:
        return await self._make_request(
            "eth_getUserOperationReceipt", json={"hash": hash_}, **kwargs
        )

    async def supported_entry_points(self, **kwargs) -> dict:
        return await self._make_request(
            "eth_supportedEntryPoints", json={}, **kwargs
        )

    async def last_user_ops(self, **kwargs) -> dict:
        return await self._make_request(
            "eth_lastUserOperations", json={}, **kwargs
        )

    async def _make_request(
        self,
        method: str,
        json: dict,
        expected_error_message=None,
    ):
        url = f"/api/{method}"
        response = await self.client.post(url, json=json)
        response_json = response.json()

        if response.status_code == 200:
            if expected_error_message is not None:
                raise Exception(
                    f'Expected error message "{expected_error_message}", but '
                    f"response code is 200"
                )
            return response_json

        if expected_error_message is not None:
            if expected_error_message not in response_json["detail"]:
                raise Exception(
                    f'Expected error message "{expected_error_message}", but '
                    f'got "{response_json["detail"]}"'
                )
            return response_json

        raise Exception(f'{response_json["detail"]}')


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
async def session(
    init_models, test_contracts
) -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        if utils.web3.is_connected_to_testnet():
            chain.revert()

        for name, table in Base.metadata.tables.items():
            await session.execute(delete(table))
        await db.service.update_entry_point(
            session, test_contracts.entry_point.address, True
        )
        await session.commit()

        yield session


@pytest_asyncio.fixture(scope="function")
async def client() -> AppClient:
    from app.main import app

    async with AsyncClient(app=app, base_url="https://localhost") as client:
        yield AppClient(client)


@pytest.fixture(scope="function")
def send_request(test_contracts, test_account):
    return SendRequest(test_contracts, test_account, 1)


@pytest.fixture(scope="function")
def send_request2(test_contracts, test_account):
    return SendRequest(test_contracts, test_account, 2)


@pytest.fixture(scope="function")
def send_request_with_expire_paymaster(
    test_contracts, test_account, send_request
):
    def f(valid_after: int, valid_until: int):
        time_range = eth_abi.encode(
            ["uint48", "uint48"], [valid_after, valid_until]
        )
        send_request.user_op.paymaster_and_data = (
            test_contracts.test_expire_paymaster.address + time_range.hex()
        )
        send_request.user_op.sign(test_account, test_contracts.entry_point)

        return send_request

    return f
