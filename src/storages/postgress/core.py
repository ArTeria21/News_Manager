import sys
import os
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.storages.postgress.setup import async_engine, async_session_factory, Base
from src.rss_manager.models import RSS_feed

async def drop_tables() -> None:
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

async def init_tables() -> None:
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def insert_data(obj) -> None:
    async with async_session_factory() as session:
        session.add(obj)
        await session.commit()

async def main() -> None:
    await drop_tables()
    await init_tables()

if __name__ == '__main__':
    asyncio.run(main())