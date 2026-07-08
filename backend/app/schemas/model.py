from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime

class ModelTrainRequest(BaseModel):
    # Optional parameters to customise hyperparameter searches
    search_type: Optional[str] = "grid" # grid, random
    balance_classes: Optional[bool] = True

class ModelMetrics(BaseModel):
    accuracy: float
    roc_auc: float
    f1_score: float
    precision: float
    recall: float

class ModelTrainResponse(BaseModel):
    message: str
    best_model: str
    metrics: ModelMetrics
    all_results: Dict[str, ModelMetrics]
    filepath: str

class MLModelResponse(BaseModel):
    id: int
    model_name: str
    version: str
    algorithm: str
    metrics: Optional[str] = None
    filepath: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
