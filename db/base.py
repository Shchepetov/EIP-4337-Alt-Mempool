from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

DB_URL = f"{settings.get_db_url()}/{settings.app_db_name if settings.environment == 'APP' else settings.test_db_name}"
engine = create_async_engine(DB_URL)

Base = declarative_base()

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
