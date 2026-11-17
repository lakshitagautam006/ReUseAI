"""Utility to generate clean sample waste graphics for instant UI testing."""

from PIL import Image, ImageDraw


def create_sample_plastic_bottle() -> Image.Image:
    """Generate a clean synthetic illustration of a plastic bottle."""
    img = Image.new("RGB", (400, 500), color=(240, 245, 250))
    draw = ImageDraw.Draw(img)

    # Bottle body
    draw.rounded_rectangle([130, 160, 270, 440], radius=25, fill=(185, 225, 245), outline=(100, 170, 220), width=3)
    # Bottle neck & cap
    draw.rectangle([170, 90, 230, 160], fill=(200, 235, 250), outline=(100, 170, 220), width=3)
    draw.rounded_rectangle([165, 65, 235, 95], radius=6, fill=(35, 110, 185), outline=(20, 80, 140), width=2)
    # Water lines & label
    draw.rectangle([133, 250, 267, 330], fill=(225, 245, 255), outline=(140, 190, 230), width=2)
    draw.text((160, 280), "PET #1 Water", fill=(30, 80, 130))

    return img


def create_sample_cardboard_box() -> Image.Image:
    """Generate a clean synthetic illustration of a cardboard shipping box."""
    img = Image.new("RGB", (400, 500), color=(248, 246, 240))
    draw = ImageDraw.Draw(img)

    # Box body
    draw.polygon([(100, 200), (200, 150), (300, 200), (300, 360), (200, 420), (100, 360)], fill=(205, 165, 120), outline=(150, 110, 70))
    # Box flap crease
    draw.line([(200, 150), (200, 420)], fill=(150, 110, 70), width=3)
    # Top flaps
    draw.polygon([(100, 200), (200, 150), (200, 220), (100, 270)], fill=(220, 180, 135), outline=(150, 110, 70))
    draw.polygon([(200, 150), (300, 200), (300, 270), (200, 220)], fill=(190, 150, 105), outline=(150, 110, 70))
    draw.text((150, 310), "FRAGILE / RECYCLE", fill=(90, 60, 30))

    return img


def create_sample_aluminum_can() -> Image.Image:
    """Generate a clean synthetic illustration of an aluminum soda can."""
    img = Image.new("RGB", (400, 500), color=(245, 245, 245))
    draw = ImageDraw.Draw(img)

    # Can body
    draw.rounded_rectangle([140, 140, 260, 420], radius=15, fill=(215, 220, 225), outline=(140, 145, 150), width=3)
    # Top rim & tab
    draw.ellipse([140, 115, 260, 160], fill=(230, 235, 240), outline=(140, 145, 150), width=3)
    draw.ellipse([185, 128, 215, 148], fill=(180, 185, 190), outline=(120, 125, 130), width=2)
    # Printed banner
    draw.rectangle([143, 210, 257, 330], fill=(225, 60, 55), outline=(180, 40, 35), width=2)
    draw.text((165, 260), "SPARK SODA\nALUMINUM", fill=(255, 255, 255))

    return img


def create_sample_glass_jar() -> Image.Image:
    """Generate a clean synthetic illustration of a transparent glass storage jar."""
    img = Image.new("RGB", (400, 500), color=(245, 248, 250))
    draw = ImageDraw.Draw(img)

    # Glass jar body
    draw.rounded_rectangle([120, 140, 280, 420], radius=20, fill=(230, 244, 248), outline=(130, 185, 205), width=3)
    # Glass jar neck
    draw.rectangle([145, 105, 255, 140], fill=(220, 238, 245), outline=(130, 185, 205), width=3)
    # Metal lid with ridges
    draw.rounded_rectangle([135, 75, 265, 110], radius=6, fill=(180, 160, 110), outline=(130, 110, 70), width=3)
    draw.line([(150, 75), (150, 110)], fill=(150, 130, 90), width=2)
    draw.line([(180, 75), (180, 110)], fill=(150, 130, 90), width=2)
    draw.line([(220, 75), (220, 110)], fill=(150, 130, 90), width=2)
    draw.line([(250, 75), (250, 110)], fill=(150, 130, 90), width=2)
    # Glass reflection highlight
    draw.rounded_rectangle([135, 160, 155, 400], radius=8, fill=(245, 252, 255), outline=(190, 225, 238), width=1)
    # Reusable pantry label
    draw.rounded_rectangle([160, 220, 265, 340], radius=6, fill=(250, 248, 240), outline=(180, 160, 130), width=2)
    draw.text((175, 255), "MASON JAR\nCLEAR GLASS\n100% REUSABLE", fill=(70, 60, 50))

    return img

