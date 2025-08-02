from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.device_list import get_devices
import logging
import asyncio
import concurrent.futures

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

# Crear un ThreadPoolExecutor reutilizable
executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)


async def scheduled_get_devices():
    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(executor, get_devices)
        logger.info("Tarea programada get_devices completada exitosamente")
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
