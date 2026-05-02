from fastapi import FastAPI
from app.core.config import settings
from app.api.webhook import router as webhook_router

app = FastAPI(title=settings.PROJECT_NAME)

# Register webhook router
app.include_router(webhook_router, prefix="/api/v1")

@app.get("/")
async def health_check():
    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "message": "Enterprise API is running....."
    }