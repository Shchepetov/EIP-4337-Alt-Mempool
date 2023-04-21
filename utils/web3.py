import re

import brownie
from brownie import web3, EntryPoint, ZERO_ADDRESS
from web3 import Web3

last_seen_block = 0


def get_base_fee():
    latest_block = web3.eth.get_block("latest")
    return (
        latest_block["baseFeePerGas"] if "baseFeePerGas" in latest_block else 0
    )


def get_bytecode_hash(address):
    return web3.keccak(web3.eth.get_code(address)).hex()


def is_address(s) -> bool:
    return bool(re.match(r"^(0x)[0-9a-f]{40}$", s, flags=re.IGNORECASE))


def is_contract(address) -> bool:
    if not is_address(address) or address == ZERO_ADDRESS:
        return False

    bytecode = web3.eth.get_code(address)
    return bool(len(bytecode))


def address_from_memory(address: str) -> str:
    return web3.toChecksumAddress("0x" + address[24:])


def get_user_op_receipt(
    user_op_hash: str, entry_point_address: str
) -> (bool, str):
    global last_seen_block

    entry_point = EntryPoint.at(entry_point_address)
    w3 = Web3(Web3.HTTPProvider(brownie.web3.provider.endpoint_uri))
    contract = w3.eth.contract(address=entry_point_address, abi=entry_point.abi)
    failed_user_op_execution_filter = (
        contract.events.UserOperationRevertReason.createFilter(
            fromBlock=last_seen_block,
            argument_filters={"userOpHash": user_op_hash},
        )
    )
    succeed_user_op_execution_filter = (
        contract.events.UserOperationEvent.createFilter(
            fromBlock=last_seen_block,
            argument_filters={"userOpHash": user_op_hash},
        )
    )

    last_seen_block = brownie.chain.height

    failed_user_op_executions = (
        failed_user_op_execution_filter.get_all_entries()
    )
    if len(failed_user_op_executions):
        return failed_user_op_executions[0].transactionHash, False

    succeed_user_op_executions = (
        succeed_user_op_execution_filter.get_all_entries()
    )
    if len(succeed_user_op_executions):
        return succeed_user_op_executions[0].transactionHash, True

    return None, None
