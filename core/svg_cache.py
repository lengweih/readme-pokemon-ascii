import os

from vercel.blob import BlobClient, BlobNotFoundError

from core.image_fetcher import pick_pokemon_number
from core.logging_config import get_logger
from core.pokemon_names import get_pokemon_name

SVG_CACHE = "{date}_{number}_{name}_{theme}.svg"
BLOB_TOKEN_ENV_VAR = "BLOB_READ_WRITE_TOKEN"
BLOB_PREFIX = "daily-svg-cache"

logger = get_logger(__name__)


def _cache_name_parts(date_str: str) -> tuple[str, str]:
    number = pick_pokemon_number(date_str)
    name = (get_pokemon_name(number) or "unknown").lower()
    return f"{number:03d}", name


def _cache_filename(date_str: str, theme: str) -> str:
    number, name = _cache_name_parts(date_str)
    return SVG_CACHE.format(
        date=date_str,
        number=number,
        name=name,
        theme=theme,
    )


def _blob_svg_pathname(date_str: str, theme: str) -> str:
    return f"{BLOB_PREFIX}/{_cache_filename(date_str, theme)}"


def _get_blob_client() -> BlobClient | None:
    token = os.environ.get(BLOB_TOKEN_ENV_VAR, "").strip()
    if not token:
        return None
    return BlobClient(token=token)


def load_cached_svg(date_str: str, theme: str) -> str | None:
    client = _get_blob_client()
    if client is None:
        return None

    pathname = _blob_svg_pathname(date_str, theme)
    try:
        result = client.get(pathname, access="private")
        if result is None or result.status_code != 200:
            return None
        return result.content.decode("utf-8")
    except BlobNotFoundError:
        return None
    except Exception:
        logger.warning(
            "[svg-cache] blob read failed date=%s theme=%s path=%s",
            date_str,
            theme,
            pathname,
            exc_info=True,
        )
        return None


def save_cached_svg(svg: str, date_str: str, theme: str) -> None:
    client = _get_blob_client()
    if client is None:
        logger.info("[svg-cache] cache disabled date=%s theme=%s", date_str, theme)
        return

    pathname = _blob_svg_pathname(date_str, theme)
    try:
        client.put(
            pathname,
            svg.encode("utf-8"),
            access="private",
            content_type="image/svg+xml",
            overwrite=True,
        )
        logger.info("[svg-cache] saved date=%s theme=%s", date_str, theme)
    except Exception:
        logger.warning(
            "[svg-cache] save failed date=%s theme=%s path=%s",
            date_str,
            theme,
            pathname,
            exc_info=True,
        )
