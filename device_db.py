from db import Device, get_engine, create_tables, SessionLocal
from sqlalchemy.exc import IntegrityError

def upsert_devices(devices):
    """
    Inserta o actualiza la lista de dispositivos en la base de datos.
    devices: lista de tuplas (name, canonic_id)
    """
    engine = get_engine()
    create_tables(engine)
    session = SessionLocal()
    try:
        for name, canonic_id in devices:
            device = session.query(Device).filter_by(canonic_id=canonic_id).first()
            if device:
                device.name = name
            else:
                device = Device(name=name, canonic_id=canonic_id)
                session.add(device)
        session.commit()
    except IntegrityError:
        session.rollback()
        raise
    finally:
        session.close()
