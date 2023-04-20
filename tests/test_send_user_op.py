import copy
import datetime
import time
from unittest.mock import patch

import eth_abi
import pytest
from brownie import (
    accounts,
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
async def test_saves_correct_user_op(client, send_request):
    request_json = send_request.json()
    user_op_hash = await client.send_user_op(request_json)
    user_op = await client.get_user_op(user_op_hash)

    for field in request_json["user_op"].keys():
        assert user_op[field] == getattr(send_request.user_op, field)

    assert user_op["entry_point"] == send_request.entry_point


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

    assert await client.get_user_op(user_op_1_hash) is None

    user_op = await client.get_user_op(user_op_2_hash)
    assert user_op["hash"] == user_op_2_hash


@pytest.mark.asyncio
async def test_rejects_user_op_without_contract_address_in_sender_and_init_code(
    client, send_request
):
    eoa_address = accounts[0].address
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
    incorrect_pre_verification_gas = send_request.user_op.get_calldata_gas() - 1
    send_request.user_op.pre_verification_gas = incorrect_pre_verification_gas
    await client.send_user_op(
        send_request.json(),
        expected_error_message="'pre_verification_gas' value is insufficient "
        "to cover the gas cost of serializing UserOp to calldata",
    )


@pytest.mark.asyncio
async def test_rejects_user_op_without_contract_address_in_paymaster(
    client, contracts, send_request
):
    eoa_address = accounts[0].address
    send_request.user_op.paymaster_and_data = eoa_address
    await client.send_user_op(
        send_request.json(),
        expected_error_message="The first 20 bytes of 'paymaster_and_data' do "
        "not represent a smart contract address",
    )

    send_request.user_op.paymaster_and_data = contracts.paymaster.address
    await client.send_user_op(send_request.json())


@pytest.mark.asyncio
async def test_rejects_user_op_with_paymaster_that_have_not_enough_deposit(
    client, contracts, send_request
):
    new_paymaster = accounts[0].deploy(
        TestPaymasterAcceptAll, contracts.entry_point.address
    )
    send_request.user_op.paymaster_and_data = new_paymaster.address
    send_request.user_op.sign(accounts[0].address, contracts.entry_point)

    await client.send_user_op(
        send_request.json(),
        expected_error_message="The paymaster does not have sufficient funds "
        "to pay for the UserOp",
    )

    contracts.entry_point.depositTo(
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
async def test_rejects_expired_user_op(client, contracts, send_request):
    now = int(time.time())
    time_range = eth_abi.encode(["uint48", "uint48"], [now, now])
    send_request.user_op.paymaster_and_data = (
        contracts.expire_paymaster.address + time_range.hex()
    )
    send_request.user_op.sign(accounts[0].address, contracts.entry_point)

    await client.send_user_op(
        send_request.json(),
        expected_error_message="Unable to add the UserOp as it is expired",
    )


@pytest.mark.asyncio
async def test_rejects_user_op_valid_after_expiry_period(
    client, contracts, send_request
):
    now = int(time.time())
    time_range = eth_abi.encode(
        ["uint48", "uint48"], [now + settings.user_op_lifetime + 10, 0]
    )
    send_request.user_op.paymaster_and_data = (
        contracts.expire_paymaster.address + time_range.hex()
    )
    send_request.user_op.sign(accounts[0].address, contracts.entry_point)

    await client.send_user_op(
        send_request.json(),
        expected_error_message="Unable to add the UserOp as it expires in the "
        "pool before its validity period starts.",
    )


@pytest.mark.asyncio
async def test_saves_validity_period_in_user_op(
    client, contracts, send_request
):
    now = int(time.time())
    valid_after = now
    valid_until = now + 300
    time_range = eth_abi.encode(
        ["uint48", "uint48"], [valid_after, valid_until]
    )
    send_request.user_op.paymaster_and_data = (
        contracts.expire_paymaster.address + time_range.hex()
    )
    send_request.user_op.sign(accounts[0].address, contracts.entry_point)

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
    client, contracts, send_request
):
    now = int(time.time())
    time_range = eth_abi.encode(["uint48", "uint48"], [now, 0])
    send_request.user_op.paymaster_and_data = (
        contracts.expire_paymaster.address + time_range.hex()
    )
    send_request.user_op.sign(accounts[0].address, contracts.entry_point)

    user_op_hash = await client.send_user_op(send_request.json())
    user_op = await client.get_user_op(user_op_hash)

    assert (
        int(datetime.datetime.fromisoformat(user_op["valid_until"]).timestamp())
        == constants.MAX_TIMESTAMP
    )


@pytest.mark.asyncio
async def test_saves_expiry_time_equal_valid_until_in_user_op(
    client, contracts, send_request
):
    now = int(time.time())
    valid_until = int(now + settings.user_op_lifetime / 2)
    time_range = eth_abi.encode(["uint48", "uint48"], [now, valid_until])
    send_request.user_op.paymaster_and_data = (
        contracts.expire_paymaster.address + time_range.hex()
    )
    send_request.user_op.sign(accounts[0].address, contracts.entry_point)

    user_op_hash = await client.send_user_op(send_request.json())
    user_op = await client.get_user_op(user_op_hash)

    assert (
        int(datetime.datetime.fromisoformat(user_op["expires_at"]).timestamp())
        == valid_until
    )


@pytest.mark.asyncio
async def test_saves_expiry_time_equal_lifetime_period_end_in_user_op(
    client, contracts, send_request
):
    now = int(time.time())
    time_range = eth_abi.encode(["uint48", "uint48"], [now, 0])
    send_request.user_op.paymaster_and_data = (
        contracts.expire_paymaster.address + time_range.hex()
    )
    send_request.user_op.sign(accounts[0].address, contracts.entry_point)

    user_op_hash = await client.send_user_op(send_request.json())
    user_op = await client.get_user_op(user_op_hash)

    assert int(
        datetime.datetime.fromisoformat(user_op["expires_at"]).timestamp()
    ) == pytest.approx(now + settings.user_op_lifetime, abs=5)


@pytest.mark.asyncio
async def test_rejects_user_op_with_banned_factory(
    client, session, contracts, send_request
):
    factory_bytecode_hash = utils.web3.get_bytecode_hash(
        contracts.simple_account_factory.address
    )
    await db.service.update_bytecode(session, factory_bytecode_hash, False)
    await session.commit()
    await client.send_user_op(
        send_request.json(),
        expected_error_message="The UserOp contains calls to smart contracts, "
        "the bytecode of which is listed in the blacklist",
    )


@pytest.mark.asyncio
async def test_rejects_user_op_with_banned_paymaster(
    client, session, contracts, send_request
):
    paymaster_bytecode_hash = utils.web3.get_bytecode_hash(
        contracts.paymaster.address
    )
    await db.service.update_bytecode(session, paymaster_bytecode_hash, False)
    await session.commit()
    await client.send_user_op(
        send_request.json(),
        expected_error_message="The UserOp contains calls to smart contracts, "
        "the bytecode of which is listed in the blacklist",
    )


@pytest.mark.asyncio
async def test_rejects_user_op_with_banned_aggregator(
    client, session, contracts, send_request
):
    salt = 1
    send_request.user_op.sender = (
        contracts.aggregated_account_factory.getAddress(
            accounts[0].address, salt
        )
    )
    send_request.user_op.init_code = (
        contracts.aggregated_account_factory.address
        + contracts.aggregated_account_factory.createAccount.encode_input(
            accounts[0].address, salt
        )[2:]
    )
    send_request.user_op.sign(accounts[0].address, contracts.entry_point)

    aggregator_bytecode_hash = utils.web3.get_bytecode_hash(
        contracts.aggregator.address
    )
    await db.service.update_bytecode(session, aggregator_bytecode_hash, False)
    await session.commit()
    await client.send_user_op(
        send_request.json(),
        expected_error_message="The UserOp contains calls to smart contracts, "
        "the bytecode of which is listed in the blacklist",
    )


@pytest.mark.asyncio
async def test_marks_user_op_not_trusted_if_any_bytecode_is_not_trusted(
    client, session, contracts, send_request
):
    factory_bytecode_hash = utils.web3.get_bytecode_hash(
        contracts.simple_account_factory.address
    )
    await db.service.update_bytecode(session, factory_bytecode_hash, True)
    await session.commit()

    user_op_hash = await client.send_user_op(send_request.json())
    user_op = await client.get_user_op(user_op_hash)
    assert not user_op["is_trusted"]


@pytest.mark.asyncio
async def test_marks_user_op_trusted_if_all_bytecodes_are_trusted(
    client, session, contracts, send_request
):
    factory_bytecode_hash = utils.web3.get_bytecode_hash(
        contracts.simple_account_factory.address
    )
    paymaster_bytecode_hash = utils.web3.get_bytecode_hash(
        contracts.paymaster.address
    )
    await db.service.update_bytecode(session, factory_bytecode_hash, True)
    await db.service.update_bytecode(session, paymaster_bytecode_hash, True)
    await session.commit()

    user_op_hash = await client.send_user_op(send_request.json())
    user_op = await client.get_user_op(user_op_hash)
    assert user_op["is_trusted"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "opcode",
    (
        # TODO Test 'BASEFEE' and 'PREVRANDAO' opcodes
        "GASPRICE",
        "GASLIMIT",
        "DIFFICULTY",
        "TIMESTAMP",
        "BLOCKHASH",
        "NUMBER",
        "SELFBALANCE",
        "BALANCE",
        "ORIGIN",
        "CREATE",
        "COINBASE",
    ),
)
async def test_rejects_user_op_using_forbidden_opcodes(
    client, send_request_with_paymaster_using_opcode, opcode
):
    await client.send_user_op(
        send_request_with_paymaster_using_opcode(opcode).json(),
        expected_error_message=f"The UserOp is using the forbidden opcode "
        f"'{opcode}' during validation",
    )


@pytest.mark.asyncio
async def test_rejects_user_op_using_SELFDESTRUCT(
    client, contracts, send_request_with_paymaster_using_opcode
):
    await client.send_user_op(
        send_request_with_paymaster_using_opcode(
            "CALL", contracts.self_destructor
        ).json(),
        expected_error_message=f"The UserOp is using the forbidden opcode "
        f"'SELFDESTRUCT' during validation",
    )


@pytest.mark.asyncio
async def test_rejects_user_op_using_CREATE2_after_initialization(
    client, contracts, send_request_with_paymaster_using_opcode
):
    await client.send_user_op(
        send_request_with_paymaster_using_opcode(
            "CREATE2", contracts.counter
        ).json(),
        expected_error_message="The UserOp is using the 'CREATE2' opcode in an "
        "unacceptable context.",
    )


@pytest.mark.asyncio
async def test_rejects_user_op_using_GAS_not_before_external_call(
    client, send_request_with_paymaster_using_opcode
):
    await client.send_user_op(
        send_request_with_paymaster_using_opcode("GAS").json(),
        expected_error_message="The UserOp is using the 'GAS' opcode during "
        "validation, but not before the external call",
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "opcode",
    (
        "CALL",
        "CALLCODE",
        "DELEGATECALL",
        "STATICCALL",
    ),
)
async def test_allow_user_op_using_GAS_before_some_opcodes(
    client, contracts, send_request_with_paymaster_using_opcode, opcode
):
    await client.send_user_op(
        send_request_with_paymaster_using_opcode(
            f"{opcode}", contracts.counter
        ).json()
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "opcode",
    (
        "CALL",
        "CALLCODE",
        "DELEGATECALL",
        "EXTCODEHASH",
        "EXTCODESIZE",
        "EXTCODECOPY",
        "STATICCALL",
    ),
)
async def test_allows_user_op_using_opcodes_with_contract_address(
    client, contracts, send_request_with_paymaster_using_opcode, opcode
):
    await client.send_user_op(
        send_request_with_paymaster_using_opcode(
            opcode, target=contracts.counter
        ).json()
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "opcode",
    ("EXTCODEHASH", "EXTCODESIZE", "EXTCODECOPY"),
)
async def test_rejects_user_op_using_EXTCODE_opcodes_with_eoa(
    client, send_request_with_paymaster_using_opcode, opcode
):
    await client.send_user_op(
        send_request_with_paymaster_using_opcode(
            opcode, target=accounts[0]
        ).json(),
        expected_error_message=f"The UserOp during validation accesses the code"
        " at an address that does not contain a smart contract.",
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "opcode",
    ("CALL", "CALLCODE", "DELEGATECALL", "STATICCALL"),
)
async def test_rejects_user_op_using_CALL_opcodes_with_eoa(
    client, send_request_with_paymaster_using_opcode, opcode
):
    await client.send_user_op(
        send_request_with_paymaster_using_opcode(
            opcode, target=accounts[0]
        ).json(),
        expected_error_message="The UserOp during validation calling an "
        "address that does not contain a smart contract",
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "opcode",
    ("CALL", "CALLCODE", "DELEGATECALL", "STATICCALL"),
)
async def test_rejects_user_op_using_CALL_opcodes_with_entry_point(
    client, contracts, send_request_with_paymaster_using_opcode, opcode
):
    await client.send_user_op(
        send_request_with_paymaster_using_opcode(
            opcode,
            target=contracts.entry_point,
            payload=contracts.entry_point.simulateValidation.signature[2:],
        ).json(),
        expected_error_message="The UserOp is calling the EntryPoint during "
        "validation, but only 'depositTo' method is allowed",
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "opcode",
    ("CALL", "CALLCODE", "DELEGATECALL", "STATICCALL"),
)
async def test_accepts_user_op_using_CALL_opcodes_with_entry_point_depositFor(
    client, contracts, send_request_with_paymaster_using_opcode, opcode
):
    await client.send_user_op(
        send_request_with_paymaster_using_opcode(
            opcode,
            target=contracts.entry_point,
            payload=contracts.entry_point.depositTo.signature[2:],
        ).json(),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "opcode",
    ("CALL", "CALLCODE", "DELEGATECALL", "STATICCALL"),
)
async def test_accepts_user_op_using_CALL_opcodes_with_entry_point_fallback(
    client, contracts, send_request_with_paymaster_using_opcode, opcode
):
    await client.send_user_op(
        send_request_with_paymaster_using_opcode(
            opcode,
            target=contracts.entry_point,
        ).json(),
    )


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
    client, session, contracts, send_request, send_request2
):
    await client.send_user_op(send_request.json())

    factory_bytecode_hash = utils.web3.get_bytecode_hash(
        contracts.simple_account_factory.address
    )
    await db.service.update_bytecode(session, factory_bytecode_hash, True)
    paymaster_bytecode_hash = utils.web3.get_bytecode_hash(
        contracts.paymaster.address
    )
    await db.service.update_bytecode(session, paymaster_bytecode_hash, True)
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