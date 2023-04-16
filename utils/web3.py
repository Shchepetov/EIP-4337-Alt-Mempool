import re

from brownie import web3, ZERO_ADDRESS


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
