from datetime import datetime, timezone
from PIL import Image
import pytest
from fastapi import HTTPException
from starlette.requests import Request

import api.index as api_index


def _make_request(
    *,
    host: str = "localhost",
    scheme: str = "http",
    path: str = "/",
    method: str = "GET",
    query: str = "",
    headers: dict[str, str] | None = None,
) -> Request:
    port = 443 if scheme == "https" else 80
    request_headers = [(b"host", host.encode("utf-8"))]
    for key, value in (headers or {}).items():
        request_headers.append((key.lower().encode("utf-8"), value.encode("utf-8")))
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "scheme": scheme,
        "path": path,
        "raw_path": path.encode("utf-8"),
        "root_path": "",
        "query_string": query.encode("utf-8"),
        "headers": request_headers,
        "client": (host, 12345),
        "server": (host, port),
    }
    return Request(scope)


def test_root_returns_svg_and_cache_headers(monkeypatch: pytest.MonkeyPatch):
    captured: dict[str, str] = {}
    monkeypatch.setattr(api_index, "load_cached_svg", lambda *_args: None)
    monkeypatch.setattr(api_index, "save_cached_svg", lambda *_args: None)

    monkeypatch.setattr(
        api_index,
        "fetch_image",
        lambda _date_str: (Image.new("RGB", (8, 8), "white"), "PIKACHU"),
    )
    monkeypatch.setattr(api_index, "resize_for_ascii", lambda img: img)
    monkeypatch.setattr(api_index, "enhance_image", lambda img: img.convert("L"))
    monkeypatch.setattr(api_index, "image_to_ascii", lambda img: ["@@", "@@"])

    def fake_build_svg(
        _ascii_lines: list[str],
        _theme: dict[str, str],
        date_str: str,
        github_url: str,
        pokemon_name: str | None = None,
    ) -> str:
        captured["date_str"] = date_str
        captured["github_url"] = github_url
        captured["pokemon_name"] = pokemon_name or ""
        return "<svg>ok</svg>"

    monkeypatch.setattr(api_index, "build_svg", fake_build_svg)

    response = api_index.widget(
        _make_request(query="debug_date=2024-03-14"),
        theme=api_index.ThemeName.DARK,
    )

    assert response.status_code == 200
    assert response.body == b"<svg>ok</svg>"
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert response.headers["cache-control"] == "no-cache, max-age=0, must-revalidate"
    assert "etag" not in response.headers
    assert captured == {
        "date_str": "2024-03-14",
        "github_url": "https://github.com/lengweih/readme-pokemon-ascii",
        "pokemon_name": "PIKACHU",
    }


def test_widget_returns_cached_svg_without_rendering(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        api_index, "load_cached_svg", lambda *_args: "<svg>cached</svg>"
    )
    monkeypatch.setattr(
        api_index,
        "fetch_image",
        lambda _date_str: (_ for _ in ()).throw(AssertionError("should not render")),
    )

    response = api_index.widget(_make_request(), theme=api_index.ThemeName.DARK)

    assert response.body == b"<svg>cached</svg>"


def test_widget_rejects_remote_debug_date():
    with pytest.raises(HTTPException) as exc_info:
        api_index.widget(
            _make_request(
                host="example.com",
                scheme="https",
                query="debug_date=2024-03-14",
            ),
            theme=api_index.ThemeName.DARK,
        )

    assert exc_info.value.status_code == 400


def test_widget_rejects_invalid_debug_date():
    with pytest.raises(HTTPException) as exc_info:
        api_index.widget(
            _make_request(query="debug_date=not-a-date"),
            theme=api_index.ThemeName.DARK,
        )

    assert exc_info.value.status_code == 422


