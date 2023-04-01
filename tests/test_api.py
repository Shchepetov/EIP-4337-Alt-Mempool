from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_send_user_operation():
    data = {
        "user_op": {
            "sender": "0x4CDbDf63ae2215eDD6B673F9DABFf789A13D4270",
            "nonce": "0x00000000001000000000001000000",
            "init_code": "0x000000000000000000000000000000000000000001",
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

    response = client.post("/api/eth_sendUserOperation", json=data)
    assert response.status_code == 200
    assert response.json()["name"] == data["name"]
    assert response.json()["description"] == data["description"]


def test_send_incorrect_sender():
    pass


def test_send_incorrect_nonce():
    pass


def test_send_incorrect_init_code():
    pass


def test_send_incorrect_call_data():
    pass


def test_send_incorrect_call_gas_limit():
    pass


def test_send_incorrect_verification_gas_limit():
    pass


def test_send_incorrect_pre_verification_gas():
    pass


def test_send_incorrect_max_fee_per_gas():
    pass


def test_send_incorrect_max_priority_fee_per_gas():
    pass


def test_send_incorrect_paymaster_and_data():
    pass


def test_send_incorrect_signature():
    pass


def test_send_incorrect_entry_point():
    pass
