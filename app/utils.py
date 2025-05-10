import redis
from datetime import timedelta

REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

def save_to_cache(short_code: str, original_url: str, days: int = 30):
    expiration = timedelta(days=days)
    redis_client.setex(short_code, expiration, original_url)

def get_from_cache(short_code: str) -> str:
    return redis_client.get(short_code)