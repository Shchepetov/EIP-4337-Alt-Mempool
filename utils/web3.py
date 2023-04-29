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
    if address == ZERO_ADDRESS:
        return False

    bytecode = web3.eth.get_code(address)
    return bool(len(bytecode))


def is_connected_to_testnet() -> bool:
    return brownie.chain.id in (1337, 31337)


def get_address_from_memory(address: str) -> str:
    return web3.toChecksumAddress("0x" + address[24:])


def get_address_from_first_20_bytes(address: bytes) -> str:
    address = "0x" + address[:20].hex()
    if is_address(address):
        return web3.toChecksumAddress(address)


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


def estimate_gas(from_, to, data):
    w3 = Web3(Web3.HTTPProvider(brownie.web3.provider.endpoint_uri))
    return w3.eth.estimate_gas({"from": from_, "to": to, "data": data})


def call_simulate_validation(user_op, entry_point) -> dict:
    w3 = Web3(Web3.HTTPProvider(brownie.web3.provider.endpoint_uri))
    if is_connected_to_testnet:
        return w3.provider.make_request(
            "eth_call",
            [
                {
                    "from": ZERO_ADDRESS,
                    "to": entry_point.address,
                    "data": entry_point.simulateValidation.encode_input(
                        user_op.values()
                    ),
                },
            ],
        )
    return w3.provider.make_request(
        "debug_traceCall",
        [
            {
                "from": ZERO_ADDRESS,
                "to": entry_point.address,
                "data": entry_point.simulateValidation.encode_input(
                    user_op.values()
                ),
            },
            "latest",
            {"enableMemory": True},
        ],
    )
