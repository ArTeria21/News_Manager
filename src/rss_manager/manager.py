import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import aiohttp
import asyncio
from feedparser import parse
from models import Post, RSS_feed
from sqlalchemy import select
from src.storages.postgress.setup import async_session_factory

from datetime import datetime
DATE_FORMAT = '%a, %d %b %Y %H:%M:%S %z'

async def is_valid_rss_feed(url: str) -> bool:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, allow_redirects=True, timeout=5) as response:
                if response.status != 200:
                    return False

                content_type = response.headers.get('Content-Type', '')
                if 'xml' not in content_type and 'rss' not in content_type and 'atom' not in content_type:
                    return False

                content = await response.text()
                feed = parse(content)
                
                if feed.bozo:
                    return False
                
                if feed.get('feed') and feed.get('entries'):
                    return True
                else:
                    return False
    except Exception as e:
        return False

class RSS_manager:
    def __init__(self):
        self.session = async_session_factory()

    async def add_feed(self, feed_url: str) -> None:
        async with self.session.begin():
            result = await self.session.execute(select(RSS_feed).filter_by(url=feed_url))
            feed = result.scalar_one_or_none()
            if not feed and await is_valid_rss_feed(feed_url):
                feed = RSS_feed(url=feed_url)
                self.session.add(feed)
                await self.session.commit()

    async def fetch_feed(self, feed_url: str) -> dict | None:
        async with aiohttp.request(url=feed_url, method='GET') as response:
            if response.status == 200:
                feed_data = parse(await response.text())
                return feed_data
            else:
                print(f"Ошибка загрузки канала {feed_url}: статус {response.status}")
                return None
            
    async def process_feed(self, feed_url: str) -> None:
        feed_data = await self.fetch_feed(feed_url)
        if feed_data is None:
            return
        
        async with self.session.begin():
            result = await self.session.execute(select(RSS_feed).filter_by(url=feed_url))
            feed = result.scalar_one_or_none()
            if not feed and await is_valid_rss_feed(feed_url):
                self.add_feed(feed_url)
        
        for entry in feed_data.entries:
            async with self.session.begin():
                result = await self.session.execute(select(Post).filter_by(link=entry.link))
                existing_post = result.scalar_one_or_none()
                if not existing_post:
                    try:
                        pub_date = datetime.strptime(entry.published, DATE_FORMAT).replace(tzinfo=None)
                    except:
                        pub_date = datetime.now().replace(tzinfo=None)

                    post = Post(
                        title=entry.title,
                        link=entry.link,
                        summary=entry.summary,
                        pub_date=pub_date,
                        feed=feed
                    )
                    self.session.add(post)
                    await self.session.commit()

    async def check_all_feeds(self) -> None:
        async with self.session.begin():
            result = await self.session.execute(select(RSS_feed))
            feeds = result.scalars().all()

        for feed in feeds:
            await self.process_feed(feed.url)

if __name__ == '__main__':
    manager = RSS_manager()
    print(asyncio.run(is_valid_rss_feed('https://machinelearningmastery.com/blog/feed/')))