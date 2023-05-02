from dataclasses import dataclass
from typing import Optional

import brownie
from brownie import web3
from brownie.network.account import Account

import utils.web3
from utils.user_op import UserOp, DEFAULTS_FOR_USER_OP


@dataclass
class Contracts:
    entry_point: Optional[brownie.Contract] = None
    simple_account_factory: Optional[brownie.Contract] = None
    aggregated_account_factory: Optional[brownie.Contract] = None
    test_paymaster_accept_all: Optional[brownie.Contract] = None
    test_expire_paymaster: Optional[brownie.Contract] = None
    test_counter: Optional[brownie.Contract] = None
    self_destructor: Optional[brownie.Contract] = None
    test_token: Optional[brownie.Contract] = None
    aggregator: Optional[brownie.Contract] = None


class SendRequest:
    def __init__(
        self,
        entry_point: brownie.Contract,
        factory: brownie.Contract,
        paymaster: brownie.Contract,
        account: Account,
        salt: int,
    ):
        self.entry_point: str
        self.user_op: UserOp
        self._set_user_op(entry_point, factory, paymaster, account, salt)

    def _set_user_op(
        self,
        entry_point: brownie.Contract,
        factory: brownie.Contract,
        paymaster: brownie.Contract,
        account: Account,
        salt: int,
    ) -> None:
        self.entry_point = entry_point.address

        user_op = UserOp(**DEFAULTS_FOR_USER_OP)
        user_op.sender = factory.getAddress(account.address, salt)
        user_op.init_code = web3.toBytes(hexstr=factory.address) + web3.toBytes(
            hexstr=factory.createAccount.encode_input(account.address, salt)
        )
        user_op.max_fee_per_gas = (
            user_op.max_priority_fee_per_gas + 2 * utils.web3.get_base_fee()
        )
        user_op.paymaster_and_data = web3.toBytes(hexstr=paymaster.address)
        user_op.sign(account, entry_point)

        self.user_op = user_op

    def json(self):
        return {
            "user_op": {
                k: self._to_hex(v) for k, v in self.user_op.dict().items()
            },
            "entry_point": self.entry_point,
        }

    @classmethod
    def _to_hex(cls, v) -> str:
        if isinstance(v, str):
            return v
        if isinstance(v, int):
            return hex(v)
        if isinstance(v, bytes):
            return "0x" + bytes.hex(v)
