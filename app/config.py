from pydantic import BaseSettings, HttpUrl


class Settings(BaseSettings):
    rpc_server: HttpUrl = "https://goerli.blockpi.network/v1/rpc/public"
    supported_entry_points: list = [
        "0xE40FdeB78BD64E7ab4BB12FA8C4046c85642eD6f",
    ]
    chain_id: int = 5
    expires_soon_interval: int = 10
    last_user_ops_count: int = 100
    environment: str = "PRODUCT"
    db_url_base = "postgresql+asyncpg://localhost"
    app_db_name = "mempool"
    test_db_name = "mempool_test"


settings = Settings()
