# -*- coding: utf-8 -*-
"""Buat icon.ico untuk aplikasi PosterBioskopAI (di-generate, bukan diunduh)."""

import os

from PIL import Image, ImageDraw

COL_BG = (20, 20, 32)
COL_GOLD = (242, 193, 78)
COL_RED = (232, 84, 63)
COL_WHITE = (245, 245, 245)


def make(size):
    s = size / 256.0
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # badan poster (rounded)
    m = int(16 * s)
    d.rounded_rectangle([m, m, size - m, size - m], radius=int(28 * s), fill=COL_BG,
                        outline=COL_GOLD, width=max(1, int(8 * s)))
    # lubang film strip di kiri
    hole = int(14 * s)
    for i in range(5):
        y = int(48 * s + i * 38 * s)
        d.rounded_rectangle([int(38 * s), y, int(38 * s) + hole, y + int(22 * s)],
                            radius=int(5 * s), fill=COL_GOLD)
    # teks "P" + bintang
    try:
        from PIL import ImageFont
        font = ImageFont.truetype("C:/Windows/Fonts/impact.ttf", int(150 * s))
    except Exception:                                      # noqa: BLE001
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(130 * s))
        except Exception:                                  # noqa: BLE001
            font = ImageFont.load_default()
    d.text((int(78 * s), int(30 * s)), "P", font=font, fill=COL_WHITE)
    # bintang aksen
    cx, cy, r1, r2 = int(190 * s), int(200 * s), int(34 * s), int(14 * s)
    import math
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        r = r1 if i % 2 == 0 else r2
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    d.polygon(pts, fill=COL_RED)
    return img


def main():
    imgs = [make(s) for s in (16, 24, 32, 48, 64, 128, 256)]
    base = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(base, "icon.ico")
    imgs[-1].save(out, format="ICO", sizes=[(im.width, im.height) for im in imgs],
                  append_images=imgs[:-1])
    print("icon.ico dibuat:", out)


if __name__ == "__main__":
    main()
