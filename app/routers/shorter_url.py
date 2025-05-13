import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, status, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from typing import Optional
from redis.asyncio import RedisError
from ..rate_limiter import limit_user_requests
from ..utils import get_redis_client
from ..schemas import ShortURLRequest, ShortURLResponse


router = APIRouter(tags=["shorter_url"])


# 短網址服務設定
EXPIRATION_SECOND = 60*60*24*30  # 預設過期時間 30 天


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
    # 直接限速，不需要傳遞參數
    await limit_user_requests(request)

    try:
        redis_client = await get_redis_client()
        original_url = body.original_url
        
        # **檢查是否已存在短網址**
        existing_short_id = await redis_client.get(f"url_mapping:{original_url}")
        if existing_short_id:
            short_id = existing_short_id
        else:
            short_id = uuid.uuid4().hex[:8]
            # **建立雙向對應**
            await redis_client.setex(short_id, EXPIRATION_SECOND, original_url)
            await redis_client.setex(f"url_mapping:{original_url}", EXPIRATION_SECOND, short_id)

        # **always renew expiration**
        expiration_date = datetime.now() + timedelta(seconds=EXPIRATION_SECOND)
        await redis_client.expire(short_id, EXPIRATION_SECOND)

        short_url = f"{request.base_url}{short_id}"
        return {
            "short_url": short_url,
            "expiration_date": expiration_date,
            "success": True,
            "reason": None,
        }
    
    except Exception as e:
        return {
            "success": False,
            "reason": handle_error(e),
        }
    

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
            raise HTTPException(status_code=404, detail="Short URL not found")
        
        return RedirectResponse(url=original_url)
   
    except Exception as e:
        handle_error(e)