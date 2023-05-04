import os
import sys

import typer

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import brownie
from brownie import accounts, EntryPoint, SimpleAccountFactory

import utils.deployments

cli = typer.Typer()


@cli.command()
def deploy_test_contracts(from_id: str, paymaster_deposit: str = "1000 gwei"):
    account = accounts.load(from_id)
    data = {}

    entry_point = account.deploy(EntryPoint)
    for contract_name in (
        "EntryPoint",
        "SelfDestructor",
        "TestToken",
        "TestCounter",
    ):
        contract = account.deploy(getattr(brownie, contract_name))
        data[contract_name] = contract.address

    for paymaster_type in (
        "AcceptAll" "BALANCE",
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
        contract_name = f"TestPaymaster{paymaster_type}"
        contract = account.deploy(
            getattr(brownie, contract_name), entry_point.address
        )
        entry_point.depositTo(
            contract.address, {"from": account, "value": paymaster_deposit}
        )
        data[contract_name] = contract.address

    simple_account_factory = account.deploy(
        SimpleAccountFactory, entry_point.address
    )
    data["SimpleAccountFactory"] = simple_account_factory.address

    utils.deployments.save(data, brownie.network.show_active())
