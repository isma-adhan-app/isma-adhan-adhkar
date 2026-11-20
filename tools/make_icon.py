"""Generate assets/icon.ico: a simple crescent on a dark green disc.

Run from the repo root:  python tools/make_icon.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "assets" / "icon.ico"

GREEN = (18, 92, 54, 255)
GOLD = (232, 190, 80, 255)
TRANSPARENT = (0, 0, 0, 0)


def main() -> None:
    size = 256
    img = Image.new("RGBA", (size, size), TRANSPARENT)
    d = ImageDraw.Draw(img)
    m = 8
    d.ellipse((m, m, size - m, size - m), fill=GREEN)
    # crescent: gold circle with a green disc cut out, offset to the left
    cx, cy, r = size * 0.56, size * 0.5, size * 0.30
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=GOLD)
    r2 = r * 0.86
    cx2 = cx + r * 0.42
    d.ellipse((cx2 - r2, cy - r2, cx2 + r2, cy + r2), fill=GREEN)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
