import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app, get_session
from db.base import Base, DATABASE_URL, init_models

TEST_DATABASE_URL = f"{DATABASE_URL}/test"


async def init_test_database():
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    return engine


test_engine = asyncio.run(init_test_database())

test_async_session = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False, future=True
)


async def override_get_session() -> AsyncSession:
    async with test_async_session() as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


@pytest.fixture(scope="module")
def test_client():
    with TestClient(app) as client:
        yield client


def test_create_user_op(test_client):
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

    response = test_client.post("/api/eth_sendUserOperation", json=data)
    assert response.status_code == 200
