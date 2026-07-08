from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import os
import shutil

from backend.app.core.database import get_db
from backend.app.schemas.model import MLModelResponse, ModelTrainResponse
from backend.app.services.prediction_service import prediction_service
from backend.app.api.deps import get_current_active_user, RoleChecker
from backend.app.models.user import User

router = APIRouter()

# Create a temporary directory for uploaded training datasets
UPLOAD_DIR = "./backend/app/ml/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload-dataset")
async def upload_training_dataset(
    file: UploadFile = File(...),
    current_user: User = Depends(RoleChecker(["admin"]))
) -> Any:
    """Upload a CSV or Excel dataset for model training."""
    if not file.filename.endswith(('.csv', '.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail="Only CSV or Excel files are allowed.")
        
    filepath = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {
            "message": "Dataset uploaded successfully.",
            "filename": file.filename,
            "filepath": filepath
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

@router.post("/train-model", response_model=ModelTrainResponse)
def train_model(
    dataset_filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["admin"]))
) -> Any:
    """Train ensemble classifiers on the uploaded dataset and register the best performer."""
    filepath = os.path.join(UPLOAD_DIR, dataset_filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_filename}' not found. Upload it first.")
        
    train_results = prediction_service.train_active_model(db, filepath)
    return {
        "message": "Model ensemble trained and updated successfully.",
        "best_model": train_results["best_model"],
        "metrics": train_results["metrics"],
        "all_results": train_results["all_results"],
        "filepath": train_results["filepath"]
    }

@router.get("/", response_model=List[MLModelResponse])
def get_all_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Retrieve metadata logs for all trained models."""
    return prediction_service.get_models(db)

@router.get("/active", response_model=MLModelResponse)
def get_active_model(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get metadata for the currently active default prediction model."""
    active = prediction_service.get_active_model(db)
    if not active:
        raise HTTPException(status_code=404, detail="No active model found. Train a model first.")
    return active
