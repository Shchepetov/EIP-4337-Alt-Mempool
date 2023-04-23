from pydantic import BaseSettings


class Settings(BaseSettings):
    max_verification_gas_limit: int = 6_000_000
    last_user_ops_count: int = 100
    min_max_fee_per_gas: int = 1
    min_max_priority_fee_per_gas: int = 1
    user_op_lifetime: int = 1800
    environment: str = "PRODUCT"
    db_url_base = "postgresql+asyncpg://localhost"
    app_db_name = "mempool"
    test_db_name = "mempool_test"


settings = Settings()
