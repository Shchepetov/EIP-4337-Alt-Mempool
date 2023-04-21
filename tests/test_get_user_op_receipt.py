import pytest
from brownie import accounts

import db.service


@pytest.mark.asyncio
async def test_returns_user_op_receipt(client, contracts, send_request):
    user_op_hash = await client.send_user_op(send_request.json())
    tx = contracts.entry_point.handleOps(
        [send_request.user_op.values()], accounts[0].address
    )

    receipt = await client.get_user_op_receipt(user_op_hash)
    assert receipt["tx_hash"] == tx.txid
    assert receipt["accepted"] == True


@pytest.mark.asyncio
async def test_rejects_request_with_non_hexadecimal_hash(client, send_request):
    user_op_hash = await client.send_user_op(send_request.json())

    incorrect_hash = user_op_hash.replace("0x", "")
    await client.get_user_op_receipt(
        incorrect_hash, expected_error_message="Not a hex value"
    )


@pytest.mark.asyncio
async def test_rejects_request_with_integer_hash(client, send_request):
    user_op_hash = await client.send_user_op(send_request.json())

    await client.get_user_op_receipt(
        int(user_op_hash, 16), expected_error_message="Not a hex value"
    )


@pytest.mark.asyncio
async def test_rejects_request_with_hash_larger_than_32_bytes(
    client, send_request
):
    user_op_hash = await client.send_user_op(send_request.json())

    await client.get_user_op_receipt(
        user_op_hash + "1234",
        expected_error_message="Not a 32-bytes hex value.",
    )


@pytest.mark.asyncio
async def test_rejects_request_if_user_op_not_exists(client, send_request):
    await client.get_user_op_receipt(
        "0x" + 64 * "0", expected_error_message="The UserOp does not exist"
    )


@pytest.mark.asyncio
async def test_rejects_request_if_user_op_deleted_with_forbidden_bytecode(
    client, session, contracts, send_request
):
    user_op_hash = await client.send_user_op(send_request.json())
    contracts.entry_point.handleOps(
        [send_request.user_op.values()], accounts[0].address
    )
    await db.service.update_bytecode_from_address(
        session, contracts.paymaster.address, False
    )
    await session.commit()

    await client.get_user_op_receipt(
        user_op_hash, expected_error_message="The UserOp does not exist"
    )


@pytest.mark.asyncio
async def test_returns_null_if_user_op_not_executed(client, send_request):
    user_op_hash = await client.send_user_op(send_request.json())
    assert (await client.get_user_op_receipt(user_op_hash)) == None
