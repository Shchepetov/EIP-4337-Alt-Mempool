import copy
import datetime
import time
from unittest.mock import patch

import pytest
from brownie import (
    TestPaymasterAcceptAll,
)

import app.constants as constants
import db.service
import utils.web3
from app.config import settings


@pytest.mark.asyncio
async def test_accepts_user_op(client, send_request):
    await client.send_user_op(send_request.json())


@pytest.mark.asyncio
async def test_rejects_user_op_from_not_supported_entry_point(
    client, send_request, test_contracts
):
    send_request.entry_point = test_contracts.test_counter.address
    await client.send_user_op(
        send_request.json(),
        expected_error_message="The EntryPoint is not supported",
    )


@pytest.mark.asyncio
async def test_rejects_user_op_with_integers_in_fields(client, send_request):
    request_json = send_request.json()
    for field in request_json["user_op"].keys():
        incorrect_json = copy.deepcopy(request_json)
        incorrect_json["user_op"][field] = 0
        await client.send_user_op(
            incorrect_json, expected_error_message="Not a hex value"
        )

    incorrect_json = copy.deepcopy(request_json)
    incorrect_json["entry_point"] = 0
    await client.send_user_op(
        incorrect_json, expected_error_message="Not a hex value"
    )


@pytest.mark.asyncio
async def test_rejects_user_op_with_non_hexadecimal_values_in_fields(
    client, send_request
):
    request_json = send_request.json()
    for field in request_json["user_op"].keys():
        incorrect_json = copy.deepcopy(request_json)
        incorrect_json["user_op"][field] = request_json["user_op"][
            field
        ].replace("0x", "")
        await client.send_user_op(
            incorrect_json, expected_error_message="Not a hex value"
        )

        incorrect_json["user_op"][field] = (
            request_json["user_op"][field][:-1] + "g"
        )
        await client.send_user_op(
            incorrect_json, expected_error_message="Not a hex value"
        )

    incorrect_json = copy.deepcopy(request_json)
    incorrect_json["entry_point"] = request_json["entry_point"].replace(
        "0x", ""
    )
    await client.send_user_op(
        incorrect_json, expected_error_message="Not a hex value"
    )

    incorrect_json = copy.deepcopy(request_json)
    incorrect_json["entry_point"] = request_json["entry_point"][:-1] + "g"
    await client.send_user_op(
        incorrect_json, expected_error_message="Not a hex value"
    )


@pytest.mark.asyncio
async def test_rejects_user_op_with_values_less_than_20_bytes_in_address_fields(
    client, send_request
):
    send_request.user_op.sender = "0x4CDbDf63ae2215eDD6B673F9DABFf789A13D427"
    await client.send_user_op(
        send_request.json(),
        expected_error_message="Must be an Ethereum address",
    )


@pytest.mark.asyncio
async def test_rejects_user_op_with_values_larger_uint256_in_integer_fields(
    client, send_request
):
    request_json = send_request.json()
    for field in (
        "nonce",
        "call_gas_limit",
        "verification_gas_limit",
        "pre_verification_gas",
        "max_fee_per_gas",
        "max_priority_fee_per_gas",
    ):
        incorrect_json = copy.deepcopy(request_json)
        incorrect_json["user_op"][field] = hex(2**256)
        await client.send_user_op(
            incorrect_json,
            expected_error_message="Must be in range [0, 2**256)",
        )


@pytest.mark.asyncio
async def test_rejects_user_op_with_odd_hexadecimal_chars_in_byte_fields(
    client, send_request
):
    request_json = send_request.json()
    for field in (
        "init_code",
        "call_data",
        "paymaster_and_data",
        "signature",
    ):
        incorrect_json = copy.deepcopy(request_json)
        incorrect_json["user_op"][field] = request_json["user_op"][field] + "1"
        await client.send_user_op(
            incorrect_json, expected_error_message="Incorrect bytes string"
        )


@pytest.mark.asyncio
async def test_rejects_same_user_op(client, send_request):
    await client.send_user_op(send_request.json())
    await client.send_user_op(
        send_request.json(),
        expected_error_message="UserOp is already in the pool",
    )


@pytest.mark.asyncio
async def test_rejects_same_user_op_with_different_signature(
    client, send_request
):
    await client.send_user_op(send_request.json())
    send_request.user_op.signature += "1234"
    await client.send_user_op(
        send_request.json(),
        expected_error_message="UserOp is already in the pool",
    )


