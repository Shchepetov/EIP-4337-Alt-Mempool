from typing import Optional

import brownie
import eth_abi
import web3.eth
from eth_account.messages import encode_defunct
from pydantic import BaseModel, Extra
from web3 import Account, Web3

from app.config import settings

DEFAULTS_FOR_USER_OP = {
    "sender": "0x0000000000000000000000000000000000000000",
    "nonce": 0,
    "init_code": "0x",
    "call_data": "0x12345678",
    "call_gas_limit": 100000,
    "verification_gas_limit": settings.max_verification_gas_limit,
    "pre_verification_gas": 10000,
    "max_fee_per_gas": settings.min_max_fee_per_gas,
    "max_priority_fee_per_gas": settings.min_max_priority_fee_per_gas,
    "paymaster_and_data": "0x",
    "signature": "0x0",
}


class UserOp(BaseModel):
    sender: str
    nonce: int
    init_code: bytes
    call_data: bytes
    call_gas_limit: Optional[int] = 0
    verification_gas_limit: Optional[int] = 200000
    pre_verification_gas: Optional[int] = 0
    max_fee_per_gas: Optional[int] = 0
    max_priority_fee_per_gas: int
    paymaster_and_data: Optional[bytes] = b""
    signature: bytes

    class Config:
        extra = Extra.allow

    def get_calldata_gas(self) -> int:
        calldata_bytes = self.encode()
        zero_bytes_count = calldata_bytes.count(0)

        return 4 * zero_bytes_count + 16 * (
            len(calldata_bytes) - zero_bytes_count
        )

    def get_required_prefund(self, with_paymaster=False):
        return (
            self.max_fee_per_gas
            * (
                self.pre_verification_gas
                + self.verification_gas_limit * (3 if with_paymaster else 1)
                + self.call_gas_limit
            )
            * 1_000_000_000
        )

    def fill_hash(self, entry_point: web3.eth.Contract) -> None:
        self.hash = (
            "0x"
            + entry_point.functions.getUserOpHash(self.values()).call().hex()
        )

    def encode(self, with_signature=True) -> bytes:
        types = [
            "address",  # sender
            "uint256",  # nonce
            "bytes",  # init_code
            "bytes",  # call_data
            "uint256",  # call_gas_limit
            "uint256",  # verification_gas_limit
            "uint256",  # pre_verification_gas
            "uint256",  # max_fee_per_gas
            "uint256",  # max_priority_fee_per_gas
            "bytes",  # paymaster_and_data
        ]
        values = [
            self.sender,
            self.nonce,
            self._to_bytes(self.init_code),
            self._to_bytes(self.call_data),
            self.call_gas_limit,
            self.verification_gas_limit,
            self.pre_verification_gas,
            self.max_fee_per_gas,
            self.max_priority_fee_per_gas,
            self._to_bytes(self.paymaster_and_data),
        ]

        if with_signature:
            types.append("bytes")
            values.append(self._to_bytes(self.signature))

        return eth_abi.encode(types, values)

    def sign(self, owner: Account, entry_point: brownie.Contract):
        s = owner.sign_message(
            encode_defunct(entry_point.getUserOpHash(self.values()))
        )
        self.signature = s.signature

    def values(self) -> list:
        return [
            self.sender,
            self.nonce,
            self.init_code,
            self.call_data,
            self.call_gas_limit,
            self.verification_gas_limit,
            self.pre_verification_gas,
            self.max_fee_per_gas,
            self.max_priority_fee_per_gas,
            self.paymaster_and_data,
            self.signature,
        ]

    @classmethod
    def _to_bytes(cls, v):
        return v if isinstance(v, bytes) else Web3.toBytes(hexstr=v)
