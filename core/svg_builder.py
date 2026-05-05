import html

from core.theme import Theme

CARD_PADDING = 10
CHAR_W = 3.6
CHAR_H = 7
TITLE_H = 36
FOOTER_H = 20
FONT_SIZE = 6
DEFAULT_ASCII_COLS = 80
DEFAULT_ASCII_ROWS = 35
ACCENT_X = CARD_PADDING
ACCENT_Y = 6
ACCENT_W = 4
ACCENT_H = TITLE_H - 12
TEXT_X = ACCENT_X + ACCENT_W + 8
TITLE_Y = 16
SUBTITLE_Y = 28
SUBTITLE_TEXT = "New Pokémon daily at 00:00 UTC"


def _card_dimensions(cols: int, rows: int) -> tuple[int, int]:
    inner_w = cols * CHAR_W
    inner_h = rows * CHAR_H + TITLE_H + FOOTER_H
    card_w = min(inner_w + CARD_PADDING * 2, 350)
    card_h = inner_h + CARD_PADDING * 2
    return int(card_w), int(card_h)


def build_svg(
    ascii_lines: list[str],
    theme: Theme,
    date_str: str,
    github_url: str,
    pokemon_name: str | None = None,
) -> str:
    if not ascii_lines:
        ascii_lines = ["[no image available today]"]

    safe_date = html.escape(date_str)
    safe_name = html.escape(pokemon_name) if pokemon_name else ""

    cols = max(len(line) for line in ascii_lines)
    rows = len(ascii_lines)
    card_w, card_h = _card_dimensions(cols, rows)

    lines_svg: list[str] = []
    for i, line in enumerate(ascii_lines):
        y = CARD_PADDING + TITLE_H + (i + 1) * CHAR_H
        escaped = html.escape(line)
        lines_svg.append(
            f'<text x="{CARD_PADDING}" y="{y}" '
            + "font-family=\"'Courier New', Courier, monospace\" "
            + f'font-size="{FONT_SIZE}" fill="{theme["text"]}" '
            + f'xml:space="preserve">{escaped}</text>'
        )

    ascii_block = "\n    ".join(lines_svg)

    footer_y = CARD_PADDING + TITLE_H + rows * CHAR_H + FOOTER_H - 2

    footer_text = (
        f'<tspan fill="{theme["text"]}">A wild </tspan>'
        f'<tspan fill="{theme["title"]}">{safe_name}</tspan>'
        f'<tspan fill="{theme["text"]}"> appeared!</tspan>'
        if pokemon_name
        else ""
    )

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="{card_w}"
     height="{card_h}"
     viewBox="0 0 {card_w} {card_h}"
     role="img"
     aria-label="Daily Pokémon ASCII art widget for {safe_date}">

  <title>Daily Pokémon ASCII — {safe_date}</title>
  <desc>ASCII art image generated daily from a deterministic shuffled Pokémon cycle.</desc>

  <!-- 1. Card background fill — no stroke so border is never clipped -->
  <rect x="0" y="0"
        width="{card_w}" height="{card_h}"
        rx="6"
        fill="{theme['card_bg']}"/>

  <!-- 2. Title bar — drawn after card bg so corners are naturally hidden -->
  <rect x="0" y="0"
        width="{card_w}" height="{TITLE_H}"
        fill="{theme['bg']}"/>

  <!-- 3. Border drawn last so it always sits on top, never clipped -->
  <rect x="0" y="0"
        width="{card_w}" height="{card_h}"
        rx="6"
        fill="none"
        stroke="{theme['border']}"
        stroke-width="0.5"/>

  <a href="{html.escape(github_url)}" target="_blank" rel="noopener noreferrer" style="cursor: pointer;">

    <rect x="0" y="0"
          width="{card_w}" height="{card_h}"
          rx="6"
          fill="transparent"/>

    <!-- Header accent -->
    <rect x="{ACCENT_X}" y="{ACCENT_Y}"
          width="{ACCENT_W}" height="{ACCENT_H}"
          rx="1.5"
          fill="{theme['title']}"/>

    <!-- Title bar label -->
    <text x="{TEXT_X}" y="{TITLE_Y}"
          font-family="'Segoe UI', system-ui, sans-serif"
          font-size="10" font-weight="600"
          fill="{theme['title']}">Daily Pokémon ASCII · {safe_date}</text>

    <text x="{TEXT_X}" y="{SUBTITLE_Y}"
          font-family="'Segoe UI', system-ui, sans-serif"
          font-size="8" font-weight="500"
          fill="{theme['text']}" fill-opacity="0.7">{SUBTITLE_TEXT}</text>

    <!-- ASCII art rows -->
    {ascii_block}

    <!-- Footer -->
    <text x="{card_w // 2}" y="{footer_y}"
          text-anchor="middle"
          font-family="'Segoe UI', system-ui, sans-serif"
          font-size="10" font-weight="600">
      {footer_text}
    </text>

  </a>
</svg>"""

    return svg


def build_fallback_svg(
    theme: Theme,
    date_str: str,
    github_url: str,
    message: str = "image unavailable",
    cols: int = DEFAULT_ASCII_COLS,
    rows: int = DEFAULT_ASCII_ROWS,
) -> str:
    safe_date = html.escape(date_str)
    safe_message = html.escape(message)
    card_w, card_h = _card_dimensions(cols, rows)
    content_top = CARD_PADDING + TITLE_H
    content_height = rows * CHAR_H
    message_y = content_top + content_height // 2

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="{card_w}"
     height="{card_h}"
     viewBox="0 0 {card_w} {card_h}"
     role="img"
     aria-label="Daily Pokémon ASCII art widget unavailable for {safe_date}">

  <title>Daily Pokémon ASCII — unavailable</title>
  <desc>Fallback card shown when the daily Pokémon image cannot be rendered.</desc>

  <rect x="0" y="0"
        width="{card_w}" height="{card_h}"
        rx="6"
        fill="{theme['card_bg']}"/>

  <rect x="0" y="0"
        width="{card_w}" height="{TITLE_H}"
        fill="{theme['bg']}"/>

  <rect x="0" y="0"
        width="{card_w}" height="{card_h}"
        rx="6"
        fill="none"
        stroke="{theme['border']}"
        stroke-width="0.5"/>

  <a href="{html.escape(github_url)}" target="_blank" rel="noopener noreferrer" style="cursor: pointer;">

    <rect x="0" y="0"
          width="{card_w}" height="{card_h}"
          rx="6"
          fill="transparent"/>

    <rect x="{ACCENT_X}" y="{ACCENT_Y}"
          width="{ACCENT_W}" height="{ACCENT_H}"
          rx="1.5"
          fill="{theme['title']}"/>

    <text x="{TEXT_X}" y="{TITLE_Y}"
          font-family="'Segoe UI', system-ui, sans-serif"
          font-size="10" font-weight="600"
          fill="{theme['title']}">Daily Pokémon ASCII · {safe_date}</text>

    <text x="{TEXT_X}" y="{SUBTITLE_Y}"
          font-family="'Segoe UI', system-ui, sans-serif"
          font-size="8" font-weight="500"
          fill="{theme['text']}" fill-opacity="0.7">{SUBTITLE_TEXT}</text>

    <text x="{card_w // 2}" y="{message_y}"
          text-anchor="middle"
          font-family="'Courier New', Courier, monospace"
          font-size="10"
          fill="{theme['text']}">{safe_message}</text>

  </a>
</svg>"""
