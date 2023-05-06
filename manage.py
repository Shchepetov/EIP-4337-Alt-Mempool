import asyncio

import typer
import uvicorn

import db.service
import db.utils
from app.config import settings
from db.base import async_session

cli = typer.Typer()


@cli.command()
def initialize_db():
    for db_name in (settings.app_db_name, settings.test_db_name):
        asyncio.run(db.utils.create_and_init(db_name))
        print(f"Database `{db_name}` initialized")


@cli.command()
def runserver(workers: int = 8):
    uvicorn.run("app.main:app", host="0.0.0.0", port=8545, workers=workers)


@cli.command()
def update_bytecode_from_address(address: str, is_trusted: bool):
    asyncio.run(_update_bytecode_from_address(address, is_trusted))


@cli.command()
def update_entry_point(address: str, is_supported: bool):
    asyncio.run(_update_entry_point(address, is_supported))


async def _update_bytecode_from_address(address: str, is_trusted: bool):
    async with async_session() as session:
        await db.service.update_bytecode_from_address(
            session, address, is_trusted=is_trusted
        )
        await session.commit()


async def _update_entry_point(address: str, is_supported: bool):
    async with async_session() as session:
        await db.service.update_entry_point(
            session, address, is_supported=is_supported
        )
        await session.commit()


if __name__ == "__main__":
    cli()
