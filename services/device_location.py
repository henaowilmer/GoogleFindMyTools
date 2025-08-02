from typing import Dict, Any
from NovaApi.ExecuteAction.LocateTracker import location_request, decrypt_locations
from datetime import datetime
import pytz


def get_device_location(device_id: str) -> Dict[str, Any]:
    """
    Devuelve la ubicación desencriptada del dispositivo.
    """
    import asyncio
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    from Auth.fcm_receiver import FcmReceiver
    from NovaApi.scopes import NOVA_ACTION_API_SCOPE
    from NovaApi.nova_request import nova_request
    from ProtoDecoders.decoder import parse_device_update_protobuf
    from NovaApi.ExecuteAction.LocateTracker.decrypt_locations import decrypt_location_response_locations

    result = None
    request_uuid = location_request.generate_random_uuid()

    def handle_location_response(response):
        nonlocal result
        device_update = parse_device_update_protobuf(response)
        if device_update.fcmMetadata.requestUuid == request_uuid:
            result = device_update

    fcm_token = FcmReceiver().register_for_location_updates(handle_location_response)
    hex_payload = location_request.create_location_request(
        device_id, fcm_token, request_uuid)
    nova_request(NOVA_ACTION_API_SCOPE, hex_payload)

    while result is None:
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.1))

    device_registration = result.deviceMetadata.information.deviceRegistration
    identity_key = decrypt_locations.retrieve_identity_key(device_registration)
    locations_proto = result.deviceMetadata.information.locationInformation.reports.recentLocationAndNetworkLocations
    is_mcu = decrypt_locations.is_mcu_tracker(device_registration)
    recent_location = locations_proto.recentLocation
    recent_location_time = locations_proto.recentLocationTimestamp
    network_locations = list(locations_proto.networkLocations)
    network_locations_time = list(locations_proto.networkLocationTimestamps)
    if locations_proto.HasField("recentLocation"):
        network_locations.append(recent_location)
        network_locations_time.append(recent_location_time)
    location_time_array = []
    for loc, time_obj in zip(network_locations, network_locations_time):
        if loc.status == decrypt_locations.Common_pb2.Status.SEMANTIC:
            location_time_array.append({
                "type": "semantic",
                "name": loc.semanticLocation.locationName,
                "time": datetime.fromtimestamp(int(time_obj.seconds)).strftime('%Y-%m-%d %H:%M:%S'),
                "status": int(loc.status),
                "is_own_report": True,
                "accuracy": 0
            })
        else:
            encrypted_location = loc.geoLocation.encryptedReport.encryptedLocation
            public_key_random = loc.geoLocation.encryptedReport.publicKeyRandom
            if public_key_random == b"":  # Own Report
                import hashlib
                identity_key_hash = hashlib.sha256(identity_key).digest()
                decrypted_location = decrypt_locations.decrypt_aes_gcm(
                    identity_key_hash, encrypted_location)
            else:
                time_offset = 0 if is_mcu else loc.geoLocation.deviceTimeOffset
                decrypted_location = decrypt_locations.decrypt(
                    identity_key, encrypted_location, public_key_random, time_offset)
            from ProtoDecoders import DeviceUpdate_pb2
            proto_loc = DeviceUpdate_pb2.Location()
            proto_loc.ParseFromString(decrypted_location)
            latitude = proto_loc.latitude / 1e7
            longitude = proto_loc.longitude / 1e7
            altitude = proto_loc.altitude
            location_time_array.append({
                "type": "geo",
                "latitude": latitude,
                "longitude": longitude,
                "altitude": altitude,
                "google_maps_link": decrypt_locations.create_google_maps_link(latitude, longitude),
                "time": datetime.fromtimestamp(int(time_obj.seconds)).strftime('%Y-%m-%d %H:%M:%S'),
                "status": int(loc.status),
                "is_own_report": loc.geoLocation.encryptedReport.isOwnReport,
                "accuracy": loc.geoLocation.accuracy
            })
    if not location_time_array:
        raise Exception("No locations found.")
    # Guardar la última ubicación
    save_device_location(device_id, location_time_array)
    return {"locations": location_time_array}


def save_device_location(device_id: str, location_time_array: list):
    """
    Guarda la última ubicación del dispositivo en la base de datos.
    Si la tabla no existe, la crea automáticamente.
    También valida geofences si existen.
    """
    from db import SessionLocal, Device, TagLocation, get_engine, create_tables
    from services.geofence_service import GeofenceService

    session = SessionLocal()
    try:
        # Verificar y crear la tabla si no existe
        engine = get_engine()
        create_tables(engine)
        # Buscar el tag_device_id usando el canonic_id
        device = session.query(Device).filter_by(canonic_id=device_id).first()
        if device and location_time_array:
            geo_locs = [
                loc for loc in location_time_array if loc["type"] == "geo"]

            if not geo_locs:
                loc_to_save = location_time_array[-1]
            else:
                geo_locs_sorted = sorted(
                    geo_locs,
                    key=lambda x: (
                        x.get("accuracy", float('inf')),
                        -datetime.strptime(x["time"],
                                           '%Y-%m-%d %H:%M:%S').timestamp()
                    )
                )
                loc_to_save = geo_locs_sorted[0]

            latitude = loc_to_save.get("latitude")
            longitude = loc_to_save.get("longitude")
            timestamp = datetime.strptime(
                loc_to_save["time"], '%Y-%m-%d %H:%M:%S')
            bogota_tz = pytz.timezone("America/Bogota")
            timestamp = bogota_tz.localize(timestamp).replace(tzinfo=None)
            now_naive = datetime.now(bogota_tz).replace(tzinfo=None)
            tag_location = TagLocation(
                tag_device_id=device.id,
                latitude=latitude,
                longitude=longitude,
                timestamp=timestamp,
                created_at=now_naive
            )
            session.add(tag_location)
            session.commit()

            # Validate geofences if coordinates are available
            if latitude is not None and longitude is not None:
                geofence_service = GeofenceService()
                geofence_service.get_geofences(
                    device.id, latitude, longitude, timestamp)

    except Exception as e:
        session.rollback()
        print(f"Error guardando ubicación: {e}")
    finally:
        session.close()
