#!/usr/bin/env python3
"""Generate clean gradient + initials avatars (256x256 PNG) for the demo people.

Outputs to seed/avatars/<ref>.png and website/public/avatars/<ref>.png so the
web-client serves them at /avatars/<ref>.png (used as desk.personalImageUrl).
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_DIRS = [os.path.join(HERE, "avatars"), os.path.join(ROOT, "website", "public", "avatars")]
SIZE = 256

FONT_CANDIDATES = [
    "/usr/share/fonts/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/liberation-sans/LiberationSans-Bold.ttf",
    "/usr/share/fonts/TTF/LiberationSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
]

# ref: (initials, top color, bottom color) — distinct, modern two-stop gradients.
PEOPLE = {
    "maya":    ("MH", "#7C3AED", "#4F46E5"),
    "omar":    ("ON", "#0EA5E9", "#2563EB"),
    "lina":    ("LF", "#EC4899", "#BE185D"),
    "karim":   ("KA", "#059669", "#047857"),
    "salma":   ("SY", "#14B8A6", "#0D9488"),
    "ahmed":   ("AS", "#F59E0B", "#D97706"),
    "nour":    ("NA", "#F43F5E", "#E11D48"),
    "hana":    ("HM", "#A855F7", "#7E22CE"),
    "youssef": ("YT", "#3B82F6", "#1D4ED8"),
    "mariam":  ("MK", "#10B981", "#059669"),
    "daniel":  ("DR", "#6366F1", "#4338CA"),
    "sara":    ("SM", "#FB7185", "#E11D48"),
    "adam":    ("AW", "#0891B2", "#0E7490"),
    "reem":    ("RF", "#8B5CF6", "#6D28D9"),
    "ziad":    ("ZE", "#22C55E", "#16A34A"),
}


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def load_font(px):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, px)
    return ImageFont.load_default()


def gradient(top, bottom, size):
    """Vertical linear gradient with a soft diagonal highlight."""
    base = Image.new("RGB", (size, size))
    px = base.load()
    tr, tg, tb = top
    br, bg, bb = bottom
    for y in range(size):
        t = y / (size - 1)
        r = int(tr + (br - tr) * t)
        g = int(tg + (bg - tg) * t)
        b = int(tb + (bb - tb) * t)
        for x in range(size):
            px[x, y] = (r, g, b)
    return base


def make(ref, initials, top, bottom):
    img = gradient(hex2rgb(top), hex2rgb(bottom), SIZE)
    draw = ImageDraw.Draw(img)
    # subtle top-left highlight for depth
    hl = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(hl).ellipse([-SIZE // 2, -SIZE // 2, SIZE // 2, SIZE // 2], fill=60)
    white = Image.new("RGB", (SIZE, SIZE), (255, 255, 255))
    img = Image.composite(white, img, hl.point(lambda a: a // 3))

    draw = ImageDraw.Draw(img)
    font = load_font(112)
    bbox = draw.textbbox((0, 0), initials, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (SIZE - tw) / 2 - bbox[0]
    y = (SIZE - th) / 2 - bbox[1]
    draw.text((x + 2, y + 3), initials, font=font, fill=(0, 0, 0, 60))  # soft shadow
    draw.text((x, y), initials, font=font, fill=(255, 255, 255))

    for d in OUT_DIRS:
        os.makedirs(d, exist_ok=True)
        img.save(os.path.join(d, f"{ref}.png"), "PNG")
    return f"{ref}.png ({initials})"


if __name__ == "__main__":
    for ref, (initials, top, bottom) in PEOPLE.items():
        print("  " + make(ref, initials, top, bottom))
    print(f"Done -> {', '.join(OUT_DIRS)}")
