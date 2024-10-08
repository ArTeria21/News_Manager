from api import app
import logging
import uvicorn

if __name__ == '__main__':
    logging.info('Starting the server')
    uvicorn.run(app, host='0.0.0.0', port=8000)