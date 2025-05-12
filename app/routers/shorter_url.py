import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, status, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from typing import Optional
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


async def get_original_url(short_id: str) -> Optional[str]:
    try:
        redis_client = await get_redis_client()
        
        # 先嘗試用 short_id 查找對應的原始 URL
        original_url = await redis_client.get(short_id)
        
        # 如果沒有找到，返回 None
        if original_url is None:
            raise HTTPException(status_code=404, detail="Short URL not found")
        
        return original_url
    
    except RedisError as re:
        raise HTTPException(
            status_code=503,
            detail=f"Redis server unavailable: {str(re)}"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


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
        redis_client = await get_redis_client()
        original_url = body.original_url
        
        # 檢查是否已有相同 URL
        existing_short_id = await redis_client.get(f"url_mapping:{original_url}")
        
        if existing_short_id:
            # 刷新過期時間
            await redis_client.expire(existing_short_id, EXPIRATION_SECOND)
            expiration_date = datetime.now() + timedelta(seconds=EXPIRATION_SECOND)
            short_url = f"http://localhost:8000/{existing_short_id}"
        else:
            # 產生新的短網址
            short_id = uuid.uuid4().hex[:8]
            short_url = f"http://localhost:8000/{short_id}"
            expiration_date = datetime.now() + timedelta(seconds=EXPIRATION_SECOND)
            
            # 儲存短網址和對應的原始 URL
            await redis_client.setex(short_id, EXPIRATION_SECOND, original_url)
            await redis_client.setex(f"url_mapping:{original_url}", EXPIRATION_SECOND, short_id)

        return {
            "short_url": short_url,
            "expiration_date": expiration_date,
            "success": True,
            "reason": None,
        }
    
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
