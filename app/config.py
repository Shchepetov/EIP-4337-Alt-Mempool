from typing import List

from pydantic import BaseSettings, HttpUrl


class Settings(BaseSettings):
    rpc_server: HttpUrl = "http://127.0.0.1:8545"
    supported_entry_points: List[str] = []
    expires_soon_interval: int = 10
    last_user_ops_count: int = 100
    environment: str = "PRODUCT"
    db_url_base = "postgresql+asyncpg://localhost"
    app_db_name = "mempool"
    test_db_name = "mempool_test"


settings = Settings()
