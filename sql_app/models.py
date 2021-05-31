import datetime
from sqlalchemy import Boolean, Column, ForeignKey, Integer, Float, String, DateTime, LargeBinary, ARRAY
from sqlalchemy.orm import relationship

from .database import Base

class ShellFamily(Base):
    __tablename__ = "shell_family"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    shell_family_id = Column(String, unique=True, index=True)
    feature_extractor_model = Column(String)
    instances = Column(Integer)
    mapping = Column(ARRAY(String))
    global_mean = Column(LargeBinary)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class Shell(Base):
    __tablename__ = "shell"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    shell_family_id = Column(String, index=True)
    shell_id = Column(String, index=True)
    shell_mean = Column(LargeBinary)
    num_instances = Column(Integer)
    noise_mean = Column(Float)
    noise_std = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class ShellImages(Base):
    __tablename__ = "shell_images"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    shell_family_id = Column(String)
    shell_id = Column(String)
    image_path = Column(String)
    image_features = Column(LargeBinary)
    assigned_at = Column(DateTime, default=datetime.datetime.utcnow)

class Images(Base):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    image_class = Column(String)
    image_path = Column(String)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
