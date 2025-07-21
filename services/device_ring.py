from typing import Dict, Any


def ring_device(device_id: str) -> Dict[str, Any]:
    """
    Hace sonar el dispositivo especificado.
    """
    from Auth.fcm_receiver import FcmReceiver
    from NovaApi.ExecuteAction.PlaySound import start_sound_request
    from NovaApi.scopes import NOVA_ACTION_API_SCOPE
    from NovaApi.nova_request import nova_request

    fcm_token = FcmReceiver().register_for_location_updates(lambda x: None)
    hex_payload = start_sound_request.start_sound_request(device_id, fcm_token)
    nova_request(NOVA_ACTION_API_SCOPE, hex_payload)
    return {"status": "ring command sent"}
