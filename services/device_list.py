from typing import List, Dict
from NovaApi.ListDevices import nbe_list_devices
from device_db import upsert_devices
from services.device_location import get_device_location
from ProtoDecoders import decoder


def get_devices() -> List[Dict]:
    """
    -Lista los dispositivos disponibles y sus IDs canónicos
    -Obtener ubicación de cada dispositivo
    """
    result_hex = nbe_list_devices.request_device_list()
    device_list = decoder.parse_device_list_protobuf(result_hex)
    canonic_ids = decoder.get_canonic_ids(device_list)

    filtered_ids = [
        (name, canonic_id)
        for name, canonic_id in canonic_ids
        if "master" not in name.lower()
    ]

    upsert_devices(filtered_ids)

    devices = []
    for name, canonic_id in filtered_ids:
        try:
            location = get_device_location(canonic_id)
        except Exception as e:
            location = {"error": str(e)}
        devices.append({"name": name, "id": canonic_id, "location": location})
    print(f"Devices: {devices}")
    return devices
