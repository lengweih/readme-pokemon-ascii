from PIL import Image

# Characters ordered from visually densest (darkest) to lightest.
# Dark pixels (low luminance) map to '@'; bright pixels map to ' '.
ASCII_RAMP = "@%#*+=-:. "


def pixel_to_char(luminance: int) -> str:
    """Map a greyscale value (0–255) to one ASCII character."""
    # Divide luminance by 255 to get a 0.0–1.0 fraction,
    # multiply by the last valid index to spread values across the ramp.
    ramp_index = int(luminance / 255 * (len(ASCII_RAMP) - 1))
    return ASCII_RAMP[ramp_index]


def image_to_ascii(img: Image.Image) -> list[str]:
    """
    Convert a greyscale PIL Image into a list of ASCII strings, one per row.
    The image should already be resized to the desired character dimensions
    before this function is called.
    """
    # Guarantee single-channel mode so every pixel is a plain int.
    if img.mode != "L":
        img = img.convert("L")

    width, height = img.size

    # load() returns a pixel access object.
    # The type stub says it can return None, so we guard against that.
    pixels = img.load()
    if pixels is None:
        raise ValueError("Failed to load pixel data from image")

    lines = []
    for y in range(height):  # iterate rows top to bottom
        row_chars = []
        for x in range(width):  # iterate columns left to right
            raw = pixels[x, y]

            # Pylance types pixels[x,y] as float | tuple[int,...] | int
            # regardless of image mode. At runtime after convert("L") it is
            # always an int, but we handle the other cases to keep type
            # checkers and linters happy.
            luminance: int = raw if isinstance(raw, int) else int(raw[0])  # type: ignore[index]

            row_chars.append(pixel_to_char(luminance))

        lines.append("".join(row_chars))  # join all chars in the row into one string

    return lines


def center_blank_rows(lines: list[str]) -> list[str]:
    """Center ASCII content by evenly redistributing outer blank rows."""
    if not lines:
        return lines

    width = len(lines[0])
    blank_row = " " * width

    top_blank_rows = 0
    for line in lines:
        if line.strip():
            break
        top_blank_rows += 1

    bottom_blank_rows = 0
    for line in reversed(lines):
        if line.strip():
            break
        bottom_blank_rows += 1

    content_start = top_blank_rows
    content_end = len(lines) - bottom_blank_rows
    content = lines[content_start:content_end]

    if not content:
        return lines

    total_outer_blank_rows = top_blank_rows + bottom_blank_rows
    centered_top = total_outer_blank_rows // 2
    centered_bottom = total_outer_blank_rows - centered_top

    return [blank_row] * centered_top + content + [blank_row] * centered_bottom
