import re

import web3
from brownie import EntryPoint
from fastapi import HTTPException

import app.constants as constants
import db.service
from app.config import settings


class SimulationResult:
    sig_failed: bool
    valid_after: int
    valid_until: int


def validate_address(v):
    v = validate_hex(v)
    if v == "0x":
        return web3.constants.ADDRESS_ZERO
    if not is_address(v):
        raise HTTPException(
            status_code=422, detail="Must be an Ethereum address."
        )

    return v


def is_address(s) -> bool:
    return bool(re.match(r"^(0x)[0-9a-f]{40}$", s, flags=re.IGNORECASE))


def validate_hex(v):
    if not (isinstance(v, str) and re.fullmatch(r"0x[0-9a-fA-F]*", v)):
        raise HTTPException(status_code=422, detail="Not a hex value.")

    return v


async def validate_user_op(
    session,
    rpc_server,
    user_op,
    entry_point_address,
    expires_soon_interval,
    check_forbidden_opcodes=False,
) -> SimulationResult:
    provider = web3.Web3(web3.Web3.HTTPProvider(rpc_server))
    entry_point = EntryPoint.at(entry_point_address)

    await validate_before_simulation(provider, session, user_op, entry_point)
    return run_simulation(user_op, entry_point)


async def validate_before_simulation(provider, session, user_op, entry_point):
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

    if user_op.call_gas_limit < constants.CALL_GAS:
        raise HTTPException(
            status_code=422,
            detail=f"'call_gas_limit' is less than {constants.CALL_GAS}, which "
            "is the minimum gas cost of a 'CALL' with non-zero value.",
        )

    if user_op.pre_verification_gas < user_op.get_calldata_gas():
        raise HTTPException(
            status_code=422,
            detail="'pre_verification_gas' value is insufficient to cover the "
            "gas cost of serializing UserOp to calldata.",
        )

    if user_op.verification_gas_limit > settings.max_verification_gas_limit:
        raise HTTPException(
            status_code=422,
            detail=f"'verification_gas_limit' value is larger than the client "
            f"limit of {settings.max_verification_gas_limit}.",
        )

    if user_op.max_fee_per_gas < settings.min_max_fee_per_gas:
        raise HTTPException(
            status_code=422,
            detail="'max_fee_per_gas' value is less than the client limit of "
            f"{settings.min_max_fee_per_gas}.",
        )

    if user_op.max_priority_fee_per_gas < settings.min_max_priority_fee_per_gas:
        raise HTTPException(
            status_code=422,
            detail="'max_priority_fee_per_gas' value is less than the client "
            f"limit of {settings.min_max_priority_fee_per_gas}.",
        )

    if user_op.max_fee_per_gas < user_op.max_priority_fee_per_gas + base_fee(
        provider
    ):
        raise HTTPException(
            status_code=422,
            detail="'max_fee_per_gas' and 'max_priority_fee_per_gas' are not "
            "sufficiently high to be included with the current block.",
        )

    if any(num != "0" for num in user_op.paymaster_and_data[2:]):
        paymaster = user_op.paymaster_and_data[:42]
        if not is_contract(provider, paymaster):
            raise HTTPException(
                status_code=422,
                detail="The first 20 bytes of 'paymaster_and_data' do not "
                "represent a smart contract address.",
            )

        if entry_point.balanceOf(paymaster) < user_op.get_required_prefund(
            with_paymaster=True
        ):
            raise HTTPException(
                status_code=422,
                detail="The paymaster does not have sufficient funds to pay "
                "for the UserOp.",
            )


async def is_unique(user_op, session) -> bool:
    return await db.service.get_user_op_by_hash(session, user_op.hash) is None


def is_contract(provider, address) -> bool:
    if not is_address(address) or address == web3.constants.ADDRESS_ZERO:
        return False

    bytecode = provider.eth.get_code(address)
    return bool(len(bytecode))


def base_fee(provider):
    latest_block = provider.eth.get_block("latest")
    return (
        latest_block["baseFeePerGas"] if "baseFeePerGas" in latest_block else 0
    )


def run_simulation(user_op, entry_point) -> SimulationResult:
    try:
        entry_point.simulateValidation(user_op.values())
    except Exception as e:
        err_msg = e.revert_msg.replace("typed error: ", "")
        if err_msg[:10].lower() not in (
            "0xe0cff05f"  # ValidationResult
            "0xf2a8087f"  # ValidationResultWithAggregation
        ):
            raise HTTPException(
                status_code=422,
                detail=f"The simulation of the UserOp has failed with an "
                f"error: {err_msg}",
            )

    simulation_result = SimulationResult()
    simulation_result.valid_after = 0
    simulation_result.valid_until = 0
    simulation_result.sig_failed = False

    return simulation_result
