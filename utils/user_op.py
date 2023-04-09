import hashlib

import ecdsa
from eth_abi import encode
from pydantic import BaseModel, Extra

import app.constants as constants
from app.config import settings

DEFAULTS_FOR_USER_OP = {
    "sender": "0x4CDbDf63ae2215eDD6B673F9DABFf789A13D4270",
    "nonce": 0,
    "init_code": 0,
    "call_data": "0x",
    "call_gas_limit": constants.CALL_GAS,
    "verification_gas_limit": settings.max_verification_gas_limit,
    "pre_verification_gas": 21000,
    "max_fee_per_gas": settings.min_max_fee_per_gas,
    "max_priority_fee_per_gas": settings.min_max_priority_fee_per_gas,
    "paymaster_and_data": "0x",
}


class UserOp(BaseModel):
    sender: str
    nonce: int
    init_code: str
    call_data: str
    call_gas_limit: int
    verification_gas_limit: int
    pre_verification_gas: int
    max_fee_per_gas: int
    max_priority_fee_per_gas: int
    paymaster_and_data: str
    signature: str = "0x"

    class Config:
        extra = Extra.allow

    def calldata_gas(self) -> int:
        calldata_bytes = self.encode()
        zero_bytes_count = calldata_bytes.count(0)

        return 4 * zero_bytes_count + 16 * (
            len(calldata_bytes) - zero_bytes_count
        )

    def encode(self) -> bytes:
        return encode(
            [
                "address",  # sender
                "uint256",  # nonce
                "bytes32",  # init_code
                "bytes32",  # call_data
                "uint256",  # call_gas_limit
                "uint",  # verification_gas_limit
                "uint",  # pre_verification_gas
                "uint256",  # max_fee_per_gas
                "uint256",  # max_priority_fee_per_gas
                "bytes32",  # paymaster_and_data
            ],
            [
                self.sender,
                self.nonce,
                bytes.fromhex(self._keccak256(self.init_code)),
                bytes.fromhex(self._keccak256(self.call_data)),
                self.call_gas_limit,
                self.verification_gas_limit,
                self.pre_verification_gas,
                self.max_fee_per_gas,
                self.max_priority_fee_per_gas,
                bytes.fromhex(self._keccak256(self.paymaster_and_data)),
            ],
        )

    def fill_hash(self) -> None:
        data = "".join(
            (hex(v) if isinstance(v, int) else v)[2:].zfill(64)
            for v in self.values()[:-1]
        )

        self.hash = "0x" + hashlib.sha3_256(bytes.fromhex(data)).digest().hex()

    def sign(self, private_key) -> None:
        sk = ecdsa.SigningKey.from_string(
            bytes.fromhex(private_key), curve=ecdsa.SECP256k1
        )
        self.signature = "0x" + sk.sign(self.encode()).hex()

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
    def _keccak256(cls, data) -> str:
        return hashlib.sha3_256(bytes.fromhex(data[2:])).digest().hex()
