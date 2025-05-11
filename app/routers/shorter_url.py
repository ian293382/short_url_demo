import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, status, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from ..utils import get_redis_client
from ..schemas import ShortURLRequest, ShortURLResponse
from redis.asyncio import RedisError

router = APIRouter(tags=["shorter_url"])


# 短網址服務設定
EXPIRATION_SECOND = 600  # 預設過期時間
RATE_LIMIT = 100  # 預設速率限制


async def enforce_rate_limit(
    redis_client, client_ip: str, limit: int = 10, window: int = 60
) -> None:
    rate_limit_key = f"rate_limit:{client_ip}"
    current_count = await redis_client.get(rate_limit_key)

    # limit access to 10 requests per minute
    if current_count is None:
        await redis_client.setex(rate_limit_key, window, 1)
    elif int(current_count) >= limit:
        raise HTTPException(
            status_code=429, detail="Too many requests.Please try again later."
        )
    else:
        await redis_client.incr(rate_limit_key)


@router.post(
    "/api/shorten",
    summary="Create a Short URL",
    response_description="Generate a short URL with expiration date",
    status_code=status.HTTP_201_CREATED,
    response_model=ShortURLResponse,
)
async def create_short_url(request: ShortURLRequest) -> ShortURLResponse:
    try:
        short_id = uuid.uuid4().hex[:8]
        short_url = f"http://localhost:8000/{short_id}"
        expiration_date = datetime.now() + timedelta(days=30) 
        redis_client = await get_redis_client()
        # save DB
        await redis_client.setex(
            short_id, 60 * 60 * 24 * 30,
            request.original_url
        )
        
        return {
            "short_url": short_url,
            "expiration_date": expiration_date,
            "success": True,
            "reason": None,
        }
    
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
        
    except RedisError as re:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis error: {str(re)}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.get(
    "/{short_id}",
    summary="Redirect to Original URL",
    response_description="Redirect to the original URL",
    response_class=HTMLResponse,
)
async def redirect_to_original(short_id: str, request: Request):
    try:
        redis_client = await get_redis_client()
        original_url = await redis_client.get(short_id)

        if original_url is None:
            return HTTPException(status_code=404, detail="Short URL not found")

        # 返回跳轉頁面
        return RedirectResponse(url=original_url)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error redirecting to original URL: {str(e)}"
        )
