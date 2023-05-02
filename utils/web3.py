import json
import re
from pathlib import Path
from typing import Optional

import web3.constants
from web3 import Web3
from web3.eth import Contract

from app.config import settings

with open(Path("build") / "contracts" / "EntryPoint.json") as f:
    entry_point_abi = json.load(f)["abi"]

w3 = Web3(Web3.HTTPProvider(settings.rpc_endpoint_uri))
last_seen_block = 1


def EntryPoint(address) -> Contract:
    return w3.eth.contract(address=address, abi=entry_point_abi)


def call_simulate_validation(
    user_op, entry_point
) -> (str, Optional[list[dict]]):
    call_data = entry_point.encodeABI("simulateValidation", [user_op.values()])
    if is_connected_to_testnet():
        response = w3.provider.make_request(
            "eth_call",
            [
                {
                    "from": web3.constants.ADDRESS_ZERO,
                    "to": entry_point.address,
                    "data": call_data,
                },
            ],
        )
        return response["error"]["data"], None

    response = w3.provider.make_request(
        "debug_traceCall",
        [
            {
                "from": web3.constants.ADDRESS_ZERO,
                "to": entry_point.address,
                "data": call_data,
            },
            "latest",
            {"enableMemory": True},
        ],
    )
    return response["result"]["returnValue"], response["result"]["structLogs"]


def estimate_gas(from_, to, data):
    return w3.eth.estimate_gas({"from": from_, "to": to, "data": data})


def get_address_from_first_20_bytes(address: bytes) -> str:
    address = "0x" + address[:20].hex()
    if is_address(address):
        return Web3.toChecksumAddress(address)


def get_address_from_memory(address: str) -> str:
    return Web3.toChecksumAddress("0x" + address[24:])


def get_base_fee():
    latest_block = w3.eth.get_block("latest")
    return (
        latest_block["baseFeePerGas"] if "baseFeePerGas" in latest_block else 0
    )


def get_bytecode_hash(address):
    return Web3.keccak(w3.eth.get_code(address)).hex()


def get_user_op_receipt(
    user_op_hash: str, entry_point_address: web3.eth.Address
) -> (bool, str):
    entry_point = EntryPoint(entry_point_address)

    global last_seen_block
    failed_user_op_execution_filter = (
        entry_point.events.UserOperationRevertReason.createFilter(
            fromBlock=last_seen_block,
            argument_filters={"userOpHash": user_op_hash},
        )
    )
    succeed_user_op_execution_filter = (
        entry_point.events.UserOperationEvent.createFilter(
            fromBlock=last_seen_block,
            argument_filters={"userOpHash": user_op_hash},
        )
    )
    last_seen_block = w3.eth.blockNumber

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


def is_address(s) -> bool:
    return bool(re.match(r"^(0x)[0-9a-f]{40}$", s, flags=re.IGNORECASE))


def is_connected_to_testnet() -> bool:
    return w3.eth.chain_id in (1337, 31337)


def is_contract(address) -> bool:
    if address == web3.constants.ADDRESS_ZERO:
        return False

    bytecode = w3.eth.get_code(address)
    return bool(len(bytecode))
