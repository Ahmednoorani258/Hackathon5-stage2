import os
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from production.channels import web_form_handler
from production.channels.web_form_handler import router


def _make_client() -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api")
    return TestClient(app)


def test_submit_support_form_success(monkeypatch):
    calls = {"create": None, "agent": None}

    async def fake_publish_to_kafka(topic, message_data):
        return None

    async def fake_create_ticket_record(ticket_id, message_data):
        calls["create"] = (ticket_id, message_data)

    async def fake_handle_customer_message_async(payload):
        calls["agent"] = payload
        return {"status": "success"}

    monkeypatch.setattr(web_form_handler, "publish_to_kafka", fake_publish_to_kafka)
    monkeypatch.setattr(web_form_handler, "create_ticket_record", fake_create_ticket_record)
    monkeypatch.setattr(web_form_handler, "handle_customer_message_async", fake_handle_customer_message_async)

    client = _make_client()
    payload = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "subject": "Need setup help",
        "category": "technical",
        "message": "I need help connecting SSO for my workspace.",
        "priority": "high",
    }

    response = client.post("/api/support/submit", json=payload)
    assert response.status_code == 200

    body = response.json()
    assert "ticket_id" in body
    assert body["estimated_response_time"]

    assert calls["create"] is not None
    created_ticket_id, message_data = calls["create"]
    assert created_ticket_id == body["ticket_id"]
    assert message_data["channel"] == "web_form"
    assert message_data["customer_email"] == payload["email"]

    assert calls["agent"] is not None
    assert calls["agent"]["channel"] == "web_form"
    assert calls["agent"]["customer_email"] == payload["email"]
    assert calls["agent"]["message"] == payload["message"]


def test_submit_support_form_validation_error():
    client = _make_client()
    payload = {
        "name": "J",
        "email": "invalid-email",
        "subject": "Help",
        "category": "invalid-category",
        "message": "short",
        "priority": "medium",
    }

    response = client.post("/api/support/submit", json=payload)
    assert response.status_code == 422


def test_ticket_status_success(monkeypatch):
    async def fake_get_ticket_by_id(ticket_id):
        return {
            "status": "open",
            "messages": [
                {
                    "channel": "web_form",
                    "direction": "inbound",
                    "role": "customer",
                    "content": "Need help with onboarding",
                    "created_at": "2026-04-11T00:00:00+00:00",
                    "channel_message_id": ticket_id,
                    "delivery_status": "delivered",
                }
            ],
            "created_at": "2026-04-11T00:00:00+00:00",
            "last_updated": "2026-04-11T00:00:00+00:00",
        }

    monkeypatch.setattr(web_form_handler, "get_ticket_by_id", fake_get_ticket_by_id)

    client = _make_client()
    ticket_id = "11111111-1111-1111-1111-111111111111"
    response = client.get(f"/api/support/ticket/{ticket_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["ticket_id"] == ticket_id
    assert body["status"] == "open"
    assert len(body["messages"]) >= 1


def test_ticket_status_not_found(monkeypatch):
    async def fake_get_ticket_by_id(ticket_id):
        return None

    monkeypatch.setattr(web_form_handler, "get_ticket_by_id", fake_get_ticket_by_id)

    client = _make_client()
    response = client.get("/api/support/ticket/11111111-1111-1111-1111-111111111111")
    assert response.status_code == 404
