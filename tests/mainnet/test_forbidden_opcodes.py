import brownie
import pytest
from brownie import accounts


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
    client, send_request_with_paymaster_from_network_using_opcode, opcode
):
    await client.send_user_op(
        send_request_with_paymaster_from_network_using_opcode(opcode).json(),
        expected_error_message=f"The UserOp is using the forbidden opcode "
        f"'{opcode}' during validation",
    )


@pytest.mark.asyncio
async def test_rejects_user_op_using_SELFDESTRUCT(
    client,
    test_contracts,
    send_request_with_paymaster_from_network_using_opcode,
):
    await client.send_user_op(
        send_request_with_paymaster_from_network_using_opcode(
            "CALL", test_contracts.self_destructor
        ).json(),
        expected_error_message=f"The UserOp is using the forbidden opcode "
        f"'SELFDESTRUCT' during validation",
    )


@pytest.mark.asyncio
async def test_rejects_user_op_using_CREATE2_after_initialization(
    client,
    test_contracts,
    send_request_with_paymaster_from_network_using_opcode,
):
    await client.send_user_op(
        send_request_with_paymaster_from_network_using_opcode(
            "CREATE2", test_contracts.test_counter
        ).json(),
        expected_error_message="The UserOp is using the 'CREATE2' opcode in an "
        "unacceptable context.",
    )


@pytest.mark.asyncio
async def test_rejects_user_op_using_CREATE2_without_initialization(
    client,
    test_contracts,
    send_request,
    send_request_with_paymaster_from_network_using_opcode,
):
    test_contracts.entry_point.handleOps(
        [send_request.user_op.values()], test_account.address
    )
    send_request_with_paymaster_using_CREATE2 = (
        send_request_with_paymaster_from_network_using_opcode(
            "CREATE2", test_contracts.test_counter
        )
    )
    send_request.user_op.init_code = "0x"
    send_request.paymaster_and_data = (
        send_request_with_paymaster_using_CREATE2.user_op.paymaster_and_data
    )
    send_request.user_op.call_data = (
        test_contracts.test_counter.address
        + test_contracts.test_counter.count.encode_input()[2:]
    )
    send_request.user_op.sign(test_account.address, test_contracts.entry_point)

    await client.send_user_op(
        send_request.json(),
        expected_error_message="The UserOp is using the 'CREATE2' opcode in an "
        "unacceptable context.",
    )


@pytest.mark.asyncio
async def test_rejects_user_op_using_GAS_not_before_external_call(
    client, send_request_with_paymaster_from_network_using_opcode
):
    await client.send_user_op(
        send_request_with_paymaster_from_network_using_opcode("GAS").json(),
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
    client,
    test_contracts,
    send_request_with_paymaster_from_network_using_opcode,
    opcode,
):
    await client.send_user_op(
        send_request_with_paymaster_from_network_using_opcode(
            f"{opcode}", test_contracts.test_counter
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
    client,
    test_contracts,
    send_request_with_paymaster_from_network_using_opcode,
    opcode,
):
    await client.send_user_op(
        send_request_with_paymaster_from_network_using_opcode(
            opcode, target=test_contracts.test_counter
        ).json()
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "opcode",
    ("EXTCODEHASH", "EXTCODESIZE", "EXTCODECOPY"),
)
async def test_rejects_user_op_using_EXTCODE_opcodes_with_eoa(
    client, send_request_with_paymaster_from_network_using_opcode, opcode
):
    await client.send_user_op(
        send_request_with_paymaster_from_network_using_opcode(
            opcode, target=test_account
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
    client, send_request_with_paymaster_from_network_using_opcode, opcode
):
    await client.send_user_op(
        send_request_with_paymaster_from_network_using_opcode(
            opcode, target=test_account
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
    client,
    test_contracts,
    send_request_with_paymaster_from_network_using_opcode,
    opcode,
):
    await client.send_user_op(
        send_request_with_paymaster_from_network_using_opcode(
            opcode,
            target=test_contracts.entry_point,
            payload=test_contracts.entry_point.simulateValidation.signature[2:],
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
    client,
    test_contracts,
    send_request_with_paymaster_from_network_using_opcode,
    opcode,
):
    await client.send_user_op(
        send_request_with_paymaster_from_network_using_opcode(
            opcode,
            target=test_contracts.entry_point,
            payload=test_contracts.entry_point.depositTo.signature[2:],
        ).json(),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "opcode",
    ("CALL", "CALLCODE", "DELEGATECALL", "STATICCALL"),
)
async def test_accepts_user_op_using_CALL_opcodes_with_entry_point_fallback(
    client,
    test_contracts,
    send_request_with_paymaster_from_network_using_opcode,
    opcode,
):
    await client.send_user_op(
        send_request_with_paymaster_from_network_using_opcode(
            opcode,
            target=test_contracts.entry_point,
        ).json(),
    )


@pytest.mark.asyncio
async def test_adds_rejected_bytecode_to_blacklist(
    client, send_request_with_paymaster_from_network_using_opcode
):
    opcode = "BLOCKHASH"
    await client.send_user_op(
        send_request_with_paymaster_from_network_using_opcode(opcode).json(),
        expected_error_message=f"The UserOp is using the forbidden opcode "
        f"'{opcode}' during validation",
    )

    await client.send_user_op(
        send_request_with_paymaster_from_network_using_opcode(opcode).json(),
        expected_error_message="The UserOp contains calls to smart test_contracts, "
        "the bytecode of which is listed in the blacklist",
    )

    opcode = "GASLIMIT"
    await client.send_user_op(
        send_request_with_paymaster_from_network_using_opcode(opcode).json(),
        expected_error_message=f"The UserOp is using the forbidden opcode "
        f"'{opcode}' during validation",
    )
