from uuid import uuid4

from fastapi.testclient import TestClient

from api import routes_auth
from api.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_auth_pages_are_served():
    auth_response = client.get("/")
    dashboard_response = client.get("/dashboard")

    assert auth_response.status_code == 200
    assert "Login" in auth_response.text
    assert dashboard_response.status_code == 200
    assert "DASHBOARD" in dashboard_response.text


def test_register_and_login_return_jwt_tokens():
    email = "auth-flow@example.com"
    register_response = client.post(
        "/api/auth/register",
        json={"email": email, "full_name": "Auth Flow", "password": "password123"},
    )
    if register_response.status_code == 409:
        login_response = client.post("/api/auth/login", json={"email": email, "password": "password123"})
        assert login_response.status_code == 200
        assert login_response.json()["access_token"]
        return

    assert register_response.status_code == 200
    assert register_response.json()["access_token"]

    login_response = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert login_response.status_code == 200
    assert login_response.json()["access_token"]


def test_forgot_password_resets_user_password():
    email = f"reset-{uuid4().hex}@example.com"
    register_response = client.post(
        "/api/auth/register",
        json={"email": email, "full_name": "Reset Flow", "password": "password123"},
    )
    assert register_response.status_code == 200

    sent_otps = {}

    def fake_send_otp(recipient: str, otp: str) -> None:
        sent_otps[recipient] = otp

    original_sender = routes_auth.email_service.send_password_reset_otp
    try:
        routes_auth.email_service.send_password_reset_otp = fake_send_otp
        reset_request = client.post("/api/auth/forgot-password", json={"email": email})
    finally:
        routes_auth.email_service.send_password_reset_otp = original_sender

    assert reset_request.status_code == 200
    assert reset_request.json()["message"] == "OTP sent to your Gmail address."
    assert reset_request.json()["otp"] is None
    otp = sent_otps[email]
    assert otp.isdigit()
    assert len(otp) == 6

    reset_response = client.post(
        "/api/auth/reset-password",
        json={"email": email, "otp": otp, "password": "newpassword123"},
    )
    assert reset_response.status_code == 200
    assert reset_response.json()["access_token"]

    old_login = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert old_login.status_code == 401

    new_login = client.post("/api/auth/login", json={"email": email, "password": "newpassword123"})
    assert new_login.status_code == 200
    assert new_login.json()["access_token"]


def test_forgot_password_requires_existing_account():
    response = client.post("/api/auth/forgot-password", json={"email": f"missing-{uuid4().hex}@example.com"})

    assert response.status_code == 404
    assert response.json()["detail"] == "No account found for this email. Please register first."
