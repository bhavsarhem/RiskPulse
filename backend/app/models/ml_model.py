from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from datetime import datetime
from backend.app.core.database import Base

class MLModel(Base):
    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, index=True, nullable=False)
    version = Column(String, nullable=False)
    algorithm = Column(String, nullable=False)  # Random Forest, XGBoost, etc.
    metrics = Column(Text, nullable=True)  # JSON encoded metrics (accuracy, AUC, etc.)
    filepath = Column(String, nullable=True)  # Path to saved model file
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
