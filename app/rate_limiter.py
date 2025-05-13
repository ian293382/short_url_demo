import hashlib
from datetime import datetime, timedelta
from fastapi import Request, HTTPException
from .utils import get_redis_client

RATE_LIMIT = 6  # 每分鐘最多 10 次


async def limit_user_requests(request: Request) -> None:
    '''
    Ref: https://dev.to/dpills/how-to-rate-limit-fastapi-with-redis-1dhf

    step 1. Get user info and process hash (secret protected), add datetime string append
    step 2. Generate redis key for user info and increment count
    step 3. On the first request, set expiration to "now + 1 minute"
    step 4. If the count > RATE_LIMIT, raise error
    '''
    redis_client = await get_redis_client()
    user_id = request.headers.get("x-user", "anonymous")
    username_hash = hashlib.sha256(user_id.encode("utf-8")).hexdigest()
    
    now = datetime.now()
    current_minute = now.strftime("%Y-%m-%dT%H:%M")
    
    # 產生 Redis Key
    redis_key = f"rate_limit_{username_hash}_{current_minute}"
    current_count = await redis_client.incr(redis_key)
    
    if current_count == 1:
        expire_at_timestamp = int((now + timedelta(minutes=1)).timestamp())
        await redis_client.expireat(redis_key, expire_at_timestamp)
    if current_count > RATE_LIMIT:
        retry_after = 60 - now.second
        raise HTTPException(
            status_code=429,
            detail="User Rate Limit Exceeded",
            headers={
                "Retry-After": str(retry_after),
                "X-Rate-Limit": str(RATE_LIMIT),
            },
        )
