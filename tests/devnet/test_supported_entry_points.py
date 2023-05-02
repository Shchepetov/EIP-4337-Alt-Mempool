import pytest

import db.service


@pytest.mark.asyncio
async def test_returns_supported_entry_points(client, test_contracts):
    entry_points = await client.supported_entry_points()
    assert len(entry_points) == 1
    assert entry_points[0] == test_contracts.entry_point.address


@pytest.mark.asyncio
async def test_adds_entry_point(client, session, test_contracts, test_account):
    await db.service.update_entry_point(
        session, test_account.address, is_supported=True
    )
    await session.commit()

    entry_points = await client.supported_entry_points()
    assert len(entry_points) == 2
    assert entry_points == [
        test_contracts.entry_point.address,
        test_account.address,
    ]


@pytest.mark.asyncio
async def test_deletes_entry_point(client, session, test_contracts):
    await db.service.update_entry_point(
        session, test_contracts.entry_point.address, is_supported=False
    )
    await session.commit()

    entry_points = await client.supported_entry_points()
    assert not len(entry_points)


@pytest.mark.asyncio
async def test_not_adds_entry_point_to_the_list_twice(
    client, session, test_contracts
):
    await db.service.update_entry_point(
        session, test_contracts.entry_point.address, True
    )
    await session.commit()

    entry_points = await client.supported_entry_points()
    assert len(entry_points) == 1
    assert entry_points[0] == test_contracts.entry_point.address
