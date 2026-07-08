import os
import pandas as pd
import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.ml.models import model_trainer, predictor
from backend.app.models.ml_model import MLModel
from backend.app.models.audit import AuditLog
from fastapi import HTTPException

class PredictionService:
    def train_active_model(self, db: Session, dataset_path: str) -> Dict[str, Any]:
        """Trains models using the specified dataset, updates active model metadata in the DB."""
        if not os.path.exists(dataset_path):
            raise HTTPException(status_code=400, detail="Dataset file not found.")

        try:
            # 1. Load data
            if dataset_path.endswith('.csv'):
                df = pd.read_csv(dataset_path)
            elif dataset_path.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(dataset_path)
            else:
                raise ValueError("Unsupported training file type.")

            # 2. Extract features and target
            X, y = model_trainer.prepare_dataset(df)

            # 3. Train
            train_results = model_trainer.train_ensemble(X, y)

            # 4. Save model metadata to database
            db.query(MLModel).update({MLModel.is_active: False}) # Deactivate previous
            
            db_model = MLModel(
                model_name="RiskPulse-Ensemble-Default",
                version=f"1.0.{db.query(MLModel).count() + 1}",
                algorithm=train_results["best_model"],
                metrics=json.dumps(train_results["all_results"]),
                filepath=train_results["filepath"],
                is_active=True
            )
            db.add(db_model)
            
            # Log action
            db.add(AuditLog(
                action="TRAIN_MODEL",
                details=f"Trained new model. Selected {train_results['best_model']} with ROC-AUC {train_results['metrics'].get('roc_auc', 0.0):.4f}"
            ))
            db.commit()

            # 5. Reload predictor active model
            predictor.load_pipeline()

            return train_results

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed during model training: {str(e)}")

    def get_models(self, db: Session) -> List[MLModel]:
        return db.query(MLModel).order_by(MLModel.created_at.desc()).all()

    def get_active_model(self, db: Session) -> Optional[MLModel]:
        return db.query(MLModel).filter(MLModel.is_active == True).first()

prediction_service = PredictionService()
