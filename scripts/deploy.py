import os
import sys

import typer

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import brownie
from brownie import (
    accounts,
    TestPaymasterAcceptAll,
    SimpleAccountFactory,
    EntryPoint,
    SelfDestructor,
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

    simple_account_factory = selected_account.deploy(
        SimpleAccountFactory, entry_point.address
    )
    data["SimpleAccountFactory"] = simple_account_factory.address

    test_paymaster = selected_account.deploy(
        TestPaymasterAcceptAll, entry_point.address
    )
    data["TestPaymasterAcceptAll"] = test_paymaster.address

    for opcode in (
        "GASPRICE",
        "GASLIMIT",
        "DIFFICULTY",
        "TIMESTAMP",
        "BLOCKHASH",
        "NUMBER",
        "SELFBALANCE",
        "BALANCE",
        "ORIGIN",
        "CREATE",
        "COINBASE",
        "CREATE2",
        "CALL",
        "CALLCODE",
        "DELEGATECALL",
        "STATICCALL",
        "EXTCODEHASH",
        "EXTCODESIZE",
        "EXTCODECOPY",
    ):
        contract_name = f"TestPaymaster{opcode}"
        contract = selected_account.deploy(
            getattr(brownie, contract_name), entry_point.address
        )
        data[contract_name] = contract.address

    utils.deployments.save(data, brownie.network.show_active())
