import time

import pytest

import utils.web3


@pytest.mark.asyncio
async def test_estimates_user_op(client, contracts, send_request):
    user_op_hash = await client.send_user_op(send_request.json())
    user_op = await client.get_user_op(user_op_hash)
    call_gas_limit = utils.web3.estimate_gas(
        from_=contracts.entry_point.address,
        to=send_request.user_op.sender,
        data=send_request.user_op.call_data,
    )
    pre_verification_gas = send_request.user_op.get_calldata_gas()

    user_op_gas_estimation = await client.estimate_user_op(send_request.json())
    assert (
        user_op_gas_estimation["pre_verification_gas"] == pre_verification_gas
    )
    assert user_op_gas_estimation["verification_gas"] == int(
        user_op["pre_op_gas"], 16
    )
    assert user_op_gas_estimation["call_gas_limit"] == call_gas_limit


@pytest.mark.asyncio
async def test_estimates_user_op_without_gas_fields(
    client, send_request, send_request2
):
    del send_request.user_op.call_gas_limit
    del send_request.user_op.verification_gas_limit
    del send_request.user_op.pre_verification_gas
    del send_request.user_op.max_fee_per_gas
    del send_request.user_op.paymaster_and_data

    await client.estimate_user_op(send_request.json())


@pytest.mark.asyncio
async def test_estimates_expired_user_op(
    client, send_request_with_expire_paymaster
):
    now = int(time.time())
    send_request = send_request_with_expire_paymaster(now - 700, now - 100)
    await client.estimate_user_op(send_request.json())


@pytest.mark.asyncio
async def test_not_estimates_user_op_failing_simulation(client, send_request):
    send_request.user_op.signature = send_request.user_op.signature[:-3] + "123"
    await client.estimate_user_op(
        send_request.json(),
        expected_error_message="The simulation of the UserOp has failed with an"
        " error",
    )
