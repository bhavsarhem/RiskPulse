import os
import joblib
import json
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional, List
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score, f1_score, precision_score, recall_score
import logging

from backend.app.ml.features import FinancialFeatureEngine
from backend.app.ml.nlp import nlp_risk_engine

logger = logging.getLogger("RiskPulse.MLModels")

# Define fallback model class if some boosters fail to import
class ModelTrainer:
    def __init__(self):
        # We will attempt imports of boosting models
        self.xgboost_available = False
        self.catboost_available = False
        self.lightgbm_available = False
        
        try:
            import xgboost
            self.xgboost_available = True
        except ImportError:
            logger.info("XGBoost not available, using Scikit-Learn RandomForest/GradientBoosting.")
            
        try:
            import catboost
            self.catboost_available = True
        except ImportError:
            logger.info("CatBoost not available, using Scikit-Learn RandomForest/GradientBoosting.")
            
        try:
            import lightgbm
            self.lightgbm_available = True
        except ImportError:
            logger.info("LightGBM not available, using Scikit-Learn RandomForest/GradientBoosting.")

        # Features that we use for default classification
        self.feature_cols = [
            "loan_amount", "interest_rate", "term_months", "monthly_revenue",
            "debt", "current_assets", "current_liabilities", "gst_growth_pct",
            "monthly_revenue_growth", "emi_delay_frequency", "collateral_value",
            "credit_utilization", "credit_age_months", "sentiment_risk_score",
            "debt_to_income", "current_ratio", "quick_ratio", "cash_flow_ratio",
            "loan_utilization", "emi_burden", "collateral_coverage", "business_stability"
        ]

    def prepare_dataset(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Ensures all features are generated and returns X, y."""
        # 1. Generate text risk features if missing
        if "sentiment_risk_score" not in df.columns:
            if "unstructured_remarks" in df.columns:
                sentiments = df["unstructured_remarks"].apply(
                    lambda x: nlp_risk_engine.analyze_remarks(str(x))["sentiment_score"]
                )
                df["sentiment_risk_score"] = sentiments
            else:
                df["sentiment_risk_score"] = 0.0

        # 2. Financial ratios feature engineering
        engine = FinancialFeatureEngine()
        df_feat = engine.create_features_df(df)

        # 3. Ensure target default column exists
        if "is_default" not in df_feat.columns:
            # For training demo purposes, generate synthetic target based on key risk features
            logger.warning("Target column 'is_default' not found in uploaded dataset. Simulating defaults for demo.")
            # Default occurs more when debt/income > 0.4, emi delays > 2, stability index < 1.0, current_ratio < 1.0
            prob = (
                (df_feat["debt_to_income"] * 0.35) +
                (df_feat["emi_burden"] * 0.25) +
                (df_feat["emi_delay_frequency"] * 0.15) +
                (df_feat["sentiment_risk_score"].apply(lambda x: -x if x < 0 else 0) * 0.15) -
                (df_feat["business_stability"] * 0.2)
            )
            df_feat["is_default"] = (prob > prob.median()).astype(int)

        X = df_feat[self.feature_cols]
        y = df_feat["is_default"]
        return X, y

    def train_ensemble(self, X: pd.DataFrame, y: pd.Series, save_dir: str = "./backend/app/ml/checkpoints") -> Dict[str, Any]:
        """Trains multiple classifiers, evaluates, chooses the best one, and saves it."""
        os.makedirs(save_dir, exist_ok=True)
        
        # Train-Test Split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        
        # Scaling
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        models_dict = {
            "Logistic Regression": LogisticRegression(class_weight="balanced", random_state=42),
            "Random Forest": RandomForestClassifier(class_weight="balanced", n_estimators=100, random_state=42),
            "Gradient Boosting": GradientBoostingClassifier(n_estimators=100, random_state=42)
        }

        # Try to include LightGBM
        if self.lightgbm_available:
            from lightgbm import LGBMClassifier
            models_dict["LightGBM"] = LGBMClassifier(class_weight="balanced", random_state=42, verbose=-1)

        # Try to include XGBoost
        if self.xgboost_available:
            from xgboost import XGBClassifier
            # Calculate class weight ratio
            ratio = (len(y_train) - sum(y_train)) / (sum(y_train) + 1)
            models_dict["XGBoost"] = XGBClassifier(scale_pos_weight=ratio, random_state=42, eval_metric="logloss")

        # Try to include CatBoost
        if self.catboost_available:
            from catboost import CatBoostClassifier
            models_dict["CatBoost"] = CatBoostClassifier(auto_class_weights="Balanced", random_state=42, verbose=0)

        results = {}
        best_name = None
        best_auc = -1.0
        best_model = None

        for name, clf in models_dict.items():
            try:
                # XGBoost and CatBoost handle pandas frames natively but work well with scaled arrays too
                # For consistency, use scaled arrays
                clf.fit(X_train_scaled, y_train)
                preds = clf.predict(X_test_scaled)
                
                # Check if model has predict_proba
                if hasattr(clf, "predict_proba"):
                    probs = clf.predict_proba(X_test_scaled)[:, 1]
                else:
                    probs = preds.astype(float)
                
                # Metrics
                acc = accuracy_score(y_test, preds)
                auc = roc_auc_score(y_test, probs)
                f1 = f1_score(y_test, preds, zero_division=0)
                prec = precision_score(y_test, preds, zero_division=0)
                rec = recall_score(y_test, preds, zero_division=0)
                
                results[name] = {
                    "accuracy": float(acc),
                    "roc_auc": float(auc),
                    "f1_score": float(f1),
                    "precision": float(prec),
                    "recall": float(rec)
                }
                
                logger.info(f"{name} trained: ROC-AUC={auc:.4f}, F1-Score={f1:.4f}")
                
                if auc > best_auc:
                    best_auc = auc
                    best_name = name
                    best_model = clf
            except Exception as e:
                logger.error(f"Failed training {name}: {str(e)}")

        if not best_model:
            # Total fallback to simple logistic regression
            logger.error("All models failed training. Forcing a standard Logistic Regression.")
            best_name = "Logistic Regression"
            best_model = models_dict["Logistic Regression"]
            best_model.fit(X_train_scaled, y_train)
            best_auc = 0.5

        # Save active pipeline
        pipeline_file = os.path.join(save_dir, "active_pipeline.joblib")
        pipeline_data = {
            "scaler": scaler,
            "model": best_model,
            "algorithm": best_name,
            "feature_cols": self.feature_cols
        }
        joblib.dump(pipeline_data, pipeline_file)
        
        # Save metrics
        metrics_file = os.path.join(save_dir, "metrics.json")
        with open(metrics_file, "w") as f:
            json.dump({
                "best_model": best_name,
                "roc_auc": best_auc,
                "all_results": results
            }, f, indent=4)

        return {
            "best_model": best_name,
            "metrics": results[best_name] if best_name in results else {"roc_auc": best_auc},
            "filepath": pipeline_file,
            "all_results": results
        }

class Predictor:
    def __init__(self, save_dir: str = "./backend/app/ml/checkpoints"):
        self.save_dir = save_dir
        self.pipeline_file = os.path.join(save_dir, "active_pipeline.joblib")
        self.pipeline_data = None
        self.load_pipeline()

    def load_pipeline(self):
        if os.path.exists(self.pipeline_file):
            try:
                self.pipeline_data = joblib.load(self.pipeline_file)
                logger.info(f"Loaded active model: {self.pipeline_data['algorithm']}")
            except Exception as e:
                logger.error(f"Failed loading model pipeline: {str(e)}")
                self.pipeline_data = None

    def predict_dict(self, borrower_features: Dict[str, Any]) -> Tuple[float, float]:
        """
        Predicts default probability and returns (probability, confidence_score).
        Falls back to a rule-based credit risk estimator if no model file is loaded.
        """
        if not self.pipeline_data:
            # Safe Fallback: Calculate credit risk score using rule-based scoring (stability indices, delays)
            # If no trained model, we provide a deterministic prediction based on financials
            dti = float(borrower_features.get("debt_to_income", 0.5))
            delays = int(borrower_features.get("emi_delay_frequency", 0))
            stability = float(borrower_features.get("business_stability", 1.0))
            current_ratio = float(borrower_features.get("current_ratio", 1.0))
            
            # Estimate probability
            prob = 0.1  # base probability
            prob += min(0.4, max(0.0, dti * 0.3))
            prob += min(0.4, delays * 0.1)
            if current_ratio < 1.0:
                prob += 0.15
            prob -= min(0.3, max(0.0, (stability - 0.5) * 0.2))
            prob = min(0.99, max(0.01, prob))
            
            # Confidence is lower when using fallback rules
            return prob, 0.70

        # Run inference using ML model
        # Reconstruct row
        cols = self.pipeline_data["feature_cols"]
        row_vals = [float(borrower_features.get(c, 0.0)) for c in cols]
        
        # Predict
        scaler = self.pipeline_data["scaler"]
        model = self.pipeline_data["model"]
        
        row_arr = np.array(row_vals).reshape(1, -1)
        row_scaled = scaler.transform(row_arr)
        
        if hasattr(model, "predict_proba"):
            prob = float(model.predict_proba(row_scaled)[0, 1])
        else:
            prob = float(model.predict(row_scaled)[0])
            
        # Confidence score based on standard model deviation or prediction margins
        confidence = 0.95 if (prob < 0.15 or prob > 0.85) else 0.85
        return prob, confidence

predictor = Predictor()
model_trainer = ModelTrainer()
