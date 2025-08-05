from .minirag_base import SQLAlchemyBase
from sqlalchemy import Column, Integer, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship

class Project(SQLAlchemyBase):

    __tablename__ = "projects"
    
    project_id = Column(Integer, primary_key=True, autoincrement=True)
    project_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    user = relationship("User", back_populates="projects")
    
    # Project code that is unique per user (what users see as "Project 1", "Project 2", etc.)
    # Making it optional for now to work with existing database structure
    project_code = Column(Integer, nullable=True)
    
    # Ensure project_code is unique per user (only if project_code exists)
    __table_args__ = (UniqueConstraint('user_id', 'project_code', name='_user_project_code_uc'),)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    chunks = relationship("DataChunk", back_populates="project", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="project", cascade="all, delete-orphan")
