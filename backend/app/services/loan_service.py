import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.models.loan import Loan
from backend.app.models.audit import AuditLog
from backend.app.schemas.loan import LoanCreate
from backend.app.repositories.loan_repo import loan_repo
from backend.app.ml.features import FinancialFeatureEngine
from backend.app.ml.nlp import nlp_risk_engine
from backend.app.ml.models import predictor
from backend.app.ml.explainability import explainable_ai
import logging

logger = logging.getLogger("RiskPulse.LoanService")

class LoanService:
    def process_and_create_loan(self, db: Session, loan_in: LoanCreate) -> Loan:
        """
        Takes raw loan inputs, calculates financial indicators, runs NLP on remarks,
        triggers ML prediction, computes risk scores/early warnings/recommendations,
        and saves everything to the database.
        """
        # 1. Base input dictionary
        loan_dict = loan_in.model_dump()
        
        # 2. NLP remarks risk extraction
        nlp_results = nlp_risk_engine.analyze_remarks(loan_in.unstructured_remarks or "")
        
        # 3. Calculate financial ratios
        ratios = FinancialFeatureEngine.calculate_ratios_dict(loan_dict)
        
        # Combine all features for the ML predictor
        all_features = {**loan_dict, **ratios}
        all_features["sentiment_risk_score"] = nlp_results["sentiment_score"]
        
        # 4. Run model prediction (Default Probability & Confidence)
        default_prob, confidence = predictor.predict_dict(all_features)
        
        # 5. Risk Score Engine (0-1000 Risk Score)
        # Higher score means lower risk (standard banking score, e.g. FICO/CIBIL style)
        # Or higher means higher risk. Let's use standard banking: 0 is worst default risk, 1000 is safest.
        base_score = int((1.0 - default_prob) * 1000)
        # Fine-tune based on credit delay frequency and text sentiment
        base_score -= int(ratios.get("emi_delay_frequency", 0) * 40)
        base_score = max(0, min(1000, base_score))
        
        # Risk Categories
        if base_score < 300:
            category = "Critical"
        elif base_score < 500:
            category = "High"
        elif base_score < 700:
            category = "Medium"
        elif base_score < 850:
            category = "Low"
        else:
            category = "Very Low"
            
        # Indian Financial Laws and Regulations Adaptations
        # 1. MSMED Act 2020 Classification (assuming 1 USD = 80 INR)
        usd_to_inr = 80.0
        annual_turnover_inr = loan_in.monthly_revenue * 12 * usd_to_inr
        investment_inr = loan_in.loan_amount * usd_to_inr
        
        if investment_inr <= 10000000 and annual_turnover_inr <= 50000000:
            msme_class = "Micro Enterprise"
        elif investment_inr <= 100000000 and annual_turnover_inr <= 500000000:
            msme_class = "Small Enterprise"
        elif investment_inr <= 500000000 and annual_turnover_inr <= 2500000000:
            msme_class = "Medium Enterprise"
        else:
            msme_class = "Corporate (Exceeds MSME Threshold)"

        # 2. RBI SMA (Special Mention Account) Framework for Stress Assets
        delays = loan_in.emi_delay_frequency
        if delays == 0:
            rbi_sma_status = "Standard Asset"
        elif delays == 1:
            rbi_sma_status = "SMA-0 (1-30 Days Overdue)"
        elif delays == 2:
            rbi_sma_status = "SMA-1 (31-60 Days Overdue)"
        elif delays == 3:
            rbi_sma_status = "SMA-2 (61-90 Days Overdue)"
        else:
            rbi_sma_status = "NPA (Non-Performing Asset, >90 Days Overdue)"

        # 3. Early Warning System (EWS) incorporating RBI & Indian rules
        alerts = []
        if loan_in.monthly_revenue_growth < -0.10:
            alerts.append({
                "type": "Warning",
                "message": f"Severe Revenue Decline: {loan_in.monthly_revenue_growth * 100:.1f}% monthly drop"
            })
        if loan_in.gst_growth_pct < -0.05:
            alerts.append({
                "type": "Warning",
                "message": f"GST filing contraction: GSTR-3B activity down {loan_in.gst_growth_pct * 100:.1f}%"
            })
            
        # Add SMA warnings as mandated by RBI EWS guidelines
        if delays > 0:
            alerts.append({
                "type": "Critical" if delays >= 2 else "Warning",
                "message": f"RBI Stress Classification: Classified as {rbi_sma_status}"
            })
            
        # IBC / NCLT Check (Insolvency and Bankruptcy Code, 2016)
        remarks_lower = (loan_in.unstructured_remarks or "").lower()
        if any(term in remarks_lower for term in ["ibc", "nclt", "nclat", "ppirp", "section 54a", "insolvency"]):
            alerts.append({
                "type": "Critical",
                "message": "Insolvency Proceedings Alert: Mentions of IBC/NCLT or Section 54A PPIRP found in audit remarks"
            })

        if loan_in.credit_utilization > 0.8:
            alerts.append({
                "type": "Warning",
                "message": f"High Credit Line Utilization: credit line is {loan_in.credit_utilization * 100:.1f}% utilized"
            })
        if nlp_results["sentiment_score"] < -0.2:
            alerts.append({
                "type": "Critical",
                "message": f"Negative Public Signals: Audit/remarks flags detected: {', '.join(nlp_results['risk_flags'])}"
            })
        if ratios["current_ratio"] < 1.0:
            alerts.append({
                "type": "Warning",
                "message": f"Liquidity stress: Current ratio {ratios['current_ratio']:.2f} is under 1.0"
            })
            
        # 4. AI Recommendation Engine linked to PSL (Priority Sector Lending) targets
        psl_msg = f"PSL Eligible: Yes ({msme_class})" if msme_class != "Corporate (Exceeds MSME Threshold)" else "PSL Eligible: No"
        
        if default_prob > 0.70 or category == "Critical" or "NPA" in rbi_sma_status:
            rec = f"REJECT LOAN. Classified as {rbi_sma_status}. High probability of default. Action: Reference to IBC pre-pack or recovery committee."
            priority = "Urgent"
        elif default_prob > 0.40 or category == "High" or "SMA-2" in rbi_sma_status:
            coverage = ratios.get("collateral_coverage", 0.0)
            rec = f"RESTRUCTURE / ADDITIONAL COLLATERAL REQUIRED. Classified as {rbi_sma_status}. Collateral coverage ({coverage:.2f}x) must be increased to mitigate credit risk. {psl_msg}."
            priority = "High"
        elif default_prob > 0.20 or category == "Medium" or "SMA-1" in rbi_sma_status:
            rec = f"APPROVE WITH CONDITIONAL MONITORING. Classified as {rbi_sma_status}. Monitor GSTR filings monthly. {psl_msg}."
            priority = "Normal"
        else:
            rec = f"APPROVE LOAN. Classified as Standard Asset. Healthy financial ratios. {psl_msg}."
            priority = "Low"

        # 8. Create DB entry
        db_loan = Loan(
            borrower_name=loan_in.borrower_name,
            industry_sector=loan_in.industry_sector,
            loan_amount=loan_in.loan_amount,
            interest_rate=loan_in.interest_rate,
            term_months=loan_in.term_months,
            monthly_revenue=loan_in.monthly_revenue,
            debt=loan_in.debt,
            current_assets=loan_in.current_assets,
            current_liabilities=loan_in.current_liabilities,
            monthly_cash_inflow=loan_in.monthly_cash_inflow,
            monthly_cash_outflow=loan_in.monthly_cash_outflow,
            gst_growth_pct=loan_in.gst_growth_pct,
            monthly_revenue_growth=loan_in.monthly_revenue_growth,
            emi_delay_frequency=loan_in.emi_delay_frequency,
            collateral_value=loan_in.collateral_value,
            credit_utilization=loan_in.credit_utilization,
            credit_age_months=loan_in.credit_age_months,
            unstructured_remarks=loan_in.unstructured_remarks,
            
            # Outputs
            sentiment_risk_score=nlp_results["sentiment_score"],
            nlp_risk_summary=nlp_results["summary"],
            nlp_risk_flags=json.dumps(nlp_results["risk_flags"]),
            
            default_probability=default_prob,
            risk_score=base_score,
            risk_category=category,
            confidence_score=confidence,
            recommendation=rec,
            action_priority=priority,
            early_warning_alerts=json.dumps(alerts)
        )
        
        created_loan = loan_repo.create(db, obj_in=db_loan)
        
        # Log event
        db.add(AuditLog(
            action="CREATE_PREDICTION",
            user_email="system@riskpulse.ai",
            details=f"Generated credit report for {loan_in.borrower_name}. Score: {base_score} ({category}). Default Prob: {default_prob:.2f}"
        ))
        db.commit()
        return created_loan

    def get_explanation(self, db: Session, loan_id: int) -> Dict[str, Any]:
        """Runs SHAP explainability mapping for a given loan."""
        loan = loan_repo.get(db, loan_id)
        if not loan:
            raise ValueError("Loan not found")
            
        # Reconstruct features dict
        loan_dict = {
            "loan_amount": loan.loan_amount,
            "interest_rate": loan.interest_rate,
            "term_months": loan.term_months,
            "monthly_revenue": loan.monthly_revenue,
            "debt": loan.debt,
            "current_assets": loan.current_assets,
            "current_liabilities": loan.current_liabilities,
            "monthly_cash_inflow": loan.monthly_cash_inflow,
            "monthly_cash_outflow": loan.monthly_cash_outflow,
            "gst_growth_pct": loan.gst_growth_pct,
            "monthly_revenue_growth": loan.monthly_revenue_growth,
            "emi_delay_frequency": loan.emi_delay_frequency,
            "collateral_value": loan.collateral_value,
            "credit_utilization": loan.credit_utilization,
            "credit_age_months": loan.credit_age_months,
            "sentiment_risk_score": loan.sentiment_risk_score
        }
        
        # Recalculate ratios
        ratios = FinancialFeatureEngine.calculate_ratios_dict(loan_dict)
        full_features = {**loan_dict, **ratios}
        
        explanation = explainable_ai.explain_prediction(
            full_features, 
            loan.default_probability,
            predictor.pipeline_data
        )
        
        return {
            "loan_id": loan.id,
            "borrower_name": loan.borrower_name,
            "default_probability": loan.default_probability,
            "risk_score": loan.risk_score,
            "risk_category": loan.risk_category,
            "risk_factors": explanation["risk_factors"],
            "mitigating_factors": explanation["mitigating_factors"],
            "narrative": explanation["narrative"]
        }

loan_service = LoanService()
