from .minirag_base import SQLAlchemyBase
from sqlalchemy import Column, Integer, DateTime, ForeignKey, func
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

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    chunks = relationship("DataChunk", back_populates="project")
    assets = relationship("Asset", back_populates="project")
