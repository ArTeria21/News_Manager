import sys
import os
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.storages.postgress.setup import async_engine, async_session_factory, Base
from src.rss_manager.models import RSS_feed
import logging
from config.logger_settings import setup_logging

setup_logging()

async def drop_tables() -> None:
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        logging.info('Dropped all tables')

async def init_tables() -> None:
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logging.info('Created all tables')

async def insert_data(obj) -> None:
    async with async_session_factory() as session:
        session.add(obj)
        await session.commit()

async def main() -> None:
    await drop_tables()
    await init_tables()

if __name__ == '__main__':
    asyncio.run(main())