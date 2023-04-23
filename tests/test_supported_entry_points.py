import pytest
from brownie import accounts

import db.service


@pytest.mark.asyncio
async def test_returns_supported_entry_points(client, contracts):
    entry_points = await client.supported_entry_points()
    assert len(entry_points) == 1
    assert entry_points[0] == contracts.entry_point.address


@pytest.mark.asyncio
async def test_adds_entry_point(client, session, contracts):
    await db.service.update_entry_point(
        session, accounts[0].address, is_supported=True
    )
    await session.commit()

    entry_points = await client.supported_entry_points()
    assert len(entry_points) == 2
    assert entry_points == [contracts.entry_point.address, accounts[0].address]


@pytest.mark.asyncio
async def test_deletes_entry_point(client, session, contracts):
    await db.service.update_entry_point(
        session, contracts.entry_point.address, is_supported=False
    )
    await session.commit()

    entry_points = await client.supported_entry_points()
    assert not len(entry_points)


@pytest.mark.asyncio
async def test_not_adds_entry_point_to_the_list_twice(
    client, session, contracts
):
    await db.service.update_entry_point(
        session, contracts.entry_point.address, True
    )
    await session.commit()

    entry_points = await client.supported_entry_points()
    assert len(entry_points) == 1
    assert entry_points[0] == contracts.entry_point.address
