from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import json

from backend.app.core.database import get_db
from backend.app.schemas.dashboard import DashboardStats
from backend.app.repositories.loan_repo import loan_repo
from backend.app.api.deps import get_current_active_user
from backend.app.models.user import User
from backend.app.models.loan import Loan
from backend.app.models.audit import AuditLog

router = APIRouter()

@router.get("/", response_model=DashboardStats)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Retrieve portfolio aggregates, alerts list, and recent user actions."""
    # 1. Base statistics
    stats = loan_repo.get_portfolio_stats(db)
    
    # 2. Extract risk distribution percentages
    total = stats["total_loans"]
    distribution = []
    for cat, count in stats["risk_categories"].items():
        pct = (count / total * 100) if total > 0 else 0.0
        distribution.append({
            "category": cat,
            "count": count,
            "percentage": round(pct, 2)
        })

    # 3. Pull active alerts from all loans
    all_loans = db.query(Loan).all()
    alerts_list = []
    for l in all_loans:
        if l.early_warning_alerts:
            try:
                loan_alerts = json.loads(l.early_warning_alerts)
                for alert in loan_alerts:
                    alerts_list.append({
                        "loan_id": l.id,
                        "borrower_name": l.borrower_name,
                        "risk_category": l.risk_category,
                        "alert_type": alert["type"], # Warning, Critical
                        "message": alert["message"]
                    })
            except Exception:
                pass

    # Sort alerts: Critical first
    alerts_list = sorted(alerts_list, key=lambda x: x["alert_type"] == "Critical", reverse=True)[:15]

    # 4. Pull audit logs for recent activity
    recent_logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10).all()
    activity = []
    for log in recent_logs:
        activity.append({
            "action": log.action,
            "details": log.details,
            "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        })

    return {
        "total_active_loans": stats["total_loans"],
        "total_portfolio_value": stats["total_value"],
        "average_default_probability": stats["avg_default_probability"],
        "risk_distribution": distribution,
        "alerts": alerts_list,
        "recent_activity": activity
    }
