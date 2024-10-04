from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from manager import RSS_manager, is_valid_rss_feed
import asyncio
import uvicorn
from contextlib import asynccontextmanager

manager = RSS_manager()

async def regular_check():
    """
    Infinite loop checking all feeds for new posts.

    This function is meant to be run as an asyncio task.
    It will sleep for 100 seconds between each check.
    """
    while True:
        await manager.check_all_feeds()
        await asyncio.sleep(30)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(regular_check())
    yield
    task.cancel()
    await task

app = FastAPI(lifespan=lifespan)

class InvalidRSSFeed(Exception):
    def __init__(self):
        super().__init__('Invalid RSS feed')

@app.get('/')
async def root():
    return JSONResponse(content={'message': "It's an API for working with RSS feeds. Here you can subscribe to new feeds and get new posts."},
                        status_code=200)

@app.post('/add_feed')
async def add_feed(feed_url: str = Query(...)):
    if not await is_valid_rss_feed(feed_url):
        raise InvalidRSSFeed()
    await manager.add_feed(feed_url)
    await manager.process_feed(feed_url)
    return JSONResponse(content={'message': f'Feed {feed_url} added'}, 
                        status_code=201)

@app.exception_handler(InvalidRSSFeed)
async def invalid_rss_feed(request, exc):
    return JSONResponse(
        status_code=400,
        content={'message': 'Invalid RSS feed. Looks like, it is imposible to parse it :-('}
    )

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)