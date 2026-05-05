from core import svg_builder
from core.theme import ThemeName, get_theme


def test_svg_escapes_user_visible_content():
    theme = get_theme(ThemeName.DARK)
    svg = svg_builder.build_svg(
        ["<&>"],
        theme,
        "<2024-01-01>",
        "https://example.com/?theme=dark&v=2",
        "PORYGON & CO",
    )

    assert "&lt;&amp;&gt;" in svg
    assert "&lt;2024-01-01&gt;" in svg
    assert "PORYGON &amp; CO" in svg
    assert "https://example.com/?theme=dark&amp;v=2" in svg


def test_svg_uses_placeholder_when_ascii_lines_are_empty():
    svg = svg_builder.build_svg(
        [],
        get_theme(ThemeName.LIGHT),
        "2024-01-01",
        "https://example.com/",
    )

    assert "[no image available today]" in svg
    assert "<svg" in svg


def test_svg_hides_footer_message_when_name_is_missing():
    svg = svg_builder.build_svg(
        ["@@@"],
        get_theme(ThemeName.DARK),
        "2024-01-01",
        "https://example.com/",
    )

    assert "appeared!" not in svg


def test_svg_includes_reset_subtitle():
    svg = svg_builder.build_svg(
        ["@@@"],
        get_theme(ThemeName.LIGHT),
        "2024-01-01",
        "https://example.com/",
    )

    assert "New Pokémon daily at 00:00 UTC" in svg


def test_svg_marks_the_full_card_as_clickable():
    svg = svg_builder.build_svg(
        ["@@@"],
        get_theme(ThemeName.DARK),
        "2024-01-01",
        "https://example.com/",
    )
    fallback_svg = svg_builder.build_fallback_svg(
        get_theme(ThemeName.LIGHT),
        "2024-01-01",
        "https://example.com/",
    )

    assert 'style="cursor: pointer;"' in svg
    assert 'fill="transparent"' in svg
    assert 'style="cursor: pointer;"' in fallback_svg
    assert 'fill="transparent"' in fallback_svg


def test_svg_rounds_the_title_bar_top_corners_without_clip_paths():
    svg = svg_builder.build_svg(
        ["@@@"],
        get_theme(ThemeName.DARK),
        "2024-01-01",
        "https://example.com/",
    )
    fallback_svg = svg_builder.build_fallback_svg(
        get_theme(ThemeName.LIGHT),
        "2024-01-01",
        "https://example.com/",
    )

    assert '<clipPath' not in svg
    assert f'height="{svg_builder.TITLE_H - svg_builder.CARD_RADIUS}"' in svg
    assert f'y="{svg_builder.CARD_RADIUS}"' in svg
    assert '<clipPath' not in fallback_svg
    assert f'height="{svg_builder.TITLE_H - svg_builder.CARD_RADIUS}"' in fallback_svg
    assert f'y="{svg_builder.CARD_RADIUS}"' in fallback_svg


def test_fallback_svg_uses_standard_widget_dimensions():
    svg = svg_builder.build_fallback_svg(
        get_theme(ThemeName.DARK),
        "2024-01-01",
        "https://example.com/",
    )

    expected_width, expected_height = svg_builder._card_dimensions(
        svg_builder.DEFAULT_ASCII_COLS,
        svg_builder.DEFAULT_ASCII_ROWS,
    )

    assert f'width="{expected_width}"' in svg
    assert f'height="{expected_height}"' in svg
    assert "image unavailable" in svg
