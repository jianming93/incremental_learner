from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import yaml

with open('config.yaml') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

SQLALCHEMY_USERNAME = config['database']['username']
SQLALCHEMY_PASSWORD = config['database']['password']
SQLALCHEMY_HOST = config['database']['host']
SQLALCHEMY_DATABASE_NAME = config['database']['database_name']
# SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
# SQLALCHEMT_USERNAME = 
SQLALCHEMY_DATABASE_URL = "postgresql://" + SQLALCHEMY_USERNAME + ":" + SQLALCHEMY_PASSWORD + "@" + SQLALCHEMY_HOST + "/" + SQLALCHEMY_DATABASE_NAME

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()