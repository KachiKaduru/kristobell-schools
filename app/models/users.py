from datetime import datetime, timezone
from sqlalchemy import Integer, Column
from sqlalchemy.types import String, Boolean, DateTime

from app.core.database import Base


class Users(Base):
    __tablename__ = "users"

    id = Column[int](Integer, primary_key=True, index=True)
    email = Column[str](String, unique=True, index=True, nullable=True)
    hashed_password = Column[str](String, nullable=False)
    role = Column[str](String, default="admin")

    created_at = Column[datetime](
        DateTime(timezone=False), default=datetime.now(timezone.utc)
    )
    updated_at = Column[datetime](
        DateTime(timezone=False), default=datetime.now(timezone.utc)
    )
