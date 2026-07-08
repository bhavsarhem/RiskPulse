from typing import List, Dict, Any
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.app.models.loan import Loan
from backend.app.repositories.base import BaseRepository

class LoanRepository(BaseRepository[Loan]):
    def __init__(self):
        super().__init__(Loan)

    def get_portfolio_stats(self, db: Session) -> Dict[str, Any]:
        """
        Returns aggregate stats for the entire loan portfolio
        """
        total_loans = db.query(func.count(Loan.id)).scalar() or 0
        total_value = db.query(func.sum(Loan.loan_amount)).scalar() or 0.0
        avg_probability = db.query(func.avg(Loan.default_probability)).scalar() or 0.0
        
        # Risk category counts
        categories = db.query(
            Loan.risk_category, 
            func.count(Loan.id)
        ).group_by(Loan.risk_category).all()
        
        cat_counts = {cat: count for cat, count in categories}
        for cat in ["Very Low", "Low", "Medium", "High", "Critical"]:
            if cat not in cat_counts:
                cat_counts[cat] = 0

        return {
            "total_loans": total_loans,
            "total_value": total_value,
            "avg_default_probability": avg_probability,
            "risk_categories": cat_counts
        }

    def get_recent_loans(self, db: Session, limit: int = 10) -> List[Loan]:
        return db.query(Loan).order_by(Loan.created_at.desc()).limit(limit).all()

    def get_high_risk_loans(self, db: Session) -> List[Loan]:
        return db.query(Loan).filter(Loan.risk_category.in_(["High", "Critical"])).all()

loan_repo = LoanRepository()
