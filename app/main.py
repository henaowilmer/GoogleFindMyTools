from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.api.endpoints.devices import router as devices_router
from app.core.scheduler import start_scheduler, shutdown_scheduler
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(devices_router)


@app.get("/health", status_code=200)
@app.head("/health", status_code=200)
def health_check():
    return {"status": "healthy"}


@app.get("/", status_code=200)
@app.head("/", status_code=200)
def root():
    return {"message": "GPS Tracker API is running"}


@app.on_event("startup")
def startup_event():
    start_scheduler()
    logger.info("Application startup")


@app.on_event("shutdown")
def shutdown_event():
    shutdown_scheduler()
    logger.info("Application shutdown")
