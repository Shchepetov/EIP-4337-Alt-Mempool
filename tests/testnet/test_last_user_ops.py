import time
from unittest.mock import patch

import pytest
import pytest_asyncio

import db.service
from app.config import settings


@pytest_asyncio.fixture(scope="function")
async def trust_contracts(session, test_contracts):
    await db.service.update_bytecode_from_address(
        session, test_contracts.simple_account_factory.address, True
    )
    await db.service.update_bytecode_from_address(
        session, test_contracts.test_paymaster_accept_all.address, True
    )
    await session.commit()

    return test_contracts


@pytest.mark.asyncio
async def test_returns_last_user_ops(
    client, send_request, send_request2, trust_contracts
):
    user_ops = await client.last_user_ops()
    assert len(user_ops) == 0

    user_op_hash = await client.send_user_op(send_request.json())
    user_ops = await client.last_user_ops()
    assert user_ops[0]["hash"] == user_op_hash

    user_op_hash = await client.send_user_op(send_request2.json())
    user_ops = await client.last_user_ops()
    assert user_ops[1]["hash"] == user_op_hash


@pytest.mark.asyncio
async def test_not_returns_expired_user_ops(
    client, send_request, send_request2, trust_contracts
):
    with patch(
        "time.time", return_value=int(time.time()) - settings.user_op_lifetime
    ):
        await client.send_user_op(send_request.json())

    user_op_hash = await client.send_user_op(send_request2.json())
    user_ops = await client.last_user_ops()
    assert len(user_ops) == 1
    assert user_ops[0]["hash"] == user_op_hash


@pytest.mark.asyncio
async def test_not_returns_user_ops_using_prohibited_bytecodes(
    client,
    session,
    test_contracts,
    test_account,
    send_request,
    send_request2,
    trust_contracts,
):
    user_op_hash = await client.send_user_op(send_request.json())

    send_request2.user_op.paymaster_and_data = (
        test_contracts.test_expire_paymaster.address + 128 * "0"
    )
    send_request2.user_op.sign(test_account, test_contracts.entry_point)
    await client.send_user_op(send_request2.json())

    await db.service.update_bytecode_from_address(
        session, test_contracts.test_expire_paymaster.address, False
    )
    await session.commit()

    user_ops = await client.last_user_ops()
    assert len(user_ops) == 1
    assert user_ops[0]["hash"] == user_op_hash


@pytest.mark.asyncio
async def test_not_returns_executed_user_ops(
    client, test_contracts, test_account, send_request, send_request2
):
    await client.send_user_op(send_request.json())
    test_contracts.entry_point.handleOps(
        [send_request.user_op.values()], test_account.address
    )

    user_ops = await client.last_user_ops()
    assert len(user_ops) == 0
