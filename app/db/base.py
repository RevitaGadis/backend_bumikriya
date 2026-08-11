import uuid

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


def generate_uuid() -> str:
    return str(uuid.uuid4())
