from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from backend.app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    user_email = Column(String, nullable=True)
    action = Column(String, nullable=False)  # e.g., "TRAIN_MODEL", "UPLOAD_LOANS"
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
