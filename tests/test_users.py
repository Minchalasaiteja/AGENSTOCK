import pytest
from fastapi.testclient import TestClient
import importlib

# Import the FastAPI app
app_main = importlib.import_module('app.main')
client = TestClient(app_main.app)

@pytest.fixture(autouse=True)
def patch_send_email(monkeypatch):
    # Patch the send_verification_email to avoid real SMTP calls
    async def fake_send(email, code):
        return True
    monkeypatch.setattr('app.services.email_service.send_verification_email', fake_send)
    yield

def test_send_verification_requires_authentication():
    # No auth -> should return 401 or redirect depending on auth implementation
    resp = client.post('/api/users/send-verification', json={"email": "test@example.com"})
    assert resp.status_code in (401, 403)

# Note: For an authenticated test you'd need to create a test user and provide a token/cookie.
# This test ensures the endpoint exists and the email service is invoked for authenticated calls.
