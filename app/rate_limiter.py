import hashlib
from datetime import datetime, timedelta
from fastapi import Request, HTTPException
from .utils import get_redis_client

RATE_LIMIT = 4  # 每分鐘最多 4 次


async def limit_user_requests(request: Request) -> None:
    '''
    Ref: https://dev.to/dpills/how-to-rate-limit-fastapi-with-redis-1dhf

    step 1. Get user IP address
    step 2. Generate a unique key for this IP + current minute
    step 3. Increment the visit count for this key in Redis
    step 4. If it's the first visit, set a 1-minute expiration time
    step 5. If the count exceeds the limit, raise a 429 error
    '''
    redis_client = await get_redis_client()

    # **取得用戶 IP 地址**
    client_ip = request.client.host
    if not client_ip:
        raise HTTPException(status_code=400, detail="Invalid client IP")
    
    # **產生 Redis Key**（根據 client_ip 和當前分鐘）
    current_minute = datetime.now().strftime("%Y-%m-%dT%H:%M")
    key = f"rate_limit_{client_ip}_{current_minute}"
    
    current_count = await redis_client.incr(key)
    
    if current_count == 1:
        expire_at_timestamp = int((datetime.now() + timedelta(minutes=1)).timestamp())
        await redis_client.expireat(key, expire_at_timestamp)

    if current_count > RATE_LIMIT:
        retry_after = 60 - datetime.now().second
        raise HTTPException(
            status_code=429,
            detail="User Rate Limit Exceeded",
            headers={
                "Retry-After": str(retry_after),
                "X-Rate-Limit": str(RATE_LIMIT),
            },
        )