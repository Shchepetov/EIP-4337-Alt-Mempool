import asyncio
import typer
from app.config import settings
from db.utils import create_and_init


cli = typer.Typer()


@cli.command()
def initialize():
    for db_name in (settings.app_db_name, settings.test_db_name):
        asyncio.run(create_and_init(db_name))
        print(f"Database `{db_name}` initialized")


if __name__ == "__main__":
    cli()
