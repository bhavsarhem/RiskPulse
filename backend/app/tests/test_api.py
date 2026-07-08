import pytest
from fastapi.testclient import TestClient
from backend.app.main import app, startup_db_seed

@pytest.fixture(autouse=True, scope="module")
def seed_db():
    startup_db_seed()

client = TestClient(app)

def test_read_root():
    """Verify that root endpoint is online."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_user_authentication_flow():
    """Verify token generation for seeded users and role access."""
    # 1. Login with analyst seeded credentials
    login_payload = {
        "email": "analyst@riskpulse.ai",
        "password": "analystpassword123"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "analyst"
    
    # 2. Access auth protected route using token
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    me_response = client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "analyst@riskpulse.ai"

def test_credit_risk_prediction_flow():
    """Verify prediction endpoint parses variables and computes risk scores."""
    # Authenticate analyst
    login_payload = {
        "email": "analyst@riskpulse.ai",
        "password": "analystpassword123"
    }
    token = client.post("/api/v1/auth/login", json=login_payload).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Input payload
    loan_payload = {
        "borrower_name": "Test Enterprise",
        "industry_sector": "Manufacturing",
        "loan_amount": 50000.0,
        "monthly_revenue": 12000.0,
        "debt": 1000.0,
        "current_assets": 15000.0,
        "current_liabilities": 10000.0,
        "monthly_cash_inflow": 12500.0,
        "monthly_cash_outflow": 11000.0,
        "gst_growth_pct": 0.05,
        "monthly_revenue_growth": 0.02,
        "emi_delay_frequency": 0,
        "collateral_value": 60000.0,
        "credit_utilization": 0.20,
        "credit_age_months": 36,
        "unstructured_remarks": "Very stable business. Growing cash flows."
    }

    response = client.post("/api/v1/loans/predict", json=loan_payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "default_probability" in data
    assert "risk_score" in data
    assert "risk_category" in data
    assert "recommendation" in data
    
    # Check that loan was saved and is inspectable
    loan_id = data["id"]
    get_response = client.get(f"/api/v1/loans/{loan_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["borrower_name"] == "Test Enterprise"
