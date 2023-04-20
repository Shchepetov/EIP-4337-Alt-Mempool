import asyncio

import typer

import db.service
import db.utils
from app.config import settings

cli = typer.Typer()


@cli.command()
def initialize():
    for db_name in (settings.app_db_name, settings.test_db_name):
        asyncio.run(db.utils.create_and_init(db_name))
        print(f"Database `{db_name}` initialized")


@cli.command()
async def trust_bytecode(address: str):
    session = await db.utils.get_session()
    await db.service.update_bytecode_from_address(
        session, address, is_trusted=True
    )
    await session.commit()


@cli.command()
async def ban_bytecode(address: str):
    session = await db.utils.get_session()
    await db.service.update_bytecode_from_address(
        session, address, is_trusted=False
    )
    await session.commit()


if __name__ == "__main__":
    cli()
