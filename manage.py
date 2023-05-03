import asyncio

import typer
import uvicorn

import db.service
import db.utils
from app.config import settings

cli = typer.Typer()


@cli.command()
def initialize_db():
    for db_name in (settings.app_db_name, settings.test_db_name):
        asyncio.run(db.utils.create_and_init(db_name))
        print(f"Database `{db_name}` initialized")


@cli.command()
async def update_bytecode(address: str, is_trusted: bool):
    session = await db.utils.get_session()
    await db.service.update_bytecode_from_address(
        session, address, is_trusted=is_trusted
    )
    await session.commit()


@cli.command()
async def update_entry_point(address: str, is_supported: bool):
    session = await db.utils.get_session()
    await db.service.update_entry_point(
        session, address, is_supported=is_supported
    )
    await session.commit()


@cli.command()
def runserver(workers: int = 8):
    uvicorn.run("app.main:app", host="0.0.0.0", port=8545, workers=workers)


if __name__ == "__main__":
    cli()