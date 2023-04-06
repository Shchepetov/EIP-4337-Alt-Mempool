import re

from Crypto.Hash import keccak
from fastapi import HTTPException

import db.service
import web3


class SimulationResult:
    sig_failed: bool
    valid_after: int
    valid_until: int


def validate_address(v):
    v = validate_hex(v)
    if v == "0x0":
        return web3.constants.ADDRESS_ZERO
    if not is_address(v):
        raise HTTPException(
            status_code=422, detail="Must be an Ethereum address."
        )

    return v


def is_address(s):
    if not re.match(r"^(0x)[0-9a-f]{40}$", s, flags=re.IGNORECASE):
        # Check if it has the basic requirements of an address
        return False
    elif re.match(r"^(0x)[0-9a-f]{40}$", s) or re.match(
        r"^(0x)[0-9A-F]{40}$", s
    ):
        # If it's all small caps or all caps, return true
        return True
    else:
        # Otherwise check each case
        return is_checksum_address(s)


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


def validate_hex(v):
    if not (isinstance(v, str) and re.fullmatch(r"0x[0-9a-fA-F]+", v)):
        raise HTTPException(status_code=422, detail="Not a hex value.")

    return v


async def validate_user_op(
    session,
    user_op,
    rpc_server,
    entry_point_address,
    expires_soon_interval,
    check_forbidden_opcodes=False,
) -> (SimulationResult):
    provider = web3.Web3(web3.Web3.HTTPProvider(rpc_server))
    await validate_before_simulation(provider, session, user_op)

    simulation_result = SimulationResult()
    simulation_result.valid_after = 0
    simulation_result.valid_until = 0
    simulation_result.sig_failed = False

    return simulation_result


async def validate_before_simulation(provider, session, user_op):
    if not await is_unique(user_op, session):
        raise HTTPException(
            status_code=422,
            detail="UserOp is already in the pool.",
        )

    if not is_contract(provider, user_op.sender):
        factory_address = user_op.init_code[:42]
        if not (
            is_address(factory_address)
            and is_contract(provider, factory_address)
        ):
            raise HTTPException(
                status_code=422,
                detail="'sender' and the first 20 bytes of 'init_code' do not represent a smart contract address.",
            )



async def is_unique(user_op, session) -> bool:
    return await db.service.get_user_op_by_hash(session, user_op.hash) is None


def is_contract(provider, address) -> bool:
    if address == web3.constants.ADDRESS_ZERO:
        return False
    bytecode = provider.eth.getCode(address)
    return bool(len(bytecode))