@pytest.mark.asyncio
async def test_replaces_user_op_with_same_sender(client, send_request):
    user_op_1_hash = await client.send_user_op(send_request.json())

    send_request.user_op.nonce += 1
    user_op_2_hash = await client.send_user_op(send_request.json())

    await client.get_user_op(
        user_op_1_hash, expected_error_message="The UserOp does not exist"
    )

    user_op = await client.get_user_op(user_op_2_hash)
    assert user_op["hash"] == user_op_2_hash


@pytest.mark.asyncio
async def test_rejects_user_op_without_contract_address_in_sender_and_init_code(
    client, test_account, send_request
):
    eoa_address = test_account.address
    send_request.user_op.sender = eoa_address
    send_request.user_op.init_code = eoa_address
    await client.send_user_op(
        send_request.json(),
        expected_error_message="'sender' and the first 20 bytes of "
        "'init_code' do not represent a smart contract address",
    )


@pytest.mark.asyncio
async def test_rejects_user_op_with_verification_gas_limit_greater_than_limit(
    client, send_request
):
    incorrect_verification_gas_limit = settings.max_verification_gas_limit + 1
    send_request.user_op.verification_gas_limit = (
        incorrect_verification_gas_limit
    )
    await client.send_user_op(
        send_request.json(),
        expected_error_message=f"'verification_gas_limit' value is larger than "
        f"the client limit of {settings.max_verification_gas_limit}",
    )

    send_request.user_op.verification_gas_limit = (
        incorrect_verification_gas_limit - 1
    )
    await client.send_user_op(send_request.json())


@pytest.mark.asyncio
async def test_rejects_user_op_with_max_fee_per_gas_less_than_limit(
    client, send_request
):
    incorrect_max_fee_per_gas = settings.min_max_fee_per_gas - 1
    send_request.user_op.max_fee_per_gas = incorrect_max_fee_per_gas
    await client.send_user_op(
        send_request.json(),
        expected_error_message=f"'max_fee_per_gas' value is less than "
        f"the client limit of {settings.min_max_fee_per_gas}",
    )


@pytest.mark.asyncio
async def test_rejects_user_op_with_max_priority_fee_per_gas_less_than_limit(
    client, send_request
):
    incorrect_max_priority_fee_per_gas = (
        settings.min_max_priority_fee_per_gas - 1
    )
    send_request.user_op.max_priority_fee_per_gas = (
        incorrect_max_priority_fee_per_gas
    )
    await client.send_user_op(
        send_request.json(),
        expected_error_message=f"'max_priority_fee_per_gas' value is less than "
        f"the client limit of {settings.min_max_priority_fee_per_gas}",
    )

    send_request.user_op.max_priority_fee_per_gas = (
        incorrect_max_priority_fee_per_gas + 1
    )
    await client.send_user_op(send_request.json())


@pytest.mark.asyncio
async def test_rejects_user_op_that_cant_be_included_with_current_basefee(
    client, send_request
):
    base_fee = utils.web3.get_base_fee()
    incorrect_max_priority_fee_per_gas = (
        send_request.user_op.max_fee_per_gas - base_fee + 1
    )
    send_request.user_op.max_priority_fee_per_gas = (
        incorrect_max_priority_fee_per_gas
    )
    await client.send_user_op(
        send_request.json(),
        expected_error_message="'max_fee_per_gas' and "
        "'max_priority_fee_per_gas' are not sufficiently high to be included "
        "with the current block",
    )

    send_request.user_op.max_priority_fee_per_gas = (
        incorrect_max_priority_fee_per_gas - 1
    )
    await client.send_user_op(send_request.json())


@pytest.mark.asyncio
async def test_rejects_user_op_with_pre_verification_gas_less_than_calldata_gas(
    client, send_request
):
    while (
        send_request.user_op.pre_verification_gas
        != send_request.user_op.get_calldata_gas() - 1
    ):
        send_request.user_op.pre_verification_gas = (
            send_request.user_op.get_calldata_gas() - 1
        )
    await client.send_user_op(
        send_request.json(),
        expected_error_message="'pre_verification_gas' value is insufficient "
        "to cover the gas cost of serializing UserOp to calldata",
    )


@pytest.mark.asyncio
async def test_rejects_user_op_without_contract_address_in_paymaster(
    client, test_contracts, test_account, send_request
):
    eoa_address = test_account.address
    send_request.user_op.paymaster_and_data = eoa_address
    await client.send_user_op(
        send_request.json(),
        expected_error_message="The first 20 bytes of 'paymaster_and_data' do "
        "not represent a smart contract address",
    )

    send_request.user_op.paymaster_and_data = (
        test_contracts.test_paymaster_accept_all.address
    )
    await client.send_user_op(send_request.json())


