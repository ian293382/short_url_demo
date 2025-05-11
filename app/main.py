import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from .routers import health_check, shorter_url

app = FastAPI()


# Allow CORS for all origins
origins = ['*']
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
