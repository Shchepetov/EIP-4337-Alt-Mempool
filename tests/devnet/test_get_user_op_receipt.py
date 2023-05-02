import pytest

import db.service


@pytest.mark.asyncio
async def test_returns_user_op_receipt(
    client, test_contracts, test_account, send_request
):
    user_op_hash = await client.send_user_op(send_request.json())
    tx = test_contracts.entry_point.handleOps(
        [send_request.user_op.values()], test_account.address
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
async def test_rejects_request_if_user_op_deleted_with_prohibited_bytecode(
    client, session, test_contracts, test_account, send_request
):
    user_op_hash = await client.send_user_op(send_request.json())
    test_contracts.entry_point.handleOps(
        [send_request.user_op.values()], test_account.address
    )
    await db.service.update_bytecode_from_address(
        session, test_contracts.test_paymaster_accept_all.address, False
    )
    await session.commit()

    await client.get_user_op_receipt(
        user_op_hash, expected_error_message="The UserOp does not exist"
    )


@pytest.mark.asyncio
async def test_returns_null_if_user_op_not_executed(client, send_request):
    user_op_hash = await client.send_user_op(send_request.json())
    assert (await client.get_user_op_receipt(user_op_hash)) == None
