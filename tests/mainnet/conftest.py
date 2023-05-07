import brownie
import pytest
import pytest_asyncio
import web3
from brownie import network

import app.constants as constants
import utils.deployments
from tests.utils.common_classes import TestContracts


@pytest.fixture(scope="session", autouse=True)
def switch_to_mainnet():
    network.disconnect()
    network.connect(constants.MAINNET_NAME)
    yield


@pytest_asyncio.fixture(scope="session")
def contracts() -> TestContracts:
    instance = TestContracts()
    deployments_data = utils.deployments.load(network.show_active())
    for contract_name, address in deployments_data.items():
        contract = getattr(brownie, contract_name)
        setattr(
            instance,
            utils.deployments.camel_to_snake(contract_name),
            contract.at(address),
        )

    return instance


@pytest_asyncio.fixture(scope="session")
def signer() -> web3.Account:
    account = web3.Account.create()
    yield account


@pytest.fixture(scope="function")
def send_request_with_paymaster_from_network_using_opcode(
    contracts, signer, send_request
):
    def f(opcode: str, target: brownie.Contract = None, payload=""):
        test_paymaster = getattr(contracts, f"test_paymaster_{opcode.lower()}")
        send_request.entry_point = contracts.entry_point.address
        send_request.user_op.paymaster_and_data = (
            test_paymaster.address + target.address[2:] + payload
            if target
            else test_paymaster.address
        )

        send_request.user_op.sign(signer, contracts.entry_point)

        return send_request

    return f
