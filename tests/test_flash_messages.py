"""Tests for flash message utilities."""

import pytest
from starlette.middleware.sessions import SessionMiddleware
from starlette.testclient import TestClient
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from app.utils.flash import add_flash_message, get_flash_messages


# Create a simple test app with SessionMiddleware
def flash_endpoint(request):
    """Endpoint to test adding flash messages."""
    message = request.query_params.get("message", "Test")
    category = request.query_params.get("category", "info")
    add_flash_message(request, message, category)
    return JSONResponse({"status": "added"})


def get_flash_endpoint(request):
    """Endpoint to test getting flash messages."""
    messages = get_flash_messages(request)
    return JSONResponse({"messages": messages})


routes = [
    Route("/add-flash", flash_endpoint),
    Route("/get-flash", get_flash_endpoint),
]

test_app = Starlette(routes=routes)
test_app.add_middleware(SessionMiddleware, secret_key="test-secret-key")


@pytest.fixture
def client():
    """Create test client with session support."""
    return TestClient(test_app)


def test_add_flash_message_creates_session_key(client):
    """Test adding first flash message creates session key."""
    # Add a flash message
    response = client.get("/add-flash?message=Test message&category=info")
    assert response.status_code == 200

    # Get flash messages
    response = client.get("/get-flash")
    assert response.status_code == 200

    data = response.json()
    assert len(data["messages"]) == 1
    assert data["messages"][0] == {
        "message": "Test message",
        "category": "info",
    }


def test_add_multiple_flash_messages(client):
    """Test adding multiple flash messages."""
    # Add multiple messages
    client.get("/add-flash?message=Success!&category=success")
    client.get("/add-flash?message=Error occurred&category=error")
    client.get("/add-flash?message=Warning!&category=warning")

    # Get all messages
    response = client.get("/get-flash")
    messages = response.json()["messages"]

    assert len(messages) == 3
    assert messages[0]["category"] == "success"
    assert messages[1]["category"] == "error"
    assert messages[2]["category"] == "warning"


def test_get_flash_messages_clears_session(client):
    """Test getting flash messages removes them from session."""
    # Add messages
    client.get("/add-flash?message=Test&category=info")
    client.get("/add-flash?message=Another&category=success")

    # Get messages (should clear them)
    response = client.get("/get-flash")
    messages = response.json()["messages"]

    assert len(messages) == 2
    assert messages[0]["message"] == "Test"
    assert messages[1]["message"] == "Another"

    # Get again - should be empty
    response = client.get("/get-flash")
    messages = response.json()["messages"]
    assert messages == []


def test_get_flash_messages_empty_when_none(client):
    """Test getting flash messages returns empty list when none exist."""
    response = client.get("/get-flash")
    messages = response.json()["messages"]

    assert messages == []


def test_flash_message_categories(client):
    """Test all flash message categories work correctly."""
    categories = ["success", "error", "warning", "info"]

    for category in categories:
        client.get(f"/add-flash?message=Test {category}&category={category}")

    response = client.get("/get-flash")
    messages = response.json()["messages"]
    assert len(messages) == 4

    for i, category in enumerate(categories):
        assert messages[i]["category"] == category
        assert messages[i]["message"] == f"Test {category}"


def test_flash_message_default_category(client):
    """Test flash message defaults to 'info' category."""
    client.get("/add-flash?message=Default category test")

    response = client.get("/get-flash")
    messages = response.json()["messages"]
    assert messages[0]["category"] == "info"
