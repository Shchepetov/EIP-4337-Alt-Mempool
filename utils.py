import re

from Crypto.Hash import keccak

FORBIDDEN_OPCODES = (
    "GASPRICE",
    "GASLIMIT",
    "DIFFICULTY",
    "TIMESTAMP",
    "BASEFEE",
    "BLOCKHASH",
    "NUMBER" "SELFBALANCE",
    "BALANCE",
    "ORIGIN",
    "CREATE",
    "COINBASE",
    "SELFDESTRUCT",
)


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


def is_checksum_address(address):
    address = address.replace("0x", "")
    address_hash = keccak.new(digest_bits=256)
    address_hash = address_hash.update(address.lower().encode("utf-8")).hexdigest()

    for i in range(0, 40):
        # The nth letter should be uppercase if the nth digit of casemap is 1
        if (int(address_hash[i], 16) > 7 and address[i].upper() != address[i]) or (
            int(address_hash[i], 16) <= 7 and address[i].lower() != address[i]
        ):
            return False
    return True


def is_address(address):
    if not re.match(r"^(0x)?[0-9a-f]{40}$", address, flags=re.IGNORECASE):
        # Check if it has the basic requirements of an address
        return False
    elif re.match(r"^(0x)?[0-9a-f]{40}$", address) or re.match(
        r"^(0x)?[0-9A-F]{40}$", address
    ):
        # If it's all small caps or all caps, return true
        return True
    else:
        # Otherwise check each case
        return is_checksum_address(address)


def is_uint256(x):
    return isinstance(x, int) and 0 <= x < 2**256