def test_prewarm_local_override_generates_both_themes(monkeypatch: pytest.MonkeyPatch):
    render_calls: list[tuple[str, api_index.ThemeName, str]] = []
    save_calls: list[tuple[str, str, str]] = []
    monkeypatch.setattr(api_index, "load_cached_svg", lambda *_args: None)
    monkeypatch.setattr(
        api_index,
        "_render_svg",
        lambda date_str, theme, github_url: (
            render_calls.append((date_str, theme, github_url))
            or f"<svg>{theme.value}</svg>",
            api_index.RenderStatus.SUCCESS,
        ),
    )
    monkeypatch.setattr(
        api_index,
        "save_cached_svg",
        lambda svg, date_str, theme: save_calls.append((svg, date_str, theme)) or None,
    )

    response = api_index.prewarm(
        _make_request(path="/api/internal/prewarm", query="date=2024-03-15")
    )

    assert response == {
        "date": "2024-03-15",
        "results": {"dark": "generated", "light": "generated"},
    }
    assert render_calls == [
        (
            "2024-03-15",
            api_index.ThemeName.DARK,
            "https://github.com/lengweih/readme-pokemon-ascii",
        ),
        (
            "2024-03-15",
            api_index.ThemeName.LIGHT,
            "https://github.com/lengweih/readme-pokemon-ascii",
        ),
    ]
    assert save_calls == [
        ("<svg>dark</svg>", "2024-03-15", "dark"),
        ("<svg>light</svg>", "2024-03-15", "light"),
    ]


def test_prewarm_uses_cached_svgs_when_available(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        api_index,
        "load_cached_svg",
        lambda _date_str, theme: f"<svg>{theme}</svg>",
    )
    monkeypatch.setattr(
        api_index,
        "_resolve_prewarm_date_str",
        lambda _request: "2024-03-15",
    )
    monkeypatch.setattr(
        api_index,
        "_render_svg",
        lambda *_args: (_ for _ in ()).throw(AssertionError("should not render")),
    )

    response = api_index.prewarm(_make_request(path="/api/internal/prewarm"))

    assert response == {
        "date": "2024-03-15",
        "results": {"dark": "cached", "light": "cached"},
    }


def test_prewarm_rejects_unauthorized_remote_requests():
    with pytest.raises(HTTPException) as exc_info:
        api_index.prewarm(
            _make_request(
                host="example.com",
                scheme="https",
                path="/api/internal/prewarm",
            )
        )

    assert exc_info.value.status_code == 401


def test_prewarm_allows_remote_requests_with_cron_secret(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv(api_index.CRON_SECRET_ENV_VAR, "secret-value")
    monkeypatch.setattr(
        api_index,
        "_resolve_prewarm_date_str",
        lambda _request: "2024-03-15",
    )
    monkeypatch.setattr(
        api_index,
        "load_cached_svg",
        lambda _date_str, theme: f"<svg>{theme}</svg>",
    )

    response = api_index.prewarm(
        _make_request(
            host="example.com",
            scheme="https",
            path="/api/internal/prewarm",
            headers={"authorization": "Bearer secret-value"},
        )
    )

    assert response == {
        "date": "2024-03-15",
        "results": {"dark": "cached", "light": "cached"},
    }


def test_widget_falls_back_when_image_fetch_fails(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(api_index, "load_cached_svg", lambda *_args: None)
    monkeypatch.setattr(api_index, "fetch_image", lambda _date_str: (None, None))

    response = api_index.widget(
        _make_request(query="debug_date=2024-03-14"),
        theme=api_index.ThemeName.LIGHT,
    )

    body = bytes(response.body).decode("utf-8")
    assert "image unavailable" in body
    assert "2024-03-14" in body
    assert 'width="308"' in body
    assert 'height="321"' in body


def test_widget_falls_back_when_pipeline_raises(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(api_index, "load_cached_svg", lambda *_args: None)
    monkeypatch.setattr(api_index, "save_cached_svg", lambda *_args: None)
    monkeypatch.setattr(
        api_index,
        "fetch_image",
        lambda _date_str: (Image.new("RGB", (8, 8), "white"), "PIKACHU"),
    )
    monkeypatch.setattr(
        api_index,
        "resize_for_ascii",
        lambda _img: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = api_index.widget(
        _make_request(query="debug_date=2024-03-14"),
        theme=api_index.ThemeName.DARK,
    )

    assert "image unavailable" in bytes(response.body).decode("utf-8")


def test_app_routes_expose_expected_paths():
    paths = {
        path
        for route in api_index.app.routes
        if (path := getattr(route, "path", None)) is not None
    }

    assert "/" in paths
    assert "/api/internal/prewarm" in paths
