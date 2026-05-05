from datetime import date
from io import BytesIO

from PIL import Image
import pytest
import requests

import core.image_fetcher as image_fetcher


class FakeResponse:
    def __init__(
        self,
        *,
        content: bytes = b"",
        status_code: int = 200,
    ) -> None:
        self.content = content
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


def _sample_png_bytes() -> bytes:
    image = Image.new("RGBA", (4, 4), (255, 0, 0, 255))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_pick_pokemon_number_is_deterministic():
    first = image_fetcher.pick_pokemon_number("2024-01-01")
    second = image_fetcher.pick_pokemon_number("2024-01-01")
    third = image_fetcher.pick_pokemon_number("2024-01-02")

    assert first == second
    assert first != third
    assert 1 <= first <= image_fetcher.MAX_POKEMON


def test_build_pokemon_cycle_is_stable_for_a_seed():
    cycle1 = image_fetcher._build_pokemon_cycle(5, "seed-one")
    cycle2 = image_fetcher._build_pokemon_cycle(5, "seed-one")

    assert cycle1 == cycle2
    assert set(cycle1) == {1, 2, 3, 4, 5}


def test_pick_pokemon_number_uses_cycle_without_repeats_until_wrap(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(image_fetcher, "SHUFFLE_EPOCH", date(2024, 1, 1))
    monkeypatch.setattr(image_fetcher, "POKEMON_CYCLE", (7, 3, 9))

    assert image_fetcher.pick_pokemon_number("2024-01-01") == 7
    assert image_fetcher.pick_pokemon_number("2024-01-02") == 3
    assert image_fetcher.pick_pokemon_number("2024-01-03") == 9
    assert image_fetcher.pick_pokemon_number("2024-01-04") == 7


def test_resize_for_ascii_uses_target_width_and_caps_height():
    img = Image.new("RGB", (100, 2000))

    resized = image_fetcher.resize_for_ascii(img)

    assert resized.width == image_fetcher.TARGET_WIDTH
    assert image_fetcher.MIN_HEIGHT <= resized.height <= image_fetcher.MAX_HEIGHT


def test_local_name_map_contains_known_entries():
    assert image_fetcher.get_pokemon_name(1) == "BULBASAUR"
    assert image_fetcher.get_pokemon_name(25) == "PIKACHU"
    assert image_fetcher.get_pokemon_name(image_fetcher.MAX_POKEMON + 1) is None


def test_fetch_image_uses_local_name_map(monkeypatch: pytest.MonkeyPatch):
    calls: list[str] = []

    def fake_get(url: str, timeout: int, headers: dict[str, str]) -> FakeResponse:
        calls.append(url)
        assert timeout == image_fetcher.FETCH_TIMEOUT
        assert headers["User-Agent"] == image_fetcher.USER_AGENT
        return FakeResponse(content=_sample_png_bytes())

    monkeypatch.setattr(image_fetcher.requests, "get", fake_get)
    monkeypatch.setattr(image_fetcher, "get_pokemon_name", lambda _number: "PIKACHU")

    img, name = image_fetcher.fetch_image("2024-01-01")

    assert name == "PIKACHU"
    assert img is not None
    assert img.mode == "RGB"
    assert img.size == (4, 4)
    assert len(calls) == 1


def test_fetch_image_returns_image_without_name_when_local_name_is_missing(
    monkeypatch: pytest.MonkeyPatch,
):
    def fake_get(url: str, timeout: int, headers: dict[str, str]) -> FakeResponse:
        return FakeResponse(content=_sample_png_bytes())

    monkeypatch.setattr(image_fetcher.requests, "get", fake_get)
    monkeypatch.setattr(image_fetcher, "get_pokemon_name", lambda _number: None)

    img, name = image_fetcher.fetch_image("2024-01-03")

    assert img is not None
    assert name is None


def test_fetch_image_returns_none_when_artwork_fetch_fails(
    monkeypatch: pytest.MonkeyPatch,
):
    def fake_get(url: str, timeout: int, headers: dict[str, str]) -> FakeResponse:
        return FakeResponse(status_code=404)

    monkeypatch.setattr(image_fetcher.requests, "get", fake_get)
    monkeypatch.setattr(image_fetcher, "get_pokemon_name", lambda _number: "PIKACHU")

    img, name = image_fetcher.fetch_image("2024-01-04")

    assert img is None
    assert name is None
