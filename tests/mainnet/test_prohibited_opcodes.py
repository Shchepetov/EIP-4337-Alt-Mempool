import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "opcode",
    (
        "BALANCE",
        "BASEFEE",
        "BLOCKHASH",
        "COINBASE",
        "CREATE",
        "GASLIMIT",
        "GASPRICE",
        "NUMBER",
        "ORIGIN",
        "PREVRANDAO",
        "SELFBALANCE",
        "TIMESTAMP",
    ),
)
async def test_rejects_user_op_using_prohibited_opcodes(
    client, send_request_with_paymaster_from_network_using_opcode, opcode
):
    await client.send_user_op(
        send_request_with_paymaster_from_network_using_opcode(opcode).json(),
        expected_error_message=f"The UserOp is using the prohibited opcode "
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
        expected_error_message=f"The UserOp is using the prohibited opcode "
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
    ("EXTCODECOPY", "EXTCODEHASH", "EXTCODESIZE"),
)
async def test_rejects_user_op_using_EXTCODE_opcodes_with_eoa(
    client,
    test_account,
    send_request_with_paymaster_from_network_using_opcode,
    opcode,
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
    client,
    test_account,
    send_request_with_paymaster_from_network_using_opcode,
    opcode,
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
        expected_error_message=f"The UserOp is using the prohibited opcode "
        f"'{opcode}' during validation",
    )

    await client.send_user_op(
        send_request_with_paymaster_from_network_using_opcode(opcode).json(),
        expected_error_message="The UserOp contains calls to smart contracts, "
        "the bytecode of which is listed in the blacklist",
    )

    opcode = "GASLIMIT"
    await client.send_user_op(
        send_request_with_paymaster_from_network_using_opcode(opcode).json(),
        expected_error_message=f"The UserOp is using the prohibited opcode "
        f"'{opcode}' during validation",
    )
