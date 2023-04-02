import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_user_op(client: AsyncClient):
    data = {
        "user_op": {
            "sender": "0x4CDbDf63ae2215eDD6B673F9DABFf789A13D4270",
            "nonce": "0x00000000001000000000001000000",
            "init_code": "0x000000000001",
            "call_data": "0x000000000001",
            "call_gas_limit": "0x000000000001",
            "verification_gas_limit": "0x000000000001",
            "pre_verification_gas": "0x000000000001",
            "max_fee_per_gas": "0x000000000001",
            "max_priority_fee_per_gas": "0x000000000001",
            "paymaster_and_data": "0x000000000001",
            "signature": "0x000000000001",
        },
        "entry_point": "0xE40FdeB78BD64E7ab4BB12FA8C4046c85642eD6f",
    }

    response = await client.post("/api/eth_sendUserOperation", json=data)
    assert response.status_code == 200
