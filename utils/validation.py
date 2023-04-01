import re
import time
from pathlib import Path

from Crypto.Hash import keccak
from fastapi import HTTPException
from web3 import Web3
from web3.constants import ADDRESS_ZERO

FORBIDDEN_OPCODES = (
    "GASPRICE",
    "GASLIMIT",
    "DIFFICULTY",
    "TIMESTAMP",
    "BASEFEE",
    "BLOCKHASH",
    "NUMBER",
    "SELFBALANCE",
    "BALANCE",
    "ORIGIN",
    "CREATE",
    "COINBASE",
    "SELFDESTRUCT",
)


class ValidationResult:
    pre_op_gas: int
    prefund: int
    sig_failed: bool
    valid_after: int
    valid_until: int

    def __init__(self, simulation_return_data: bytes):
        data = (simulation_return_data[32 * k : 32 * (k + 1)] for k in range(5))

        for field in [
            "pre_op_gas",
            "prefund",
            "sig_failed",
            "valid_after",
            "valid_until",
        ]:
            setattr(self, field, int.from_bytes(next(data), byteorder="big"))


def is_checksum_address(s):
    address = s.replace("0x", "")
    address_hash = keccak.new(digest_bits=256)
    address_hash = address_hash.update(
        address.lower().encode("utf-8")
    ).hexdigest()

    for i in range(0, 40):
        # The nth letter should be uppercase if the nth digit of casemap is 1
        if (
            int(address_hash[i], 16) > 7 and address[i].upper() != address[i]
        ) or (
            int(address_hash[i], 16) <= 7 and address[i].lower() != address[i]
        ):
            return False
    return True


def is_address(s):
    if not re.match(r"^(0x)?[0-9a-f]{40}$", s, flags=re.IGNORECASE):
        # Check if it has the basic requirements of an address
        return False
    elif re.match(r"^(0x)?[0-9a-f]{40}$", s) or re.match(
        r"^(0x)?[0-9A-F]{40}$", s
    ):
        # If it's all small caps or all caps, return true
        return True
    else:
        # Otherwise check each case
        return is_checksum_address(s)


def is_hex(s):
    return bool(re.fullmatch(r"0x[0-9a-fA-F]+", s))


def validate_user_op(
    user_op,
    rpc_server,
    entry_point_address,
    expires_soon_interval,
    check_forbidden_opcodes=False,
) -> (ValidationResult, int):
    # TODO: УБрать
    validation_result = ValidationResult()
    validation_result.valid_after = 0
    validation_result.valid_until = 0
    validation_result.sig_failed = False
    validation_result.pre_op_gas = 14880
    validation_result.prefund = 1000000
    current_time = time.time()
    return validation_result, current_time
    # TODO: УБрать

    w3 = Web3(Web3.HTTPProvider(rpc_server))
    abi = (Path("abi") / "EntryPoint.abi").read_text()
    entry_point = w3.eth.contract(address=entry_point_address, abi=abi)

    if user_op.init_code:
        # Check if the first bytes of init_code is an address
        if len(user_op.init_code) < 42:
            raise HTTPException(
                status_code=422, detail='"init_code" is less than 20 bytes'
            )
    # Check if the sender is an existing contract
    elif not w3.eth.get_code(user_op.sender):
        raise HTTPException(
            status_code=422,
            detail='"sender" is not an existing contract but "init_code" is empty',
        )

    # Simulate validation
    call_data = entry_point.encodeABI(
        "simulateValidation", [tuple(v for k, v in user_op)]
    )
    result = w3.provider.make_request(
        "debug_traceCall",
        [
            {
                "from": ADDRESS_ZERO,
                "to": entry_point_address,
                "data": call_data,
            },
            "latest",
        ],
    )["result"]

    return_value = result["returnValue"]
    selector = return_value[:8]
    if selector not in (
        "f04297e9",  # ValidationResult
        "356877a3",  # ValidationResultWithAggregation
    ):
        raise HTTPException(
            status_code=422,
            detail=f"Simulation failed with return data: {return_value}",
        )

    validation_result = ValidationResult(bytes.fromhex(return_value[8:]))

    current_time = time.time()
    if (
        validation_result.sig_failed
        and validation_result.valid_after <= current_time
    ):
        raise HTTPException(status_code=422, detail="UserOp signing failed")
    if 0 < validation_result.valid_until < current_time + expires_soon_interval:
        raise HTTPException(
            status_code=422,
            detail="UserOp is expired or will expire within the next 15 seconds",
        )

    # TODO: validate stakes and storage access
    # Check forbidden opcodes
    if check_forbidden_opcodes and have_forbidden_opcodes(
        result["result"], initializing=True if len(user_op.init_code) else False
    ):
        raise HTTPException(
            status_code=422, detail="UserOp have forbidden opcodes"
        )

    return validation_result, current_time


def have_forbidden_opcodes(struct_logs, initializing=False):
    create2_can_be_called = initializing
    for i in range(len(struct_logs)):
        op = struct_logs[i]["op"]

        if struct_logs[i]["depth"] == 1:
            if create2_can_be_called and op == "NUMBER":
                create2_can_be_called = False
            continue

        if op in FORBIDDEN_OPCODES:
            return True

        if op == "CREATE2":
            if not create2_can_be_called:
                return True
            create2_can_be_called = False
            continue

        if op == "GAS" and struct_logs[i + 1]["op"] not in (
            "CALL",
            "DELEGATECALL",
            "CALLCODE",
            "STATICCALL",
        ):
            return True

        # TODO: allow not malicious "REVERT" opcode
        if op == "REVERT" and i != len(struct_logs) - 1:
            return True

    return False
