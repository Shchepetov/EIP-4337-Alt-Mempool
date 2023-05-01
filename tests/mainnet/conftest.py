import brownie
import pytest
import pytest_asyncio
from brownie import accounts, network
from brownie.network.account import Account

import app.constants as constants
import utils.deployments
from tests.utils.common_classes import Contracts, SendRequest


@pytest.fixture(scope="session", autouse=True)
def switch_to_mainnet():
    network.disconnect()
    network.connect(constants.MAINNET_NAME)
    yield
    network.disconnect()


@pytest_asyncio.fixture(scope="session")
def test_contracts() -> Contracts:
    instance = Contracts()
    deployments_data = utils.deployments.load(network.show_active())
    for contract_name, address in deployments_data.items():
        contract = getattr(brownie, contract_name)
        setattr(
            instance,
            utils.deployments.camel_to_snake(contract_name),
            contract.at(address),
        )

    return instance


@pytest.fixture(scope="function")
def send_request(test_contracts, test_account):
    return SendRequest(test_contracts, test_account, 1)


@pytest.fixture(scope="function")
def send_request_with_paymaster_from_network_using_opcode(
    test_contracts, test_account, send_request
):
    def f(opcode: str, target: brownie.Contract = None, payload=""):
        test_paymaster_accept_all = (
            getattr(test_contracts, f"test_paymaster_{opcode}"),
        )
        send_request.entry_point = test_contracts.entry_point.address
        send_request.user_op.paymaster_and_data = (
            (test_paymaster_accept_all.address + target.address[2:] + payload)
            if target
            else test_paymaster_accept_all.address
        )

        send_request.user_op.sign(test_account, test_contracts.entry_point)

        return send_request

    return f