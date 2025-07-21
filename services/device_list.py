from typing import List, Dict
from NovaApi.ListDevices import nbe_list_devices
from device_db import upsert_devices
from ProtoDecoders import decoder


def get_devices() -> List[Dict]:
    """
    Lista los dispositivos disponibles y sus IDs canónicos.
    """
    result_hex = nbe_list_devices.request_device_list()
    device_list = decoder.parse_device_list_protobuf(result_hex)
    canonic_ids = decoder.get_canonic_ids(device_list)
    upsert_devices(canonic_ids)
    return [
        {"name": name, "id": canonic_id}
        for name, canonic_id in canonic_ids
    ]
