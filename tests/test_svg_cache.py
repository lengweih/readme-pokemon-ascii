import core.svg_cache as svg_cache
from vercel.blob import BlobNotFoundError


class FakeBlobResult:
    def __init__(self, content: bytes, status_code: int = 200):
        self.content = content
        self.status_code = status_code


class FakeBlobClient:
    def __init__(
        self,
        *,
        get_result: FakeBlobResult | None = None,
        get_error: Exception | None = None,
    ):
        self.get_result = get_result
        self.get_error = get_error
        self.get_calls: list[tuple[str, str]] = []
        self.put_calls: list[tuple[str, bytes, dict[str, object]]] = []

    def get(self, url_or_path: str, *, access: str = "public", **_kwargs):
        self.get_calls.append((url_or_path, access))
        if self.get_error is not None:
            raise self.get_error
        return self.get_result

    def put(self, path: str, body: bytes, **kwargs) -> None:
        self.put_calls.append((path, body, kwargs))


def test_cache_filename_uses_date_first_readable_filename(monkeypatch):
    monkeypatch.setattr(svg_cache, "pick_pokemon_number", lambda _date_str: 25)
    monkeypatch.setattr(svg_cache, "get_pokemon_name", lambda _number: "PIKACHU")

    filename = svg_cache._cache_filename("2026-04-30", "dark")

    assert filename == "2026-04-30_025_pikachu_dark.svg"


def test_blob_svg_pathname_uses_cache_prefix(monkeypatch):
    monkeypatch.setattr(svg_cache, "pick_pokemon_number", lambda _date_str: 25)
    monkeypatch.setattr(svg_cache, "get_pokemon_name", lambda _number: "PIKACHU")

    pathname = svg_cache._blob_svg_pathname("2026-04-30", "dark")

    assert pathname == "daily-svg-cache/2026-04-30_025_pikachu_dark.svg"


def test_load_cached_svg_returns_none_without_blob_client(monkeypatch):
    monkeypatch.setattr(svg_cache, "_get_blob_client", lambda: None)

    assert svg_cache.load_cached_svg("2026-04-30", "dark") is None


def test_save_cached_svg_is_noop_without_blob_client(monkeypatch):
    monkeypatch.setattr(svg_cache, "_get_blob_client", lambda: None)

    assert svg_cache.save_cached_svg("<svg>blob</svg>", "2026-04-30", "dark") is None


def test_load_cached_svg_reads_from_blob_when_configured(monkeypatch):
    fake_client = FakeBlobClient(get_result=FakeBlobResult(b"<svg>blob</svg>"))
    monkeypatch.setattr(svg_cache, "_get_blob_client", lambda: fake_client)
    monkeypatch.setattr(svg_cache, "pick_pokemon_number", lambda _date_str: 25)
    monkeypatch.setattr(svg_cache, "get_pokemon_name", lambda _number: "PIKACHU")

    svg = svg_cache.load_cached_svg("2026-04-30", "dark")

    assert svg == "<svg>blob</svg>"
    assert fake_client.get_calls == [
        ("daily-svg-cache/2026-04-30_025_pikachu_dark.svg", "private")
    ]


def test_load_cached_svg_returns_none_for_missing_blob(monkeypatch):
    fake_client = FakeBlobClient(get_error=BlobNotFoundError())
    monkeypatch.setattr(svg_cache, "_get_blob_client", lambda: fake_client)
    monkeypatch.setattr(svg_cache, "pick_pokemon_number", lambda _date_str: 25)
    monkeypatch.setattr(svg_cache, "get_pokemon_name", lambda _number: "PIKACHU")

    svg = svg_cache.load_cached_svg("2026-04-30", "dark")

    assert svg is None
    assert fake_client.get_calls == [
        ("daily-svg-cache/2026-04-30_025_pikachu_dark.svg", "private")
    ]


def test_save_cached_svg_writes_to_blob_when_configured(monkeypatch):
    fake_client = FakeBlobClient()
    monkeypatch.setattr(svg_cache, "_get_blob_client", lambda: fake_client)
    monkeypatch.setattr(svg_cache, "pick_pokemon_number", lambda _date_str: 25)
    monkeypatch.setattr(svg_cache, "get_pokemon_name", lambda _number: "PIKACHU")

    assert svg_cache.save_cached_svg("<svg>blob</svg>", "2026-04-30", "dark") is None

    assert fake_client.put_calls == [
        (
            "daily-svg-cache/2026-04-30_025_pikachu_dark.svg",
            b"<svg>blob</svg>",
            {
                "access": "private",
                "content_type": "image/svg+xml",
                "overwrite": True,
            },
        )
    ]
