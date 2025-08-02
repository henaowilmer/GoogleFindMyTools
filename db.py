import os
from sqlalchemy import create_engine, Column, Integer, String, UniqueConstraint, DateTime, func, Float, ForeignKey, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()


class Device(Base):
    __tablename__ = 'tag_devices'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    canonic_id = Column(String, nullable=False, unique=True)
    nickname = Column(String, nullable=True)
    company_id = Column(Integer, ForeignKey(
        'companies.id_company'), nullable=True)
    svg = Column(String, nullable=True)
    svg_color = Column(String, nullable=True)
    geofence_flag = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False)

    __table_args__ = (
        UniqueConstraint('canonic_id', name='uix_tag_canonic_id'),
    )


class TagLocation(Base):
    __tablename__ = 'tag_locations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tag_device_id = Column(Integer, ForeignKey(
        'tag_devices.id'), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False)


class Geofence(Base):
    __tablename__ = 'geofences_tag'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    tag_id = Column(Integer, ForeignKey('tag_devices.id'), nullable=False)
    polygon = Column(Text, nullable=False)  # JSON string with coordinates
    status = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class EventAlert(Base):
    __tablename__ = 'events_alerts_tag'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tag_id = Column(Integer, ForeignKey('tag_devices.id'), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    # '98' for inclusion, '99' for exclusion
    event = Column(String, nullable=False)
    date_event = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False)


class Company(Base):
    __tablename__ = 'companies'
    id_company = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    id_company = Column(Integer, ForeignKey(
        'companies.id_company'), nullable=False)
    whatsapp = Column(Boolean, default=False, nullable=True)
    status = Column(Boolean, default=True, nullable=False)
    tags = Column(Text, nullable=False)  # JSON string with tag IDs
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class FirebaseToken(Base):
    __tablename__ = 'firebases'
    id_firebase = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String, nullable=False)
    id_company = Column(Integer, ForeignKey(
        'companies.id_company'), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


def get_db_url():
    host = os.environ.get('DB_HOST', 'localhost')
    port = os.environ.get('DB_PORT', '5432')
    user = os.environ.get('DB_USER', 'usuario')
    password = os.environ.get('DB_PASSWORD', 'contraseña')
    dbname = os.environ.get('DB_NAME', 'nombre_db')
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"


def get_engine(db_url=None):
    if db_url is None:
        db_url = get_db_url()
    return create_engine(db_url, echo=False)


def create_tables(engine):
    Base.metadata.create_all(engine)


SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=get_engine())
