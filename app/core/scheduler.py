from app import shared_executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services import device_list
from app.shared_executor import shared_executor
import logging
import asyncio

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def scheduled_get_devices():
    def blocking_list_lookup():
        return device_list.get_devices()
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(shared_executor, blocking_list_lookup)
        return result
    except Exception as e:
        logger.error(f"Error en tarea programada get_devices: {e}")


def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(
            scheduled_get_devices,
            'interval',
            minutes=10,
            id='get_devices_job',
            replace_existing=True
        )
        scheduler.start()
        logger.info(
            "Scheduler started with job 'get_devices_job' every 10 minutes")


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shut down successfully")
