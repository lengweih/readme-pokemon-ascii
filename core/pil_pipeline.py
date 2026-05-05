from PIL import Image, ImageEnhance, ImageFilter


def enhance_image(img: Image.Image) -> Image.Image:
    """
    Sharpen, boost contrast and brightness, then convert to greyscale.
    Order is intentional — sharpening before contrast prevents amplifying blur.
    """
    # SHARPEN is a convolution kernel that accentuates edges.
    # Edges translate to dense ASCII characters, so this improves detail.
    img = img.filter(ImageFilter.SHARPEN)

    # Contrast(1.6) means 60% more contrast than the original.
    # Without this, mid-tone-heavy images produce flat, unreadable ASCII.
    img = ImageEnhance.Contrast(img).enhance(1.6)

    # Brightness(1.1) is a 10% lift.
    # Prevents dark images from collapsing entirely to '@@@@@' walls.
    img = ImageEnhance.Brightness(img).enhance(1.1)

    # Convert to single-channel greyscale.
    # ASCII maps luminance (how bright a pixel is), not colour,
    # so colour information is discarded here.
    return img.convert("L")
