import re
import time

from Crypto.Hash import keccak
from fastapi import HTTPException


class ValidationResult:
    sig_failed: bool
    valid_after: int
    valid_until: int


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
) -> (ValidationResult):
    validation_result = ValidationResult()
    validation_result.valid_after = 0
    validation_result.valid_until = 0
    validation_result.sig_failed = False
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

    return validation_result
