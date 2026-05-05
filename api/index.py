import os
from enum import Enum, auto
from datetime import date, datetime, timedelta, timezone
from typing import TypedDict

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import Response

from core.ascii_converter import center_blank_rows, image_to_ascii
from core.image_fetcher import fetch_image, resize_for_ascii
from core.logging_config import get_logger
from core.pil_pipeline import enhance_image
from core.svg_builder import build_fallback_svg, build_svg
from core.svg_cache import load_cached_svg, save_cached_svg
from core.theme import ThemeName, get_theme

logger = get_logger(__name__)
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
GITHUB_REPO_URL = "https://github.com/lengweih/readme-pokemon-ascii"
CRON_SECRET_ENV_VAR = "CRON_SECRET"
FALLBACK_MESSAGE = "image unavailable"


class RenderStatus(Enum):
    SUCCESS = auto()
    ERROR = auto()


class SvgResultStatus(str, Enum):
    CACHED = "cached"
    GENERATED = "generated"
    FALLBACK = "fallback"


class PrewarmResponse(TypedDict):
    date: str
    results: dict[str, str]


app = FastAPI(
    title="Daily Pokemon ASCII",
    description="Returns a daily Pokemon ASCII art SVG card for embedding in GitHub READMEs.",
    version="1.0.0",
)


def _is_local_request(request: Request) -> bool:
    host = request.url.hostname or ""
    return host in LOCAL_HOSTS


def _require_local_request(request: Request, action: str) -> None:
    if not _is_local_request(request):
        raise HTTPException(
            status_code=400,
            detail=f"{action} is only available for local development",
        )


def _is_authorized_cron_request(request: Request) -> bool:
    if _is_local_request(request):
        return True

    secret = os.environ.get(CRON_SECRET_ENV_VAR, "").strip()
    auth_header = request.headers.get("authorization", "")
    return bool(secret) and auth_header == f"Bearer {secret}"


def _require_authorized_cron_request(request: Request) -> None:
    if not _is_authorized_cron_request(request):
        raise HTTPException(status_code=401, detail="Unauthorized")


def _parse_iso_date_param(value: str, param_name: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"{param_name} must use YYYY-MM-DD format",
        ) from exc


def _resolve_date_str(request: Request) -> str:
    debug_date = request.query_params.get("debug_date")
    if not debug_date:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    _require_local_request(request, "debug_date")
    return _parse_iso_date_param(debug_date, "debug_date")


def _resolve_prewarm_date_str(request: Request) -> str:
    requested_date = request.query_params.get("date")
    if requested_date is not None:
        _require_local_request(request, "prewarm date override")
        return _parse_iso_date_param(requested_date, "date")

    return (datetime.now(timezone.utc).date() + timedelta(days=1)).isoformat()


def _render_svg(
    date_str: str,
    theme: ThemeName,
    github_url: str,
) -> tuple[str, RenderStatus]:
    theme_colors = get_theme(theme)
    img, pokemon_name = fetch_image(date_str)

    if img is None:
        logger.warning(
            "[widget] fetch failed; serving fallback date=%s theme=%s",
            date_str,
            theme.value,
        )
        return (
            build_fallback_svg(
                theme_colors,
                date_str,
                github_url,
                message=FALLBACK_MESSAGE,
            ),
            RenderStatus.ERROR,
        )

    try:
        img = resize_for_ascii(img)
        img = enhance_image(img)
        ascii_lines = center_blank_rows(image_to_ascii(img))
        cols = len(ascii_lines[0]) if ascii_lines else 0
        logger.info(
            "[widget] grid=%sr x %sc pokemon=%s",
            len(ascii_lines),
            cols,
            pokemon_name,
        )
        return (
            build_svg(
                ascii_lines,
                theme_colors,
                date_str,
                github_url,
                pokemon_name,
            ),
            RenderStatus.SUCCESS,
        )
    except Exception:
        logger.exception(
            "[widget] image pipeline error date=%s theme=%s",
            date_str,
            theme.value,
        )
        return (
            build_fallback_svg(
                theme_colors,
                date_str,
                github_url,
                message=FALLBACK_MESSAGE,
            ),
            RenderStatus.ERROR,
        )


def _get_or_render_svg(
    date_str: str,
    theme: ThemeName,
) -> tuple[str, SvgResultStatus]:
    cached_svg = load_cached_svg(date_str, theme.value)
    if cached_svg is not None:
        logger.info("[svg-cache] hit date=%s theme=%s", date_str, theme.value)
        return cached_svg, SvgResultStatus.CACHED

    logger.info("[svg-cache] miss date=%s theme=%s", date_str, theme.value)
    svg, render_status = _render_svg(date_str, theme, GITHUB_REPO_URL)
    if render_status is RenderStatus.SUCCESS:
        save_cached_svg(svg, date_str, theme.value)
        return svg, SvgResultStatus.GENERATED

    return svg, SvgResultStatus.FALLBACK


@app.get(
    "/",
    response_class=Response,
    responses={200: {"content": {"image/svg+xml": {}}}},
    summary="Get today's Pokemon ASCII art",
    description="Returns an SVG card with Pokemon ASCII art. Changes daily. Embed in your README.",
    name="widget",
)
def widget(
    request: Request,
    theme: ThemeName = Query(
        default=ThemeName.DARK,
        description="dark or light",
    ),
) -> Response:
    date_str = _resolve_date_str(request)
    logger.info(
        "[widget] date=%s theme=%s debug=%s",
        date_str,
        theme.value,
        "yes" if "debug_date" in request.query_params else "no",
    )

    svg, _status = _get_or_render_svg(date_str, theme)

    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "no-cache, max-age=0, must-revalidate",
            "Vary": "Accept-Encoding",
            "X-Content-Type-Options": "nosniff",
        },
    )


@app.get("/api/internal/prewarm", include_in_schema=False)
def prewarm(request: Request) -> PrewarmResponse:
    _require_authorized_cron_request(request)
    date_str = _resolve_prewarm_date_str(request)
    results: dict[str, str] = {}

    logger.info("[prewarm] date=%s", date_str)

    for theme in (ThemeName.DARK, ThemeName.LIGHT):
        _svg, status = _get_or_render_svg(date_str, theme)
        results[theme.value] = status.value
        logger.info(
            "[prewarm] date=%s theme=%s status=%s", date_str, theme.value, status.value
        )

    return {"date": date_str, "results": results}
