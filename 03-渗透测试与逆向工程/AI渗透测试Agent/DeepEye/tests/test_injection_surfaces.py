"""Tests for multi-surface injection helper."""
import sys
from pathlib import Path
from unittest.mock import MagicMock, call

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from core.injection_surfaces import Surface, extract_surfaces, inject, surfaces_for_injection_checks


def test_extract_query_params():
    s = extract_surfaces("https://x.com/a?b=1&c=2", {})
    names = {n for n, _ in s[Surface.QUERY]}
    assert names == {"b", "c"}


def test_extract_form_post():
    s = extract_surfaces(
        "https://x.com/form",
        {
            "forms": [
                {
                    "action": "/form",
                    "method": "POST",
                    "inputs": [{"name": "q", "type": "text", "value": ""}],
                }
            ]
        },
    )
    assert ("q", "") in s[Surface.FORM_POST]


def test_extract_path_segments():
    s = extract_surfaces("https://x.com/api/users/123/orders/45", {})
    vals = [v for _, v in s[Surface.PATH_SEGMENT]]
    assert "123" in vals and "45" in vals


def test_inject_query():
    hc = MagicMock()
    inject(
        "https://x.com/a?b=1&c=2",
        {},
        Surface.QUERY,
        "b",
        "PAYLOAD",
        http_client=hc,
    )
    assert hc.get.called
    url = hc.get.call_args[0][0]
    assert "b=PAYLOAD" in url
    assert "c=2" in url


def test_inject_form_post():
    hc = MagicMock()
    ctx = {
        "forms": [
            {
                "action": "/login",
                "method": "POST",
                "inputs": [{"name": "q", "type": "text", "value": ""}],
            }
        ]
    }
    inject("https://x.com/form", ctx, Surface.FORM_POST, "q", "X", http_client=hc)
    assert hc.post.called
    kwargs = hc.post.call_args
    assert kwargs[1].get("data", {}).get("q") == "X" or (
        len(kwargs[0]) > 1 and kwargs[0][1].get("q") == "X"
    ) or kwargs.kwargs.get("data", {}).get("q") == "X"


def test_inject_json_body():
    hc = MagicMock()
    inject(
        "https://x.com/api",
        {"json_body": {"q": "old"}},
        Surface.JSON_BODY,
        "q",
        "X",
        http_client=hc,
    )
    assert hc.post.called
    kw = hc.post.call_args.kwargs
    assert kw.get("json", {}).get("q") == "X"


def test_openapi_query_stub_seeds_query_surface():
    s = extract_surfaces(
        "https://api.example.com/users",
        {"openapi_query_stub": "id=1&role=user", "query_params": ["filter"]},
    )
    names = {n for n, _ in s[Surface.QUERY]}
    assert "id" in names and "role" in names and "filter" in names


def test_json_params_from_openapi_context():
    s = extract_surfaces(
        "https://api.example.com/items",
        {"json_params": ["name", "price"]},
    )
    names = {n for n, _ in s[Surface.JSON_BODY]}
    assert "name" in names and "price" in names
