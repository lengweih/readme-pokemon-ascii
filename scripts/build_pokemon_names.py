#!/usr/bin/env python3
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen

API_URL = "https://pokeapi.co/api/v2/pokemon-species?limit=2000"
USER_AGENT = "readme-pokemon-ascii/1.0"
ID_PATTERN = re.compile(r"/pokemon-species/(\d+)/?$")
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "core" / "pokemon_names.txt"


def main() -> None:
    request = Request(API_URL, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        payload = json.load(response)

    names_by_id: dict[int, str] = {}
    for result in payload["results"]:
        match = ID_PATTERN.search(result["url"])
        if match is None:
            raise RuntimeError(f"Could not parse Pokemon id from {result['url']}")
        names_by_id[int(match.group(1))] = result["name"]

    highest_id = max(names_by_id)
    lines = [names_by_id[number] for number in range(1, highest_id + 1)]
    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
