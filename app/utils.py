import configparser
import os
from aioredis import from_url, Redis

# Config setting
CONFIG_FILE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "app/config.ini")
)
config = configparser.ConfigParser()
config.read(CONFIG_FILE_PATH)

# Redis settings
REDIS_HOST = config["redis"]["host"]
REDIS_PORT = int(config["redis"]["port"])
REDIS_DB = int(config["redis"]["db"])
REDIS_ENCODING = config["redis"]["encoding"]
REDIS_DECODE_RESPONSES = config.getboolean("redis", "decode_responses")

# Connect to Redis Pool
redis_pool = None


async def get_redis_client() -> Redis:
    global redis_pool
    if redis_pool is None:
        url = f"redis://{REDIS_HOST}:{REDIS_PORT}"
        redis_pool = await from_url(
            url,
            db=REDIS_DB,
            encoding=REDIS_ENCODING,
            decode_responses=REDIS_DECODE_RESPONSES,
            max_connections=3,
            socket_timeout=5,
            retry_on_timeout=True
        )
    return redis_pool
