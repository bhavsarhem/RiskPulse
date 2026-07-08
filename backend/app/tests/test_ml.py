import pytest
import pandas as pd
import numpy as np

from backend.app.ml.features import FinancialFeatureEngine
from backend.app.ml.pipeline import DataPreprocessor
from backend.app.ml.nlp import nlp_risk_engine

def test_financial_ratios_calculation():
    """Verify that financial ratios are calculated correctly and handle division by zero."""
    sample_borrower = {
        "loan_amount": 100000.0,
        "monthly_revenue": 10000.0,
        "debt": 40000.0,
        "current_assets": 50000.0,
        "current_liabilities": 25000.0,
        "monthly_cash_inflow": 12000.0,
        "monthly_cash_outflow": 10000.0,
        "collateral_value": 150000.0,
        "credit_utilization": 0.40,
        "interest_rate": 0.12,
        "term_months": 36,
        "emi_delay_frequency": 0
    }
    
    ratios = FinancialFeatureEngine.calculate_ratios_dict(sample_borrower)
    
    # 1. Debt-to-Income: debt / (monthly_revenue * 12) = 40000 / 120000 = 0.333
    assert pytest.approx(ratios["debt_to_income"], 0.01) == 0.333
    
    # 2. Current Ratio: assets / liabilities = 50000 / 25000 = 2.0
    assert ratios["current_ratio"] == 2.0
    
    # 3. Quick Ratio: (assets * 0.7) / liabilities = 35000 / 25000 = 1.4
    assert ratios["quick_ratio"] == 1.4
    
    # 4. Collateral Coverage: collateral / loan = 150000 / 100000 = 1.5
    assert ratios["collateral_coverage"] == 1.5
    
    # 5. Business stability index should be high for zero delays and healthy current ratio
    assert ratios["business_stability"] > 1.0

def test_preprocessor_outlier_clipping_and_imputation():
    """Verify missing values are filled and outliers are successfully clipped."""
    schema = {
        "debt": "numerical",
        "monthly_revenue": "numerical"
    }
    
    preprocessor = DataPreprocessor(schema)
    
    # Create test data with missing values and extreme outlier
    raw_df = pd.DataFrame({
        "debt": [100.0, 120.0, np.nan, 110.0, 10000.0],  # 10000 is outlier
        "monthly_revenue": [50.0, 60.0, 55.0, 50.0, 50.0]
    })
    
    cleaned_df = preprocessor.clean_and_validate(raw_df)
    
    # Missing value in index 2 (debt) should be imputed with median
    assert not cleaned_df["debt"].isna().any()
    
    # Outlier (index 4) should be capped/clipped
    assert cleaned_df["debt"].iloc[4] < 10000.0

def test_nlp_sentiment_sentiment_score():
    """Verify that sentiment is negative for distress remarks and extracts correct risk flags."""
    remarks = "WARNING: Apex Logistics has delayed loan repayments twice. Internal auditor reports serious cash flow issues and legal dispute is active."
    
    analysis = nlp_risk_engine.analyze_remarks(remarks)
    
    # Sentiment score should be negative due to words like 'delayed', 'dispute', 'warning'
    assert analysis["sentiment_score"] < 0
    
    # Should detect late payments and legal dispute flags
    assert "late_payments" in analysis["risk_flags"]
    assert "legal_dispute" in analysis["risk_flags"]
    assert analysis["risk_score"] > 20.0
