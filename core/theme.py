from enum import Enum
from typing import TypedDict


class ThemeName(str, Enum):
    DARK = "dark"
    LIGHT = "light"


class Theme(TypedDict):
    bg: str
    card_bg: str
    border: str
    text: str
    title: str


# A dictionary of named colour palettes.
# Each key is a theme name; the value is a dict of colour roles.
THEMES: dict[ThemeName, Theme] = {
    ThemeName.DARK: {
        "bg": "#0d1117",  # page / title-bar background
        "card_bg": "#161b22",  # main card fill
        "border": "#30363d",  # card stroke
        "text": "#c9d1d9",  # ASCII art text
        "title": "#58a6ff",  # title bar label
    },
    ThemeName.LIGHT: {
        "bg": "#ffffff",
        "card_bg": "#f6f8fa",
        "border": "#d0d7de",
        "text": "#24292f",
        "title": "#0969da",
    },
}


def get_theme(name: ThemeName) -> Theme:
    return THEMES[name]
