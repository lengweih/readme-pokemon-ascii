from core import svg_builder
from core.theme import ThemeName, get_theme


def test_svg_escapes_user_visible_content():
    theme = get_theme(ThemeName.DARK)
    svg = svg_builder.build_svg(
        ["<&>"],
        theme,
        "<2024-01-01>",
        "https://example.com/api?theme=dark&v=2",
        "PORYGON & CO",
    )

    assert "&lt;&amp;&gt;" in svg
    assert "&lt;2024-01-01&gt;" in svg
    assert "PORYGON &amp; CO" in svg
    assert "https://example.com/api?theme=dark&amp;v=2" in svg


def test_svg_uses_placeholder_when_ascii_lines_are_empty():
    svg = svg_builder.build_svg(
        [],
        get_theme(ThemeName.LIGHT),
        "2024-01-01",
        "https://example.com/api",
    )

    assert "[no image available today]" in svg
    assert "<svg" in svg


def test_svg_hides_footer_message_when_name_is_missing():
    svg = svg_builder.build_svg(
        ["@@@"],
        get_theme(ThemeName.DARK),
        "2024-01-01",
        "https://example.com/api",
    )

    assert "appeared!" not in svg


def test_svg_includes_reset_subtitle():
    svg = svg_builder.build_svg(
        ["@@@"],
        get_theme(ThemeName.LIGHT),
        "2024-01-01",
        "https://example.com/api",
    )

    assert "New Pokémon daily at 00:00 UTC" in svg


def test_fallback_svg_uses_standard_widget_dimensions():
    svg = svg_builder.build_fallback_svg(
        get_theme(ThemeName.DARK),
        "2024-01-01",
        "https://example.com/api",
    )

    expected_width, expected_height = svg_builder._card_dimensions(
        svg_builder.DEFAULT_ASCII_COLS,
        svg_builder.DEFAULT_ASCII_ROWS,
    )

    assert f'width="{expected_width}"' in svg
    assert f'height="{expected_height}"' in svg
    assert "image unavailable" in svg
