import time
from unittest.mock import patch

import pytest
from brownie import accounts

import db.service
from app.config import settings


@pytest.mark.asyncio
async def test_returns_user_op(client, send_request):
    request_json = send_request.json()
    user_op_hash = await client.send_user_op(request_json)
    user_op = await client.get_user_op(user_op_hash)

    for (key, value) in request_json["user_op"].items():
        assert user_op[key].lower() == value.lower()

    assert user_op["entry_point"] == send_request.entry_point


@pytest.mark.asyncio
async def test_returns_expired_user_op(client, send_request):
    with patch(
        "time.time", return_value=int(time.time()) - settings.user_op_lifetime
    ):
        user_op_hash = await client.send_user_op(send_request.json())

    user_op = await client.get_user_op(user_op_hash)
    assert user_op["hash"] == user_op_hash


@pytest.mark.asyncio
async def test_returns_executed_user_ops(
    client, contracts, send_request, send_request2
):
    user_op_hash = await client.send_user_op(send_request.json())
    contracts.entry_point.handleOps(
        [send_request.user_op.values()], accounts[0].address
    )

    user_op = await client.get_user_op(user_op_hash)
    assert int(user_op["accepted"], 16) == True


@pytest.mark.asyncio
async def test_not_returns_not_existing_user_op(
    client, contracts, send_request
):
    send_request.user_op.fill_hash(contracts.entry_point)
    await client.get_user_op(
        send_request.user_op.hash,
        expected_error_message="The UserOp does not " "exist",
    )


@pytest.mark.asyncio
async def test_not_returns_user_op_using_prohibited_bytecodes(
    client, session, contracts, send_request
):
    user_op_hash = await client.send_user_op(send_request.json())
    await db.service.update_bytecode_from_address(
        session, contracts.paymaster.address, False
    )
    await session.commit()

    await client.get_user_op(
        user_op_hash, expected_error_message="The UserOp does not exist"
    )
