import pytest_asyncio
from brownie import (
    TestAggregatedAccountFactory,
    TestExpirePaymaster,
    TestPaymasterAcceptAll,
    EntryPoint,
    SelfDestructor,
    SimpleAccountFactory,
    TestCounter,
    TestToken,
)
from brownie import accounts, chain

from tests.utils.common_classes import Contracts


@pytest_asyncio.fixture(scope="session")
def test_contracts() -> Contracts:
    deployer = accounts[0]

    instance = Contracts()
    instance.test_counter = deployer.deploy(TestCounter)
    instance.entry_point = deployer.deploy(EntryPoint)
    instance.self_destructor = deployer.deploy(SelfDestructor)
    instance.test_token = deployer.deploy(TestToken)
    instance.aggregator = instance.entry_point

    instance.aggregated_account_factory = deployer.deploy(
        TestAggregatedAccountFactory,
        instance.entry_point.address,
        instance.aggregator.address,
    )
    instance.simple_account_factory = deployer.deploy(
        SimpleAccountFactory, instance.entry_point.address
    )

    instance.test_expire_paymaster = deployer.deploy(
        TestExpirePaymaster, instance.entry_point.address
    )
    instance.test_paymaster_accept_all = deployer.deploy(
        TestPaymasterAcceptAll, instance.entry_point.address
    )

    for address in (
        instance.test_expire_paymaster.address,
        instance.test_paymaster_accept_all.address,
    ):
        instance.entry_point.depositTo(address, {"value": "10 ether"})

    chain.snapshot()

    return instance


@pytest_asyncio.fixture(autouse=True)
def revert_chain(test_contracts):
    yield
    chain.revert()
