import asyncio
from collections.abc import AsyncGenerator

import brownie
import pytest
import pytest_asyncio
from brownie import (
    accounts,
    chain,
    web3,
    TestAggregatedAccountFactory,
    TestExpirePaymaster,
    TestPaymasterAcceptAll,
    EntryPoint,
    SelfDestructor,
    SimpleAccountFactory,
    TestCounter,
    TestToken,
)
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

import app.config as config
import db.utils
from app.config import Settings
from db.base import engine, async_session, Base
from utils.user_op import UserOp, DEFAULTS_FOR_USER_OP


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

    async def get_user_op_receipt(self, hash_: str, **kwargs) -> dict:
        return await self._make_request(
            "eth_getUserOperationReceipt", json={"hash": hash_}, **kwargs
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
                    f'Expected error message "{expected_error_message}", but response code is 200'
                )
            return response_json

        if expected_error_message is not None:
            if expected_error_message not in response_json["detail"]:
                raise Exception(
                    f'Expected error message "{expected_error_message}", but got "{response_json["detail"]}"'
                )
            return response_json

        raise Exception(f'{response_json["detail"]}')


class TestContracts:
    def __init__(self):
        self.counter = accounts[0].deploy(TestCounter)
        self.entry_point = accounts[0].deploy(EntryPoint)
        self.self_destructor = accounts[0].deploy(SelfDestructor)
        self.token = accounts[0].deploy(TestToken)
        self.aggregator = self.entry_point

        self.aggregated_account_factory = accounts[0].deploy(
            TestAggregatedAccountFactory,
            self.entry_point.address,
            self.aggregator.address,
        )
        self.simple_account_factory = accounts[0].deploy(
            SimpleAccountFactory, self.entry_point.address
        )

        self.expire_paymaster = accounts[0].deploy(
            TestExpirePaymaster, self.entry_point.address
        )
        self.paymaster = accounts[0].deploy(
            TestPaymasterAcceptAll, self.entry_point.address
        )

        for address in (
            self.expire_paymaster.address,
            self.paymaster.address,
        ):
            self.entry_point.depositTo(address, {"value": "10 ether"})

        chain.snapshot()


class SendRequest:
    def __init__(self, user_op, entry_point):
        self.user_op = user_op
        self.entry_point = entry_point

    def json(self):
        return {
            "user_op": {
                k: self._to_hex(v) for k, v in self.user_op.dict().items()
            },
            "entry_point": self.entry_point,
        }

    @classmethod
    def _to_hex(cls, v) -> str:
        if isinstance(v, str):
            return v
        if isinstance(v, int):
            return hex(v)
        if isinstance(v, bytes):
            return "0x" + bytes.hex(v)


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
def send_request(contracts):
    return get_send_request(contracts, 1)


@pytest.fixture(scope="function")
def send_request2(contracts):
    return get_send_request(contracts, 2)


def get_send_request(contracts, salt):
    user_op = UserOp(**DEFAULTS_FOR_USER_OP)
    user_op.sender = contracts.simple_account_factory.getAddress(
        accounts[0].address, salt
    )
    user_op.init_code = (
        contracts.simple_account_factory.address
        + contracts.simple_account_factory.createAccount.encode_input(
            accounts[0].address, salt
        )[2:]
    )
    user_op.paymaster_and_data = contracts.paymaster.address

    user_op.sign(accounts[0].address, contracts.entry_point)

    return SendRequest(user_op, contracts.entry_point.address)


@pytest.fixture(scope="function")
def send_request_with_paymaster_using_opcode(contracts, send_request):
    def f(opcode: str, target: brownie.Contract = None, payload=""):
        paymaster = accounts[0].deploy(
            getattr(brownie, f"TestPaymaster{opcode}"),
            contracts.entry_point.address,
        )
        send_request.user_op.paymaster_and_data = (
            (paymaster.address + target.address[2:] + payload)
            if target
            else paymaster.address
        )

        send_request.user_op.sign(accounts[0].address, contracts.entry_point)
        contracts.entry_point.depositTo(paymaster.address, {"value": "1 ether"})

        return send_request

    return f
