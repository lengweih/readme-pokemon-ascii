from pathlib import Path

NAMES_PATH = Path(__file__).with_name("pokemon_names.txt")


def _load_pokemon_names() -> tuple[str, ...]:
    lines = NAMES_PATH.read_text(encoding="utf-8").splitlines()
    return tuple(line.strip().upper() for line in lines if line.strip())


POKEMON_NAMES = _load_pokemon_names()


def get_pokemon_name(number: int) -> str | None:
    if 1 <= number <= len(POKEMON_NAMES):
        return POKEMON_NAMES[number - 1]
    return None
