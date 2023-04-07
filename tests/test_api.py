import copy

import pytest
from brownie import accounts

import utils.validation
from app.config import settings


@pytest.mark.eth_sendUserOperation
@pytest.mark.asyncio
async def test_accepts_user_op(client, test_request: dict):
    await client.send_user_op(test_request, status_code=200)


@pytest.mark.eth_sendUserOperation
@pytest.mark.asyncio
async def test_rejects_user_op_with_integers_in_fields(
    client, test_request: dict
):
    for field in test_request["user_op"].keys():
        incorrect_request = copy.deepcopy(test_request)
        incorrect_request["user_op"][field] = int(
            test_request["user_op"][field], 16
        )
        await client.send_user_op(
            incorrect_request, expected_error_message="Not a hex value"
        )

    incorrect_request = copy.deepcopy(test_request)
    incorrect_request["entry_point"] = int(test_request["entry_point"], 16)
    await client.send_user_op(
        incorrect_request, expected_error_message="Not a hex value"
    )


@pytest.mark.eth_sendUserOperation
@pytest.mark.asyncio
async def test_rejects_user_op_with_non_hexadecimal_values_in_fields(
    client, test_request: dict
):
    for field in test_request["user_op"].keys():
        incorrect_request = copy.deepcopy(test_request)
        incorrect_request["user_op"][field] = test_request["user_op"][
            field
        ].replace("0x", "")
        await client.send_user_op(
            incorrect_request, expected_error_message="Not a hex value"
        )

        incorrect_request["user_op"][field] = (
            test_request["user_op"][field][:-1] + "g"
        )
        await client.send_user_op(
            incorrect_request, expected_error_message="Not a hex value"
        )

    incorrect_request = copy.deepcopy(test_request)
    incorrect_request["entry_point"] = test_request["entry_point"].replace(
        "0x", ""
    )
    await client.send_user_op(
        incorrect_request, expected_error_message="Not a hex value"
    )

    incorrect_request = copy.deepcopy(test_request)
    incorrect_request["entry_point"] = test_request["entry_point"][:-1] + "g"
    await client.send_user_op(
        incorrect_request, expected_error_message="Not a hex value"
    )


@pytest.mark.eth_sendUserOperation
@pytest.mark.asyncio
async def test_rejects_user_op_with_values_less_than_20_bytes_in_address_fields(
    client, test_request: dict
):
    test_request["user_op"][
        "sender"
    ] = "0x4CDbDf63ae2215eDD6B673F9DABFf789A13D427"
    await client.send_user_op(
        test_request, expected_error_message="Must be an Ethereum address"
    )


@pytest.mark.eth_sendUserOperation
@pytest.mark.asyncio
async def test_accepts_user_op_with_0x0_sender(client, test_request: dict):
    test_request["user_op"]["sender"] = "0x0"
    await client.send_user_op(test_request, status_code=200)


@pytest.mark.eth_sendUserOperation
@pytest.mark.asyncio
async def test_rejects_user_op_with_values_larger_uint256_in_integer_fields(
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
        await client.send_user_op(
            incorrect_request,
            expected_error_message="Must be in range [0, 2**256)",
        )


@pytest.mark.eth_sendUserOperation
@pytest.mark.asyncio
async def test_rejects_user_op_with_odd_hexadecimal_chars_in_byte_fields(
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
        await client.send_user_op(
            incorrect_request, expected_error_message="Incorrect bytes string"
        )


@pytest.mark.eth_sendUserOperation
@pytest.mark.asyncio
async def test_saves_correct_user_op(client, test_request: dict):
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


@pytest.mark.eth_sendUserOperation
@pytest.mark.asyncio
async def test_rejects_same_user_op(client, test_request: dict):
    await client.send_user_op(test_request)
    await client.send_user_op(
        test_request, expected_error_message="UserOp is already in the pool"
    )


@pytest.mark.eth_sendUserOperation
@pytest.mark.asyncio
async def test_rejects_same_user_op_with_different_signature(
    client, test_request: dict
):
    await client.send_user_op(test_request)
    test_request["user_op"]["signature"] = (
        test_request["user_op"]["signature"] + "1234"
    )
    await client.send_user_op(
        test_request, expected_error_message="UserOp is already in the pool"
    )


@pytest.mark.eth_sendUserOperation
@pytest.mark.asyncio
async def test_replaces_user_op_with_same_sender(client, test_request: dict):
    user_op_1_hash = await client.send_user_op(test_request)

    test_request["user_op"]["nonce"] = test_request["user_op"]["nonce"] + "1234"
    user_op_2_hash = await client.send_user_op(test_request, status_code=200)

    assert await client.get_user_op(user_op_1_hash) is None

    user_op = await client.get_user_op(user_op_2_hash, status_code=200)
    assert user_op["hash"] == user_op_2_hash


@pytest.mark.eth_sendUserOperation
@pytest.mark.asyncio
async def test_not_replaces_user_op_with_sender_0x0(client, test_request: dict):
    test_request["user_op"]["sender"] = "0x0"
    user_op_1_hash = await client.send_user_op(test_request)

    test_request["user_op"]["nonce"] = test_request["user_op"]["nonce"] + "1234"
    user_op_2_hash = await client.send_user_op(test_request)

    user_op_1 = await client.get_user_op(user_op_1_hash)
    assert user_op_1["hash"] == user_op_1_hash

    user_op_2 = await client.get_user_op(user_op_2_hash)
    assert user_op_2["hash"] == user_op_2_hash


@pytest.mark.eth_sendUserOperation
@pytest.mark.asyncio
async def test_rejects_user_op_without_contract_address_in_sender_and_init_code(
    client, test_request: dict
):
    eoa_address = accounts[0].address
    test_request["user_op"]["sender"] = eoa_address
    test_request["user_op"]["init_code"] = eoa_address
    await client.send_user_op(
        test_request,
        expected_error_message="'sender' and the first 20 bytes of "
        "'init_code' do not represent a smart contract address",
    )


@pytest.mark.eth_sendUserOperation
@pytest.mark.asyncio
async def test_rejects_user_op_with_verification_gas_limit_greater_than_limit(
    client, test_request: dict
):
    incorrect_verification_gas_limit = hex(settings.max_verification_gas + 1)
    test_request["user_op"][
        "verification_gas_limit"
    ] = incorrect_verification_gas_limit
    await client.send_user_op(
        test_request,
        expected_error_message=f"'verification_gas_limit' value is larger than "
        "the client limit of {settings.max_verification_gas}",
    )


@pytest.mark.eth_sendUserOperation
@pytest.mark.asyncio
async def test_rejects_user_op_with_pre_verification_gas_less_than_calldata_gas(
    client, test_request: dict
):
    incorrect_pre_verification_gas = (
        utils.validation.calldata_gas(test_request["user_op"]) - 1
    )
    test_request["user_op"]["pre_verification_gas"] = hex(
        incorrect_pre_verification_gas
    )
    await client.send_user_op(
        test_request,
        expected_error_message="'pre_verification_gas' value is insufficient "
        "to cover the gas cost of serializing UserOp to calldata",
    )


@pytest.mark.eth_sendUserOperation
@pytest.mark.asyncio
async def test_rejects_user_op_without_contract_address_in_paymaster(
    client, test_request: dict
):
    test_request["user_op"]["paymaster_and_data"] = hex(123)
    await client.send_user_op(
        test_request,
        expected_error_message="The first 20 bytes of 'paymaster_and_data' do "
        "not represent a smart contract address",
    )
