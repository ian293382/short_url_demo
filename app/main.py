import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from .routers import health_check, shorter_url

app = FastAPI()


app.include_router(health_check.router)
app.include_router(shorter_url.router)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Home Page
    Serves the main HTML page for URL shortening.
    """
    template_path = os.path.join(
        os.path.dirname(__file__), "template", "index.html"
    )
    return FileResponse(template_path)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
