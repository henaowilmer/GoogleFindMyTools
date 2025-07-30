import os
from sqlalchemy import create_engine, Column, Integer, String, UniqueConstraint, DateTime, func, Float, ForeignKey
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
    company_id = Column(Integer, nullable=True)
    svg = Column(String, nullable=True)
    svg_color = Column(String, nullable=True)
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
