import os
import sys

import typer

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import brownie
from brownie import (
    accounts,
    EntryPoint,
    SelfDestructor,
    SimpleAccountFactory,
    TestCounter,
    TestPaymasterAcceptAll,
    TestToken,
)

import utils.deployments

cli = typer.Typer()


@cli.command()
def deploy_all(from_id: str):
    selected_account = accounts.load(from_id)
    data = {}

    entry_point = selected_account.deploy(EntryPoint)
    data["EntryPoint"] = entry_point.address

    self_destructor = selected_account.deploy(SelfDestructor)
    data["SelfDestructor"] = self_destructor.address

    test_token = selected_account.deploy(TestToken)
    data["TestToken"] = test_token.address

    test_counter = selected_account.deploy(TestCounter)
    data["TestCounter"] = test_counter.address

    simple_account_factory = selected_account.deploy(
        SimpleAccountFactory, entry_point.address
    )
    data["SimpleAccountFactory"] = simple_account_factory.address

    test_paymaster = selected_account.deploy(
        TestPaymasterAcceptAll, entry_point.address
    )
    data["TestPaymasterAcceptAll"] = test_paymaster.address

    for opcode in (
        "BALANCE",
        "BASEFEE",
        "BLOCKHASH",
        "CALL",
        "CALLCODE",
        "CREATE",
        "CREATE2",
        "DELEGATECALL",
        "DIFFICULTY",
        "EXTCODECOPY",
        "EXTCODEHASH",
        "EXTCODESIZE",
        "GAS",
        "GASLIMIT",
        "GASPRICE",
        "NUMBER",
        "ORIGIN",
        "SELFBALANCE",
        "STATICCALL",
        "TIMESTAMP",
    ):
        contract_name = f"TestPaymaster{opcode}"
        contract = selected_account.deploy(
            getattr(brownie, contract_name), entry_point.address
        )
        data[contract_name] = contract.address

    utils.deployments.save(data, brownie.network.show_active())
