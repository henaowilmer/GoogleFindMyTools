from fastapi import FastAPI
from app.api.endpoints.devices import router as devices_router
from app.core.scheduler import start_scheduler, shutdown_scheduler

app = FastAPI()

app.include_router(devices_router)


@app.on_event("startup")
async def startup_event():
    start_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    shutdown_scheduler()
