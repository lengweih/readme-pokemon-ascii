# Daily Pokemon ASCII

A self-hosted GitHub README widget that picks one Pokemon per UTC day, converts its official artwork into ASCII, and serves the result as an SVG.

Use the hosted widget in a README like this:

```markdown
[![Daily Pokemon ASCII](https://readme-pokemon-ascii.vercel.app/)](https://github.com/lengweih/readme-pokemon-ascii)
```

If you want a centered version, you can also use HTML:

```html
<p align="center">
  <a href="https://readme-pokemon-ascii.vercel.app/">
    <img src="https://readme-pokemon-ascii.vercel.app/" alt="Daily Pokemon ASCII" />
  </a>
</p>
```

If you want to inspect the hosted SVG page itself, open `https://readme-pokemon-ascii.vercel.app/` directly in a browser.

## Endpoint

The widget is served from `/`.

- `GET /` returns the dark theme by default.
- `GET /?theme=light` returns the light theme.
- `GET /?theme=dark` returns the same default dark theme explicitly.
- `/docs` serves the built-in Swagger UI.
- `/api/internal/prewarm` exists for the daily cron prewarm and is not shown in the docs.

For local development only, you can also pass `debug_date=YYYY-MM-DD` to preview a specific day:

```text
http://127.0.0.1:8000/?theme=dark&debug_date=2024-03-14
```

`debug_date` is rejected on non-local hosts.

## How It Works

1. The app maps the current UTC date into a deterministic shuffled Pokemon cycle.
2. It fetches that Pokemon's official artwork and looks up the display name from a checked-in local file.
3. Pillow resizes and enhances the image for monospace rendering.
4. The processed pixels are mapped to an ASCII ramp.
5. Successful SVG renders are cached per day and theme when Vercel Blob is configured. Local development skips SVG caching and simply rerenders on each request.

The same date and theme always produce the same SVG output, and Pokemon do not repeat until the cycle wraps.

## Project Layout

```text
.
├── api/
│   └── index.py
├── core/
│   ├── ascii_converter.py
│   ├── image_fetcher.py
│   ├── logging_config.py
│   ├── pokemon_names.py
│   ├── pokemon_names.txt
│   ├── pil_pipeline.py
│   ├── svg_builder.py
│   ├── svg_cache.py
│   └── theme.py
├── scripts/
│   └── build_pokemon_names.py
├── tests/
│   ├── test_api.py
│   ├── test_ascii.py
│   ├── test_image.py
│   ├── test_svg.py
│   └── test_svg_cache.py
├── .python-version
├── pytest.ini
├── requirements.txt
├── requirements-dev.txt
└── vercel.json
```

## Local Development

Create a virtualenv, install dependencies, and run FastAPI with Uvicorn:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
uvicorn api.index:app --reload --port 8000
```

Then open one of these URLs:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/?theme=light
http://127.0.0.1:8000/docs
```

## Refreshing Pokemon Names

If new Pokemon are added officially, regenerate [core/pokemon_names.txt](/Users/ricky/Workspace/python/readme-pokemon-ascii/core/pokemon_names.txt) from PokeAPI's species list with:

```bash
python3 scripts/build_pokemon_names.py
```

That script fetches `pokemon-species?limit=2000`, extracts the national Pokedex IDs `1..N`, and rewrites the checked-in names file. After regenerating it, `MAX_POKEMON` updates automatically because it is derived from the file length.

## Testing

Run the suite with:

```bash
.venv/bin/pytest -q
```

The tests cover:

- ASCII conversion behavior
- Pokemon selection, local name lookup, and artwork fetching
- SVG escaping and fallback rendering
- API route behavior, headers, and debug-date restrictions

## Deployment

This repo is set up for Vercel. `vercel.json` routes requests to `api/index.py`, `.python-version` pins the Python runtime, `requirements.txt` lists runtime dependencies, and `requirements-dev.txt` adds local development tools. Create a Vercel Blob store in the project Storage tab, choose private access, and include the generated `BLOB_READ_WRITE_TOKEN` in your production environment so daily SVGs are cached persistently across function instances. Without that token, the app still works normally but skips SVG caching.

To prewarm the next day's SVGs before the UTC rollover, also add a `CRON_SECRET` environment variable in Vercel. The configured cron job calls `/api/internal/prewarm` once per day at `23:00 UTC` and pre-generates both dark and light variants for the next UTC date. On Hobby, Vercel's timing precision is hourly, so the job may run anytime between `23:00` and `23:59 UTC`, which is still early enough for this prewarm use case.

```bash
vercel --prod
```

After deployment, the widget URL is:

```text
https://your-project.vercel.app/
```

## Notes

- The response is served as `image/svg+xml`.
- Cache headers are tuned for README image proxying and CDN revalidation.
- If the image pipeline fails, the API returns a compact fallback SVG instead of an error page.


## Credits

This project relies on a few third-party resources:

- [PokéAPI](https://pokeapi.co/) for the Pokémon species list used to generate [core/pokemon_names.txt](/Users/ricky/Workspace/python/readme-pokemon-ascii/core/pokemon_names.txt).
- [PokéAPI sprites repository](https://github.com/PokeAPI/sprites) for the official artwork images served from GitHub.


## Disclaimer

Pokémon is a trademark of The Pokémon Company International, Inc. This application is a non-commercial, fan-made project created for personal, educational use. It is not affiliated with, endorsed, sponsored, or supported by The Pokémon Company, Nintendo, or Game Freak in any way. All Pokémon character names, images, and related content are owned by their respective copyright holders.
