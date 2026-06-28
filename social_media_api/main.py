from fastapi import FastAPI, HTTPException
from fastapi.exception_handlers import http_exception_handler
from asgi_correlation_id import CorrelationIdMiddleware
import logging
from social_media_api.routers.post import router as post_router
from social_media_api.database import database
from social_media_api.logging_conf import configure_logging
import uvicorn
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    configure_logging()
    logger.info("Application startup complete.")
    yield
    await database.disconnect()

app = FastAPI(lifespan=lifespan)
app.add_middleware(CorrelationIdMiddleware)
app.include_router(post_router)

@app.exception_handler(HTTPException)
async def http_exception_handle_logging(request, exc):
    logger.error(f"HTTP exception occurred: {exc.status_code} - {exc.detail}")
    return await http_exception_handler(request, exc)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)