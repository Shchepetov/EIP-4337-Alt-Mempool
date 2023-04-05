import copy
import logging

import pytest
from httpx import AsyncClient

LOGGER = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_create_user_op(client: AsyncClient, test_request: dict):
    response = await client.post(
        "/api/eth_sendUserOperation", json=test_request
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_integer_fields_rejected(client: AsyncClient, test_request: dict):
    async def test_incorrect_entity(request_):
        response = await client.post(
            "/api/eth_sendUserOperation", json=request_
        )
        assert response.status_code == 422

    for field in test_request["user_op"].keys():
        request = copy.deepcopy(test_request)
        request["user_op"][field] = int(test_request["user_op"][field], 16)
        await test_incorrect_entity(request)

    request = copy.deepcopy(test_request)
    request["entry_point"] = int(test_request["entry_point"], 16)
    await test_incorrect_entity(request)


@pytest.mark.asyncio
async def test_non_hexadecimal_fields_rejected(
    client: AsyncClient, test_request: dict
):
    async def test_incorrect_entity(request_):
        response = await client.post(
            "/api/eth_sendUserOperation", json=request_
        )
        assert response.status_code == 422

    for field in test_request["user_op"].keys():
        request = copy.deepcopy(test_request)
        request["user_op"][field] = test_request["user_op"][field].replace(
            "0x", ""
        )
        await test_incorrect_entity(request)
        request["user_op"][field] = test_request["user_op"][field][:-1] + "g"
        await test_incorrect_entity(request)

    request = copy.deepcopy(test_request)
    request["entry_point"] = test_request["entry_point"].replace("0x", "")
    await test_incorrect_entity(request)
    request["entry_point"] = test_request["entry_point"][:-1] + "g"
    await test_incorrect_entity(request)


@pytest.mark.asyncio
async def test_address_0x0_accepted(client: AsyncClient, test_request: dict):
    test_request["user_op"]["sender"] = "0x0"
    response = await client.post(
        "/api/eth_sendUserOperation", json=test_request
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_address_less_than_20_bytes_rejected(
    client: AsyncClient, test_request: dict
):
    test_request["user_op"][
        "sender"
    ] = "0x4CDbDf63ae2215eDD6B673F9DABFf789A13D427"
    response = await client.post(
        "/api/eth_sendUserOperation", json=test_request
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_address_with_incorrect_checksum_rejected(
    client: AsyncClient, test_request: dict
):
    test_request["user_op"][
        "sender"
    ] = "4cDbDf63ae2215eDD6B673F9DABFf789A13D4270"
    response = await client.post(
        "/api/eth_sendUserOperation", json=test_request
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_values_larger_uint256_in_integer_fields_rejected(
    client: AsyncClient, test_request: dict
):
    for field in (
        "nonce",
        "call_gas_limit",
        "verification_gas_limit",
        "pre_verification_gas",
        "max_fee_per_gas",
        "max_priority_fee_per_gas",
    ):
        request = copy.deepcopy(test_request)
        request["user_op"][field] = hex(2**256)
        response = await client.post("/api/eth_sendUserOperation", json=request)
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_odd_hexadecimal_chars_in_byte_fields_rejected(
    client: AsyncClient, test_request: dict
):
    for field in (
        "init_code",
        "call_data",
        "paymaster_and_data",
        "signature",
    ):
        request = copy.deepcopy(test_request)
        request["user_op"][field] = test_request["user_op"][field] + "0"
        response = await client.post("/api/eth_sendUserOperation", json=request)
        assert response.status_code == 422
