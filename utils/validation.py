import re
import time

import brownie
import eth_abi
import hexbytes
from brownie import EntryPoint, history, ZERO_ADDRESS
from fastapi import HTTPException

import app.constants as constants
import db.service
import utils.web3
from app.config import settings

FORBIDDEN_OPCODES = (
    "GASPRICE",
    "GASLIMIT",
    "DIFFICULTY",
    "PREVRANDAO",
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
    def __init__(self, validation_result_string):
        types = [
            "(uint256,uint256,bool,uint48,uint48,bytes)",
            "(uint256,uint256)",
            "(uint256,uint256)",
            "(uint256,uint256)",
        ]
        selector = validation_result_string[:10].lower()
        if selector == "0xf2a8087f":  # ValidationResultWithAggregation
            types.append("(address,(uint256,uint256))")
        elif selector != "0xe0cff05f":  # ValidationResult
            raise HTTPException(
                status_code=422,
                detail=f"The simulation of the UserOp has failed with an "
                f"error: {validation_result_string}",
            )
        decoded = eth_abi.decode(
            types, bytes.fromhex(validation_result_string[10:])
        )
        (
            self.pre_op_gas,
            self.prefund,
            self.sig_failed,
            self.valid_after,
            self.valid_until,
            self.paymaster_context,
        ) = decoded[0]


def validate_address(v):
    v = validate_hex(v)
    if v == "0x":
        return ZERO_ADDRESS
    if not utils.web3.is_address(v):
        raise HTTPException(
            status_code=422, detail="Must be an Ethereum address."
        )

    return v


def validate_hex(v):
    if not (isinstance(v, str) and re.fullmatch(r"0x[0-9a-fA-F]*", v)):
        raise HTTPException(status_code=422, detail="Not a hex value.")

    return v


async def validate_user_op(
    session, user_op, entry_point_address
) -> (ValidationResult, bool, int, hexbytes.HexBytes):
    entry_point = EntryPoint.at(entry_point_address)

    initializing, used_bytecode_hashes = await validate_before_simulation(
        session, user_op, entry_point
    )
    validation_result, expires_at = run_simulation(user_op, entry_point)
    is_trusted = await db.service.all_trusted_bytecodes(
        session, used_bytecode_hashes
    )
    if not is_trusted:
        await validate_after_simulation(entry_point, initializing)

    return validation_result, is_trusted, expires_at, used_bytecode_hashes


async def validate_before_simulation(
    session, user_op, entry_point
) -> (bool, list[hexbytes.HexBytes]):
    used_contracts = []
    if await db.service.get_user_op_by_hash(session, user_op.hash) is not None:
        raise HTTPException(
            status_code=422,
            detail="UserOp is already in the pool.",
        )

    if utils.web3.is_contract(user_op.sender):
        initializing = False
        used_contracts.append(user_op.sender)
    else:
        initializing = True
        factory_address = user_op.init_code[:42]
        if not (
            utils.web3.is_address(factory_address)
            and utils.web3.is_contract(factory_address)
        ):
            raise HTTPException(
                status_code=422,
                detail="'sender' and the first 20 bytes of 'init_code' do not "
                "represent a smart contract address.",
            )
        used_contracts.append(factory_address)

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

    if (
        user_op.max_fee_per_gas
        < user_op.max_priority_fee_per_gas + utils.web3.get_base_fee()
    ):
        raise HTTPException(
            status_code=422,
            detail="'max_fee_per_gas' and 'max_priority_fee_per_gas' are not "
            "sufficiently high to be included with the current block.",
        )

    if any(num != "0" for num in user_op.paymaster_and_data[2:]):
        paymaster_addresss = user_op.paymaster_and_data[:42]
        if not utils.web3.is_contract(paymaster_addresss):
            raise HTTPException(
                status_code=422,
                detail="The first 20 bytes of 'paymaster_and_data' do not "
                "represent a smart contract address.",
            )

        if entry_point.balanceOf(
            paymaster_addresss
        ) < user_op.get_required_prefund(with_paymaster=True):
            raise HTTPException(
                status_code=422,
                detail="The paymaster does not have sufficient funds to pay "
                "for the UserOp.",
            )

        used_contracts.append(paymaster_addresss)

    used_bytecode_hashes = [
        utils.web3.get_bytecode_hash(address) for address in used_contracts
    ]
    if await db.service.any_banned_bytecodes(session, used_bytecode_hashes):
        raise HTTPException(
            status_code=422,
            detail="The UserOp contains calls to smart contracts, the bytecode "
            "of which is listed in the blacklist.",
        )

    return initializing, used_bytecode_hashes


def run_simulation(user_op, entry_point) -> (ValidationResult, int):
    try:
        entry_point.simulateValidation(user_op.values())
        raise HTTPException(
            status_code=500, detail="The simulation didn't revert."
        )
    except Exception as e:
        err_msg = e.revert_msg.replace("typed error: ", "")

    validation_result = ValidationResult(err_msg)
    current_timestamp = int(time.time())
    if validation_result.valid_until <= current_timestamp:
        raise HTTPException(
            status_code=422,
            detail="Unable to add the UserOp as it is expired.",
        )
    if (
        validation_result.valid_after
        > current_timestamp + settings.user_op_lifetime
    ):
        raise HTTPException(
            status_code=422,
            detail="Unable to add the UserOp as it expires in the pool before "
            "its validity period starts.",
        )
    expires_at = min(
        current_timestamp + settings.user_op_lifetime,
        validation_result.valid_until,
    )

    return validation_result, expires_at


async def validate_after_simulation(
    entry_point: brownie.Contract, initializing: bool
):
    validate_called_instructions(
        history[-1].trace, entry_point, initializing=initializing
    )


def validate_called_instructions(
    instructions: list[dict], entry_point: brownie.Contract, initializing: bool
):
    create2_can_be_called = initializing
    for i in range(len(instructions)):
        if instructions[i][
            "address"
        ] == entry_point.address or not is_caller_known(instructions[i]):
            continue

        opcode = instructions[i]["op"]
        if opcode in FORBIDDEN_OPCODES:
            raise HTTPException(
                status_code=422,
                detail=f"The UserOp is using the forbidden opcode '{opcode}' "
                f"during validation.",
            )

        if opcode == "CREATE2":
            if not create2_can_be_called:
                raise HTTPException(
                    status_code=422,
                    detail="The UserOp is using the 'CREATE2' opcode in an "
                    "unacceptable context.",
                )
            create2_can_be_called = False
            continue

        if opcode == "GAS" and instructions[i + 1]["op"] not in (
            "CALL",
            "DELEGATECALL",
            "CALLCODE",
            "STATICCALL",
        ):
            raise HTTPException(
                status_code=422,
                detail="The UserOp is using the 'GAS' opcode during validation,"
                " but not before the external call",
            )

        if opcode == "NUMBER":
            create2_can_be_called = False
            continue

        if opcode in (
            "EXTCODEHASH",
            "EXTCODESIZE",
            "EXTCODECOPY",
        ):
            target = instructions[i]["stack"][-1]
            if not utils.web3.is_contract(target):
                raise HTTPException(
                    status_code=422,
                    detail="The UserOp during validation accesses the code at "
                    "an address that does not contain a smart contract.",
                )

        if opcode in (
            "CALL",
            "CALLCODE",
            "DELEGATECALL",
            "STATICCALL",
        ):
            target = instructions[i]["stack"][-2]
            if not utils.web3.is_contract(target):
                raise HTTPException(
                    status_code=422,
                    detail="The UserOp during validation calling an address "
                    "that does not contain a smart contract.",
                )


def is_caller_known(instruction: dict) -> bool:
    return not instruction["fn"].startswith("<UnknownContract>")
