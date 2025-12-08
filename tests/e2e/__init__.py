"""E2E test utilities and helpers.

Provides common functions for HTTP-level testing with HTMX.
See: TESTING.md §End-to-End Tests
"""


def is_partial_html(content: str) -> bool:
    """Check if response is partial HTML (not full page).

    HTMX endpoints should return partial HTML without <html>, <body> tags.

    Args:
        content: Response content as string

    Returns:
        True if partial HTML (no full page wrapper)
    """
    content_lower = content.lower()
    return "<html" not in content_lower and "<body" not in content_lower


def is_full_page(content: str) -> bool:
    """Check if response is full HTML page.

    Non-HTMX requests should return full pages.

    Args:
        content: Response content as string

    Returns:
        True if full page (has <html> tag)
    """
    return "<html" in content.lower()


def htmx_headers() -> dict:
    """Return headers that simulate an HTMX request.

    Returns:
        Dict with HX-Request header set
    """
    return {"HX-Request": "true"}


def assert_contains_text(content: str, text: str, case_sensitive: bool = False) -> None:
    """Assert response contains expected text.

    Args:
        content: Response content
        text: Expected text
        case_sensitive: Whether to match case (default False)

    Raises:
        AssertionError if text not found
    """
    if case_sensitive:
        assert text in content, f"Text '{text}' not found in response"
    else:
        assert text.lower() in content.lower(), f"Text '{text}' not found in response"


def assert_redirect(response, expected_location: str = None) -> None:
    """Assert response is a redirect.

    Args:
        response: TestClient response
        expected_location: Optional expected redirect location

    Raises:
        AssertionError if not a redirect or wrong location
    """
    assert response.status_code in [301, 302, 303, 307, 308], (
        f"Expected redirect, got {response.status_code}"
    )
    if expected_location:
        location = response.headers.get("location", "")
        assert expected_location in location, (
            f"Expected redirect to '{expected_location}', got '{location}'"
        )


def assert_status_ok(response) -> None:
    """Assert response has 2xx status code.

    Args:
        response: TestClient response

    Raises:
        AssertionError if not 2xx
    """
    assert 200 <= response.status_code < 300, (
        f"Expected 2xx status, got {response.status_code}"
    )


def assert_unauthorized(response) -> None:
    """Assert response is unauthorized (401).

    Args:
        response: TestClient response

    Raises:
        AssertionError if not 401
    """
    assert response.status_code == 401, (
        f"Expected 401 Unauthorized, got {response.status_code}"
    )


def assert_forbidden(response) -> None:
    """Assert response is forbidden (401 or 403).

    Note: Our app returns 401 for both unauthenticated and unauthorized.

    Args:
        response: TestClient response

    Raises:
        AssertionError if not 401/403
    """
    assert response.status_code in [401, 403], (
        f"Expected 401/403 Forbidden, got {response.status_code}"
    )


def assert_not_found(response) -> None:
    """Assert response is not found (404).

    Args:
        response: TestClient response

    Raises:
        AssertionError if not 404
    """
    assert response.status_code == 404, (
        f"Expected 404 Not Found, got {response.status_code}"
    )
