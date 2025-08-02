import json
import os
import requests
from datetime import datetime
from typing import List
from db import SessionLocal, Device, Geofence, EventAlert, User, FirebaseToken
from sqlalchemy import text
import firebase_admin
from firebase_admin import credentials, messaging


class GeofenceService:
    def __init__(self):
        self.session = SessionLocal()
        self.firebase_app = None

    def __del__(self):
        if hasattr(self, 'session'):
            self.session.close()

    def send_notification(self, device_id: int, name_event: str):
        """Send WhatsApp and Firebase notifications for geofence alerts"""
        try:
            device = self.session.query(Device).filter_by(id=device_id).first()
            if not device:
                return

            # Get users for WhatsApp notifications
            users = self.session.query(User).filter(
                User.id_company == device.company_id,
                User.whatsapp == True,
                User.status == True,
                text(
                    "tags::jsonb @> :device_id").params(device_id=f'[{device_id}]')
            ).all()

            # Send WhatsApp messages
            for user in users:
                if user.phone:
                    body_whatsapp = (
                        f"*¡Alerta de {name_event}!* \n\n"
                        f"*{user.name}*, le informamos que *{device.nickname}* "
                        f"ha presentado una alerta. Te recomendamos verificar la situación y "
                        f"tomar las medidas necesarias para garantizar la seguridad. \n"
                        f"Si consideras necesario tomar acciones, puedes revisar desde tu app.\n\n"
                        f"Isolutions Ingeniería está disponible para ayudarle."
                    )
                    try:
                        alert_host = os.getenv(
                            'IP_SERVICE_WHATSAPP', 'localhost')
                        alert_port = os.getenv('PORT_SERVICE_WHATSAPP', '3000')
                        alert_url = f'http://{alert_host}:{alert_port}/sendAlert'

                        print(f'Sending WhatsApp to: {alert_url}')
                        print(f'Phone: {user.phone}')

                        response = requests.post(alert_url, json={
                            'body': body_whatsapp,
                            'phone': user.phone
                        }, timeout=10)

                        print(f'Response status: {response.status_code}')
                        print(f'Response text: {response.text}')

                    except requests.exceptions.Timeout:
                        print(f'Timeout error connecting to WhatsApp service at {alert_url}')  # noqa 501
                    except requests.exceptions.ConnectionError:
                        print(f'Connection error to WhatsApp service at {alert_url}')  # noqa 501
                    except Exception as e:
                        print(f'Error sending WhatsApp: {e}')

            # Get Firebase tokens
            firebase_tokens = self.session.query(FirebaseToken).filter_by(
                id_company=device.company_id
            ).all()

            if firebase_tokens:
                tokens = [ft.token for ft in firebase_tokens]
                self._send_firebase_notification(
                    device, name_event, tokens, firebase_tokens)

        except Exception as e:
            print(f'Error sending notification: {e}')

    def _send_firebase_notification(self, device: Device, name_event: str, tokens: List[str], firebase_tokens: List[FirebaseToken]):
        """Send Firebase push notifications"""
        try:
            # Initialize Firebase if not already done
            if not self.firebase_app:
                # You'll need to add your Firebase service account file
                cred = credentials.Certificate('fcm.json')
                self.firebase_app = firebase_admin.initialize_app(cred)

            title = f"¡Alerta de {name_event}!"
            body = f"{device.nickname} ha presentado una alerta, te recomendamos verificar la situación."  # noqa 501

            message = messaging.MulticastMessage(
                tokens=tokens,
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data={
                    'title': title,
                    'body': body,
                    'click_action': 'https://gps.isolutions.website/#/admin/maps',
                    'icon': '/img/favicon.ico',
                    'image': '/img/logo_isolutions.png'
                },
                webpush=messaging.WebpushConfig(
                    fcm_options=messaging.WebpushFCMOptions(
                        link='https://gps.isolutions.website/#/admin/maps'
                    ),
                    headers={'Urgency': 'high'},
                    notification=messaging.WebpushNotification(
                        title=title,
                        body=body,
                        icon='/img/favicon.ico',
                        image='/img/logo_isolutions.png',
                        require_interaction=True,
                        badge='/img/favicon.ico'
                    )
                )
            )

            response = messaging.send_multicast(message)

            # Remove failed tokens
            if response.failure_count > 0:
                failed_tokens = []
                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        failed_tokens.append(firebase_tokens[idx])

                for failed_token in failed_tokens:
                    self.session.delete(failed_token)

                self.session.commit()

        except Exception as e:
            print(f'Error sending Firebase notification: {e}')

    def get_geofences(self, device_id: int, latitude: float, longitude: float, date_event: datetime):
        """Get geofences for a device and validate position"""
        try:
            geofences = self.session.query(Geofence).filter(
                Geofence.tag_id == device_id,
                Geofence.status == True
            ).all()

            if geofences and not (latitude is None or longitude is None):
                self.validate_position(
                    geofences, device_id, latitude, longitude, date_event)

        except Exception as e:
            print(f'Error getting geofences: {e}')

    def validate_position(self, geofences: List[Geofence], device_id: int, latitude: float, longitude: float, date_event: datetime):
        """Validate if device position is inside or outside geofences"""
        try:
            lat = latitude
            lng = longitude
            point_to_check = [lat, lng]

            for geofence in geofences:
                polygon_data = json.loads(geofence.polygon)
                polygon = []

                # Build polygon coordinates
                for coord in polygon_data:
                    polygon.append([coord['lat'], coord['lng']])

                # Point-in-polygon algorithm (ray casting)
                is_inside = self._point_in_polygon(point_to_check, polygon)

                if is_inside:
                    self._handle_inclusion_event(
                        device_id, latitude, longitude, date_event)
                    return

            # If not inside any geofence
            self._handle_exclusion_event(
                device_id, latitude, longitude, date_event)

        except Exception as e:
            print(f'Error validating position: {e}')

    def _point_in_polygon(self, point: List[float], polygon: List[List[float]]) -> bool:
        """Check if a point is inside a polygon using ray casting algorithm"""
        x, y = point
        n = len(polygon)
        inside = False

        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / \
                                (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    def _handle_inclusion_event(self, device_id: int, latitude: float, longitude: float, date_event: datetime):
        """Handle when device enters a geofence"""
        try:
            device = self.session.query(Device).filter_by(id=device_id).first()
            if not device:
                return

            if device.geofence_flag:
                device.geofence_flag = False
                self.session.commit()

                # Create event alert
                event_alert = EventAlert(
                    tag_id=device_id,
                    latitude=latitude,
                    longitude=longitude,
                    event='98',  # Inclusion event
                    date_event=date_event,
                    created_at=datetime.now()
                )
                self.session.add(event_alert)
                self.session.commit()

                name_event = 'Geocerca de Inclusión✅'
                self.send_notification(device_id, name_event)

        except Exception as e:
            print(f'Error handling inclusion event: {e}')
            self.session.rollback()

    def _handle_exclusion_event(self, device_id: int, latitude: float, longitude: float, date_event: datetime):
        """Handle when device exits a geofence"""
        try:
            device = self.session.query(Device).filter_by(id=device_id).first()
            if not device:
                return

            if not device.geofence_flag:
                device.geofence_flag = True
                self.session.commit()

                # Create event alert
                event_alert = EventAlert(
                    tag_id=device_id,
                    latitude=latitude,
                    longitude=longitude,
                    event='99',  # Exclusion event
                    date_event=date_event,
                    created_at=datetime.now()
                )
                self.session.add(event_alert)
                self.session.commit()

                name_event = 'Geocerca de Exclusión🚨'
                self.send_notification(device_id, name_event)

        except Exception as e:
            print(f'Error handling exclusion event: {e}')
            self.session.rollback()
