from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.device_list import get_devices

scheduler = AsyncIOScheduler()


def scheduled_get_devices():
    try:
        get_devices()
    except Exception as e:
        print(f"Error en tarea programada get_devices: {e}")


def start_scheduler():
    scheduler.add_job(scheduled_get_devices, 'interval', minutes=10,
                      id='get_devices_job', replace_existing=True)
    scheduler.start()
    print("Scheduler started with job 'get_devices_job' every 10 minutes.")


def shutdown_scheduler():
    scheduler.shutdown()
