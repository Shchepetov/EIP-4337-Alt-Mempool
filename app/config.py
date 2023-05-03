from pydantic import BaseSettings


class Settings(BaseSettings):
    rpc_endpoint_uri: str = ""
    max_verification_gas_limit: int = 6_000_000
    last_user_ops_count: int = 100
    min_max_fee_per_gas: int = 1
    min_max_priority_fee_per_gas: int = 1
    user_op_lifetime: int = 1800
    environment: str = "PRODUCT"
    db_host: str = "localhost"
    db_user: str = ""
    db_password: str = ""
    db_url_base = "postgresql+asyncpg"
    app_db_name = "app"
    test_db_name = "app_test"

    def get_db_url(self):
        return f"{self.db_url_base}://{self.db_user}:{self.db_password}@{self.db_host}"


settings = Settings()
