from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
import asyncio
import concurrent.futures
from services import device_list, device_location, device_ring

app = FastAPI()


@app.get("/devices", response_model=List[Dict])
def list_devices():
    """
    Lista los dispositivos disponibles y sus IDs canónicos.
    """
    try:
        return device_list.get_devices()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/devices/{device_id}/location", response_model=Dict[str, Any])
async def get_device_location(device_id: str):
    """
    Devuelve la ubicación desencriptada del dispositivo.
    """
    def blocking_location_lookup(device_id):
        return device_location.get_device_location(device_id)
    try:
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = await loop.run_in_executor(pool, blocking_location_lookup, device_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/devices/{device_id}/ring")
async def ring_device(device_id: str):
    """
    Hace sonar el dispositivo especificado.
    """
    def blocking_ring(device_id):
        return device_ring.ring_device(device_id)
    try:
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = await loop.run_in_executor(pool, blocking_ring, device_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
