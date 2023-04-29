from dataclasses import dataclass

import brownie
from brownie.network.account import Account
from typing import Optional
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
        test_contracts: Contracts,
        test_account: Account,
        salt: int,
    ):
        self.entry_point: str
        self.user_op: UserOp
        self._set_user_op(test_contracts, test_account, salt)

    def _set_user_op(
        self, test_contracts: Contracts, test_account: Account, salt: int
    ) -> None:
        self.entry_point = test_contracts.entry_point.address

        user_op = UserOp(**DEFAULTS_FOR_USER_OP)
        user_op.sender = test_contracts.simple_account_factory.getAddress(
            test_account.address, salt
        )
        user_op.init_code = (
            test_contracts.simple_account_factory.address
            + test_contracts.simple_account_factory.createAccount.encode_input(
                test_account.address, salt
            )[2:]
        )
        user_op.paymaster_and_data = (
            test_contracts.test_paymaster_accept_all.address
        )
        user_op.sign(test_account.address, test_contracts.entry_point)

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
