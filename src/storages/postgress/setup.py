import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from config.db_settings import pg_settings
import asyncio

async_engine = create_async_engine(
    url=pg_settings.DB_URL,
    pool_size=10,
    max_overflow=20,
)

class Base(DeclarativeBase):
    pass

async_session_factory = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)