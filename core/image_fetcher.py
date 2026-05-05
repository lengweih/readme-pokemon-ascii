import hashlib
import random
from datetime import date
from io import BytesIO

from PIL import Image
import requests

from core.logging_config import get_logger
from core.pokemon_names import POKEMON_NAMES, get_pokemon_name

MAX_POKEMON = len(POKEMON_NAMES)
SHUFFLE_EPOCH = date(2026, 1, 1)
SHUFFLE_SEED = "readme-pokemon-ascii-v1"
ARTWORK_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{number}.png"
FETCH_TIMEOUT = 8
TARGET_WIDTH = 80
MIN_HEIGHT = 10
MAX_HEIGHT = 35
ASCII_ASPECT_RATIO = 0.45
USER_AGENT = "readme-pokemon-ascii/1.0"

logger = get_logger(__name__)


def _build_pokemon_cycle(
    max_pokemon: int = MAX_POKEMON,
    seed: str = SHUFFLE_SEED,
) -> tuple[int, ...]:
    """Create one deterministic shuffled cycle of Pokemon numbers."""
    numbers = list(range(1, max_pokemon + 1))
    seed_int = int(hashlib.sha256(seed.encode("utf-8")).hexdigest(), 16)
    rng = random.Random(seed_int)
    rng.shuffle(numbers)
    return tuple(numbers)


POKEMON_CYCLE = _build_pokemon_cycle()


def pick_pokemon_number(date_str: str) -> int:
    """Pick a Pokemon from a deterministic no-repeat cycle until it wraps."""
    target_date = date.fromisoformat(date_str)
    day_index = (target_date - SHUFFLE_EPOCH).days
    cycle_index = day_index % len(POKEMON_CYCLE)
    return POKEMON_CYCLE[cycle_index]


def fetch_image(date_str: str) -> tuple[Image.Image | None, str | None]:
    """Return today's artwork image plus a locally stored display name."""
    number = pick_pokemon_number(date_str)
    name = get_pokemon_name(number)
    if name is None:
        logger.warning("[names] missing local name for pokemon=%s", number)

    url = ARTWORK_URL.format(number=number)
    logger.info(
        "[fetch] artwork date=%s pokemon=%s name=%s url=%s",
        date_str,
        number,
        name,
        url,
    )

    try:
        response = requests.get(
            url,
            timeout=FETCH_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()

        img = Image.open(BytesIO(response.content)).convert("RGBA")

        background = Image.new("RGBA", img.size, (255, 255, 255, 255))
        background.paste(img, mask=img.split()[3])
        img = background.convert("RGB")
        return img, name

    except (requests.RequestException, OSError, ValueError):
        logger.exception("[fetch] image failed date=%s pokemon=%s", date_str, number)
        return None, None


def resize_for_ascii(img: Image.Image) -> Image.Image:
    """
    Resize image to ASCII grid dimensions.
    Corrects for monospace character aspect ratio (chars are ~2x taller than wide).
    Caps height to prevent portrait images producing a wall of text.
    """
    orig_w, orig_h = img.size
    scale = TARGET_WIDTH / orig_w
    new_rows = int(orig_h * scale * ASCII_ASPECT_RATIO)
    new_rows = max(MIN_HEIGHT, min(new_rows, MAX_HEIGHT))

    return img.resize((TARGET_WIDTH, new_rows), Image.Resampling.LANCZOS)