@pytest.mark.asyncio
async def test_rejects_user_op_with_paymaster_that_have_not_enough_deposit(
    client, test_contracts, test_account, send_request
):
    new_paymaster = test_account.deploy(
        TestPaymasterAcceptAll, test_contracts.entry_point.address
    )
    send_request.user_op.paymaster_and_data = new_paymaster.address
    send_request.user_op.sign(test_account.address, test_contracts.entry_point)

    await client.send_user_op(
        send_request.json(),
        expected_error_message="The paymaster does not have sufficient funds "
        "to pay for the UserOp",
    )

    test_contracts.entry_point.depositTo(
        new_paymaster.address,
        {
            "value": send_request.user_op.get_required_prefund(
                with_paymaster=True
            )
        },
    )

    await client.send_user_op(send_request.json())


@pytest.mark.asyncio
async def test_rejects_user_op_with_call_gas_limit_less_than_call_opcode_cost(
    client, send_request
):
    send_request.user_op.call_gas_limit = constants.CALL_GAS - 1
    await client.send_user_op(
        send_request.json(),
        expected_error_message=f"'call_gas_limit' is less than "
        f"{constants.CALL_GAS}, which is the minimum gas cost of a 'CALL' with "
        f"non-zero value",
    )

    send_request.user_op.call_gas_limit = constants.CALL_GAS
    await client.send_user_op(send_request.json())


@pytest.mark.asyncio
async def test_rejects_user_op_failing_simulation(client, send_request):
    send_request.user_op.signature = send_request.user_op.signature[:-2]
    await client.send_user_op(
        send_request.json(),
        expected_error_message="The simulation of the UserOp has failed",
    )


@pytest.mark.asyncio
async def test_rejects_expired_user_op(
    client, send_request_with_expire_paymaster
):
    now = int(time.time())
    send_request = send_request_with_expire_paymaster(now, now)
    await client.send_user_op(
        send_request.json(),
        expected_error_message="Unable to process the UserOp as it is expired",
    )


@pytest.mark.asyncio
async def test_rejects_user_op_valid_after_expiry_period(
    client, send_request_with_expire_paymaster
):
    now = int(time.time())
    send_request = send_request_with_expire_paymaster(
        now + settings.user_op_lifetime + 10, 0
    )

    await client.send_user_op(
        send_request.json(),
        expected_error_message="Unable to process the UserOp as it expires in "
        "the pool before its validity period starts.",
    )


@pytest.mark.asyncio
async def test_saves_validity_period_in_user_op(
    client, send_request_with_expire_paymaster
):
    now = int(time.time())
    valid_after = now
    valid_until = now + 300
    send_request = send_request_with_expire_paymaster(valid_after, valid_until)

    user_op_hash = await client.send_user_op(send_request.json())
    user_op = await client.get_user_op(user_op_hash)

    assert (
        int(datetime.datetime.fromisoformat(user_op["valid_after"]).timestamp())
        == valid_after
    )
    assert (
        int(datetime.datetime.fromisoformat(user_op["valid_until"]).timestamp())
        == valid_until
    )


@pytest.mark.asyncio
async def test_saves_another_valid_until_in_user_op_if_simulation_returns_uint64_max(
    client, send_request_with_expire_paymaster
):
    now = int(time.time())
    send_request = send_request_with_expire_paymaster(now, 0)

    user_op_hash = await client.send_user_op(send_request.json())
    user_op = await client.get_user_op(user_op_hash)

    assert (
        int(datetime.datetime.fromisoformat(user_op["valid_until"]).timestamp())
        == constants.MAX_TIMESTAMP
    )


@pytest.mark.asyncio
async def test_saves_expiry_time_equal_valid_until_in_user_op(
    client, send_request_with_expire_paymaster
):
    now = int(time.time())
    valid_until = int(now + settings.user_op_lifetime / 2)
    send_request = send_request_with_expire_paymaster(now, valid_until)

    user_op_hash = await client.send_user_op(send_request.json())
    user_op = await client.get_user_op(user_op_hash)

    assert (
        int(datetime.datetime.fromisoformat(user_op["expires_at"]).timestamp())
        == valid_until
    )


