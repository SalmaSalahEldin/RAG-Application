from .minirag_base import SQLAlchemyBase
from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship

class User(SQLAlchemyBase):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    user_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    projects = relationship("Project", back_populates="user")
    logs = relationship("QueryLog", back_populates="user") 