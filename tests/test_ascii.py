from PIL import Image

from core.ascii_converter import ASCII_RAMP, center_blank_rows, image_to_ascii, pixel_to_char


def test_pixel_to_char_maps_both_extremes():
    assert pixel_to_char(0) == ASCII_RAMP[0]
    assert pixel_to_char(255) == ASCII_RAMP[-1]


def test_image_to_ascii_preserves_image_shape():
    img = Image.new("L", (10, 5), color=128)

    lines = image_to_ascii(img)

    assert len(lines) == 5
    assert all(len(line) == 10 for line in lines)


def test_image_to_ascii_converts_rgb_input_to_ascii():
    img = Image.new("RGB", (3, 2), color=(0, 0, 0))

    lines = image_to_ascii(img)

    assert lines == ["@@@", "@@@"]


def test_center_blank_rows_evenly_redistributes_outer_whitespace():
    lines = [
        "     ",
        "     ",
        "     ",
        "  @  ",
        " @@@ ",
        "     ",
    ]

    centered = center_blank_rows(lines)

    assert centered == [
        "     ",
        "     ",
        "  @  ",
        " @@@ ",
        "     ",
        "     ",
    ]


def test_center_blank_rows_preserves_total_height():
    lines = [
        "     ",
        "     ",
        "     ",
        "     ",
        "  @  ",
        " @@@ ",
    ]

    centered = center_blank_rows(lines)

    assert len(centered) == len(lines)
    assert centered == [
        "     ",
        "     ",
        "  @  ",
        " @@@ ",
        "     ",
        "     ",
    ]