@pytest.mark.asyncio
async def test_saves_expiry_time_equal_lifetime_period_end_in_user_op(
    client, send_request_with_expire_paymaster
):
    now = int(time.time())
    send_request = send_request_with_expire_paymaster(now, 0)

    user_op_hash = await client.send_user_op(send_request.json())
    user_op = await client.get_user_op(user_op_hash)

    assert int(
        datetime.datetime.fromisoformat(user_op["expires_at"]).timestamp()
    ) == pytest.approx(now + settings.user_op_lifetime, abs=5)


@pytest.mark.asyncio
async def test_rejects_user_op_with_prohibited_factory(
    client, session, test_contracts, send_request
):
    await db.service.update_bytecode_from_address(
        session, test_contracts.simple_account_factory.address, False
    )
    await session.commit()
    await client.send_user_op(
        send_request.json(),
        expected_error_message="The UserOp contains calls to smart contracts, "
        "the bytecode of which is listed in the blacklist",
    )


@pytest.mark.asyncio
async def test_rejects_user_op_with_prohibited_paymaster(
    client, session, test_contracts, send_request
):
    await db.service.update_bytecode_from_address(
        session, test_contracts.test_paymaster_accept_all.address, False
    )
    await session.commit()
    await client.send_user_op(
        send_request.json(),
        expected_error_message="The UserOp contains calls to smart contracts, "
        "the bytecode of which is listed in the blacklist",
    )


@pytest.mark.asyncio
async def test_rejects_user_op_with_prohibited_aggregator(
    client, session, test_contracts, test_account, send_request
):
    salt = 1
    send_request.user_op.sender = (
        test_contracts.aggregated_account_factory.getAddress(
            test_account.address, salt
        )
    )
    send_request.user_op.init_code = (
        test_contracts.aggregated_account_factory.address
        + test_contracts.aggregated_account_factory.createAccount.encode_input(
            test_account.address, salt
        )[2:]
    )
    send_request.user_op.sign(test_account.address, test_contracts.entry_point)

    await db.service.update_bytecode_from_address(
        session, test_contracts.aggregator.address, False
    )
    await session.commit()
    await client.send_user_op(
        send_request.json(),
        expected_error_message="The UserOp contains calls to smart contracts, "
        "the bytecode of which is listed in the blacklist",
    )


@pytest.mark.asyncio
async def test_marks_user_op_not_trusted_if_any_bytecode_is_not_trusted(
    client, session, test_contracts, send_request
):
    await db.service.update_bytecode_from_address(
        session, test_contracts.simple_account_factory.address, True
    )
    await session.commit()

    user_op_hash = await client.send_user_op(send_request.json())
    user_op = await client.get_user_op(user_op_hash)
    assert not int(user_op["is_trusted"], 16)


@pytest.mark.asyncio
async def test_marks_user_op_trusted_if_all_bytecodes_are_trusted(
    client, session, test_contracts, send_request
):
    await db.service.update_bytecode_from_address(
        session, test_contracts.simple_account_factory.address, True
    )
    await db.service.update_bytecode_from_address(
        session, test_contracts.test_paymaster_accept_all.address, True
    )
    await session.commit()

    user_op_hash = await client.send_user_op(send_request.json())
    user_op = await client.get_user_op(user_op_hash)
    assert user_op["is_trusted"]


@pytest.mark.asyncio
async def test_rejects_user_op_using_not_trusted_bytecode_already_in_pool(
    client, send_request, send_request2
):
    await client.send_user_op(send_request.json())
    await client.send_user_op(
        send_request2.json(),
        expected_error_message="The UserOp is not trusted and the pool already"
        " has a UserOp that uses the same helper contracts",
    )


@pytest.mark.asyncio
async def test_accepts_user_op_using_trusted_bytecode_already_in_pool(
    client, session, test_contracts, send_request, send_request2
):
    await client.send_user_op(send_request.json())

    await db.service.update_bytecode_from_address(
        session, test_contracts.simple_account_factory.address, True
    )
    await db.service.update_bytecode_from_address(
        session, test_contracts.test_paymaster_accept_all.address, True
    )
    await session.commit()

    await client.send_user_op(send_request2.json())


@pytest.mark.asyncio
async def test_accepts_user_op_using_not_trusted_bytecode_expired_in_pool(
    client, send_request, send_request2
):
    with patch(
        "time.time", return_value=int(time.time()) - settings.user_op_lifetime
    ):
        await client.send_user_op(send_request.json())

    await client.send_user_op(send_request2.json())
