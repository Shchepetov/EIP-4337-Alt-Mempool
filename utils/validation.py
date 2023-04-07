import re

import web3
from fastapi import HTTPException

import db.service
from app.config import settings


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


def is_address(s) -> bool:
    return bool(re.match(r"^(0x)[0-9a-f]{40}$", s, flags=re.IGNORECASE))


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
                detail="'sender' and the first 20 bytes of 'init_code' do not "
                "represent a smart contract address.",
            )

    if user_op.verification_gas_limit > settings.max_verification_gas:
        raise HTTPException(
            status_code=422,
            detail=f"'verification_gas_limit' value is larger than the client "
            "limit of {settings.max_verification_gas}.",
        )

    if user_op.pre_verification_gas < calldata_gas(user_op):
        raise HTTPException(
            status_code=422,
            detail="'pre_verification_gas' value is insufficient to cover the "
            "gas cost of serializing UserOp to calldata.",
        )

    if any(num != "0" for num in user_op.paymaster_and_data[2:]):
        paymaster = user_op.paymaster_and_data[:42]
        if not is_contract(provider, paymaster):
            raise HTTPException(
                status_code=422,
                detail="The first 20 bytes of 'paymaster_and_data' do not "
                "represent a smart contract address.",
            )


async def is_unique(user_op, session) -> bool:
    return await db.service.get_user_op_by_hash(session, user_op.hash) is None


def is_contract(provider, address) -> bool:
    if not is_address(address) or address == web3.constants.ADDRESS_ZERO:
        return False

    bytecode = provider.eth.get_code(address)
    return bool(len(bytecode))


def calldata_gas(user_op) -> int:
    user_op_dict = dict(user_op)
    if "hash" in user_op_dict:
        user_op_dict.pop("hash")

    calldata_hex = "".join(
        (v if isinstance(v, str) else hex(v))[2:].zfill(64)
        for v in user_op_dict.values()
    )
    calldata_bytes = bytes.fromhex(calldata_hex)
    zero_bytes_count = calldata_bytes.count(0)

    return 4 * zero_bytes_count + 16 * (len(calldata_bytes) - zero_bytes_count)
