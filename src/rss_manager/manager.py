import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import aiohttp
import asyncio
from feedparser import parse
from models import Post, RSS_feed
from sqlalchemy import select
from src.storages.postgress.setup import async_session_factory

import logging
from config.logger_settings import setup_logging

from datetime import datetime, timedelta
DATE_FORMAT = '%a, %d %b %Y %H:%M:%S %z'
setup_logging()

async def is_valid_rss_feed(url: str) -> bool:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, allow_redirects=True, timeout=5) as response:
                logging.debug(f'Response status for {url}: {response.status}')
                if response.status != 200:
                    return False

                content_type = response.headers.get('Content-Type', '')
                logging.debug(f'Content type for {url}: {content_type}')
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
    except Exception as exception:
        logging.error(f'Error while checking RSS feed {url}: {exception}')
        return False

class RSS_manager:
    def __init__(self):
        self.session = async_session_factory()
        logging.debug(f'Session created: {self.session}')

    async def add_feed(self, feed_url: str) -> None:
        async with self.session.begin():
            result = await self.session.execute(select(RSS_feed).filter_by(url=feed_url))
            feed = result.scalar_one_or_none()
            if not feed and await is_valid_rss_feed(feed_url):
                feed = RSS_feed(url=feed_url)
                self.session.add(feed)
                await self.session.commit()
                logging.info(f'Added feed {feed_url} to the database')

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
            logging.error(f'Failed to fetch feed {feed_url}')
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
                        logging.debug(f'Failed to parse date {entry.published}')
                        pub_date = datetime.now().replace(tzinfo=None)

                    if pub_date >= datetime.now().replace(tzinfo=None) - timedelta(days=7):
                        post = Post(
                            title=entry.title,
                            link=entry.link,
                            summary=entry.summary,
                            pub_date=pub_date,
                            feed=feed
                        )
                        self.session.add(post)
                        await self.session.commit()
                        logging.info(f'Added post "{post.title}" (by {entry.published}) to the database')
                    else:
                        logging.debug(f'Post "{entry.title}" (by {entry.published}) is too old')

    async def check_all_feeds(self) -> None:
        async with self.session.begin():
            result = await self.session.execute(select(RSS_feed))
            feeds = result.scalars().all()

        for feed in feeds:
            await self.process_feed(feed.url)

if __name__ == '__main__':
    manager = RSS_manager()
    print(asyncio.run(is_valid_rss_feed('https://machinelearningmastery.com/blog/feed/')))