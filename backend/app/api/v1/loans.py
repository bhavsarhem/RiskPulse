from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import json

from backend.app.core.database import get_db
from backend.app.schemas.loan import LoanCreate, LoanResponse, LoanExplanationResponse
from backend.app.services.loan_service import loan_service
from backend.app.repositories.loan_repo import loan_repo
from backend.app.api.deps import get_current_active_user, RoleChecker
from backend.app.models.user import User
from backend.app.ml.nlp import nlp_risk_engine

router = APIRouter()

@router.get("/", response_model=List[LoanResponse])
def read_loans(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Retrieve all loan records."""
    return loan_repo.get_multi(db, skip=skip, limit=limit)

@router.post("/predict", response_model=LoanResponse)
def predict_loan_default(
    loan_in: LoanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Predict default probability and risk rating for an MSME borrower."""
    return loan_service.process_and_create_loan(db, loan_in)

@router.post("/upload-document")
async def upload_borrower_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Upload a borrower document (PDF, Text), extract text via OCR/parsers,
    and compute NLP risk parameters.
    """
    file_bytes = await file.read()
    try:
        text = nlp_risk_engine.extract_text_from_file(file_bytes, file.filename)
        nlp_stats = nlp_risk_engine.analyze_remarks(text)
        return {
            "filename": file.filename,
            "extracted_text_snippet": text[:500] + "...",
            "nlp_risk_score": nlp_stats["risk_score"],
            "sentiment_score": nlp_stats["sentiment_score"],
            "detected_risk_flags": nlp_stats["risk_flags"],
            "summary": nlp_stats["summary"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse document: {str(e)}")

@router.get("/{id}", response_model=LoanResponse)
def read_loan_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get single loan detail."""
    loan = loan_repo.get(db, id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan application not found")
    return loan

@router.get("/{id}/explain", response_model=LoanExplanationResponse)
def explain_loan_default(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Generate SHAP explainability insights for a borrower prediction."""
    try:
        return loan_service.get_explanation(db, id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate explanation: {str(e)}")

@router.get("/{id}/recommend")
def get_loan_recommendation(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Retrieve structured AI credit decision recommendations for a loan."""
    loan = loan_repo.get(db, id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    return {
        "loan_id": loan.id,
        "borrower_name": loan.borrower_name,
        "risk_category": loan.risk_category,
        "recommendation": loan.recommendation,
        "priority": loan.action_priority,
        "next_review_date": (datetime.utcnow() + timedelta(days=30 if loan.risk_category in ["Critical", "High"] else 90)).strftime("%Y-%m-%d")
    }
