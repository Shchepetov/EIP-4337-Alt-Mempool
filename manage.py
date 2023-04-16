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
async def update_bytecode(bytecode_hash: str, is_trusted: bool):
    session = await db.utils.get_session()
    await db.service.update_bytecode(session, bytecode_hash, is_trusted)
    await session.commit()


if __name__ == "__main__":
    cli()
