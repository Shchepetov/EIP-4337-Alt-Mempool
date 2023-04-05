import copy
import logging

import pytest

LOGGER = logging.getLogger(__name__)


@pytest.mark.eth_sendUserOperation
@pytest.mark.asyncio
async def test_create_user_op(client, test_request: dict):
    await client.send_user_op(test_request, status_code=200)


@pytest.mark.eth_sendUserOperation
@pytest.mark.asyncio
async def test_integer_fields_rejected(client, test_request: dict):
    for field in test_request["user_op"].keys():
        incorrect_request = copy.deepcopy(test_request)
        incorrect_request["user_op"][field] = int(
            test_request["user_op"][field], 16
        )
        await client.send_user_op(incorrect_request, status_code=422)

    incorrect_request = copy.deepcopy(test_request)
    incorrect_request["entry_point"] = int(test_request["entry_point"], 16)
    await client.send_user_op(incorrect_request, status_code=422)


@pytest.mark.eth_sendUserOperation
@pytest.mark.asyncio
async def test_non_hexadecimal_fields_rejected(client, test_request: dict):
    for field in test_request["user_op"].keys():
        incorrect_request = copy.deepcopy(test_request)
        incorrect_request["user_op"][field] = test_request["user_op"][
            field
        ].replace("0x", "")
        await client.send_user_op(incorrect_request, status_code=422)

        incorrect_request["user_op"][field] = (
            test_request["user_op"][field][:-1] + "g"
        )
        await client.send_user_op(incorrect_request, status_code=422)

    incorrect_request = copy.deepcopy(test_request)
    incorrect_request["entry_point"] = test_request["entry_point"].replace(
        "0x", ""
    )
    await client.send_user_op(incorrect_request, status_code=422)

    incorrect_request = copy.deepcopy(test_request)
    incorrect_request["entry_point"] = test_request["entry_point"][:-1] + "g"
    await client.send_user_op(incorrect_request, status_code=422)


@pytest.mark.eth_sendUserOperation
@pytest.mark.asyncio
async def test_address_0x0_accepted(client, test_request: dict):
    test_request["user_op"]["sender"] = "0x0"
    await client.send_user_op(test_request, status_code=200)


@pytest.mark.eth_sendUserOperation
@pytest.mark.asyncio
async def test_address_less_than_20_bytes_rejected(client, test_request: dict):
    test_request["user_op"][
        "sender"
    ] = "0x4CDbDf63ae2215eDD6B673F9DABFf789A13D427"
    await client.send_user_op(test_request, status_code=422)


@pytest.mark.eth_sendUserOperation
@pytest.mark.asyncio
async def test_address_with_incorrect_checksum_rejected(
    client, test_request: dict
):
    test_request["user_op"][
        "sender"
    ] = "4cDbDf63ae2215eDD6B673F9DABFf789A13D4270"
    await client.send_user_op(test_request, status_code=422)


@pytest.mark.eth_sendUserOperation
@pytest.mark.asyncio
async def test_values_larger_uint256_in_integer_fields_rejected(
    client, test_request: dict
):
    for field in (
        "nonce",
        "call_gas_limit",
        "verification_gas_limit",
        "pre_verification_gas",
        "max_fee_per_gas",
        "max_priority_fee_per_gas",
    ):
        incorrect_request = copy.deepcopy(test_request)
        incorrect_request["user_op"][field] = hex(2**256)
        await client.send_user_op(incorrect_request, status_code=422)


@pytest.mark.eth_sendUserOperation
@pytest.mark.asyncio
async def test_odd_hexadecimal_chars_in_byte_fields_rejected(
    client, test_request: dict
):
    for field in (
        "init_code",
        "call_data",
        "paymaster_and_data",
        "signature",
    ):
        incorrect_request = copy.deepcopy(test_request)
        incorrect_request["user_op"][field] = (
            test_request["user_op"][field] + "0"
        )
        await client.send_user_op(incorrect_request, status_code=422)


@pytest.mark.eth_sendUserOperation
@pytest.mark.asyncio
async def test_sent_user_op_saved(client, test_request: dict):
    user_op_hash = await client.send_user_op(test_request)
    user_op = await client.get_user_op(user_op_hash, status_code=200)

    for field in test_request["user_op"].keys():
        if field in (
            "nonce",
            "call_gas_limit",
            "verification_gas_limit",
            "pre_verification_gas",
            "max_fee_per_gas",
            "max_priority_fee_per_gas",
        ):
            assert user_op[field] == int(test_request["user_op"][field], 16)
        else:
            assert user_op[field] == test_request["user_op"][field]

    assert user_op["entry_point"] == test_request["entry_point"]
