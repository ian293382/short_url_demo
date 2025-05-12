import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, status, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from redis.asyncio import RedisError
from ..rate_limiter import enforce_rate_limit
from ..utils import get_redis_client
from ..schemas import ShortURLRequest, ShortURLResponse


router = APIRouter(tags=["shorter_url"])


# 短網址服務設定
EXPIRATION_SECOND = 600  # 預設過期時間
RATE_LIMIT = 100  # 預設速率限制


def handle_error(exception: Exception):
    if isinstance(exception, ValueError):
        raise HTTPException(status_code=400, detail=str(exception))
    elif isinstance(exception, RedisError):
        raise HTTPException(status_code=503, detail="Redis server unavailable")
    else:
        raise HTTPException(status_code=500, detail="Unexpected server error")



@router.post(
    "/api/shorten",
    summary="Create a Short URL",
    response_description="Generate a short URL with expiration date",
    status_code=status.HTTP_201_CREATED,
    response_model=ShortURLResponse,
)
async def create_short_url(request: Request, body: ShortURLRequest) -> ShortURLResponse:
    await enforce_rate_limit(request)
    try:
        short_id = uuid.uuid4().hex[:8]
        short_url = f"http://localhost:8000/{short_id}"
        expiration_date = datetime.now() + timedelta(days=30) 
        redis_client = await get_redis_client()
        # save DB
        await redis_client.setex(
            short_id, 60 * 60 * 24 * 30,
            body.original_url
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
