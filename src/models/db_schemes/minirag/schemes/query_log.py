from .minirag_base import SQLAlchemyBase
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship

class QueryLog(SQLAlchemyBase):
    __tablename__ = "query_logs"
    
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    log_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    user = relationship("User", back_populates="logs")
    
    # Query details
    question = Column(Text, nullable=False)
    llm_response = Column(Text, nullable=False)
    response_time_ms = Column(Float, nullable=False)  # Time to respond in milliseconds
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False) 