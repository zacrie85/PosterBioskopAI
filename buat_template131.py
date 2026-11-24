# -*- coding: utf-8 -*-
"""Generate 131 template poster bergaya Hollywood (ORIGINAL, bukan karya
berhak cipta): 15 keluarga layout x 10 palet warna, diambil 131 pertama.
Setiap template = PNG RGBA 1080x1920 (overlay/latar) + JSON zona teks.
Jalankan dari folder aplikasi: python3 buat_template131.py"""

import json
import os

from PIL import Image, ImageDraw, ImageFilter

W, H = 1080, 1920

PALET = [
    ("emas", "#F2C14E", (14, 11, 6)),
    ("crimson", "#E23B3B", (18, 5, 7)),
    ("orka", "#2EC4B6", (5, 15, 15)),
    ("ungu", "#B14CF0", (13, 5, 19)),
    ("biru", "#4C7DF0", (5, 9, 19)),
    ("senja", "#FF8C42", (19, 9, 3)),
    ("rimba", "#3FA34D", (5, 13, 7)),
    ("mono", "#E0E0E0", (9, 9, 9)),
    ("pop", "#FF5D8F", (19, 5, 11)),
    ("perak", "#9FB4C7", (7, 9, 11)),
]

# Zona judul & opsi per keluarga: (label, slug, cfg)
FAMILI = [
    ("Klasik", "klasik", {"judul": [0.06, 0.72, 0.94, 0.88], "garis": True,
                          "tanggal": True, "billing": True}),
    ("Judul Atas", "judul-atas", {"judul": [0.06, 0.07, 0.94, 0.24],
                                  "garis": True, "tanggal": False,
                                  "billing": True}),
    ("Letterbox", "letterbox", {"judul": [0.06, 0.868, 0.94, 0.945],
                                "garis": False, "tanggal": False,
                                "billing": False}),
    ("Panel Samping", "panel-samping", {"judul": [0.20, 0.72, 0.96, 0.88],
                                        "garis": True, "tanggal": True,
                                        "billing": True}),
    ("Festival", "festival", {"judul": [0.06, 0.66, 0.94, 0.82], "garis": True,
                              "tanggal": True, "billing": True}),
    ("Komedi", "komedi", {"judul": [0.08, 0.79, 0.92, 0.90], "garis": False,
                          "tanggal": True, "billing": True}),
    ("Minimalis", "minimalis", {"judul": [0.10, 0.845, 0.90, 0.935],
                                "garis": True, "tanggal": False,
                                "billing": False, "studio": False}),
    ("Gradien Penuh", "gradien-penuh", {"judul": [0.06, 0.72, 0.94, 0.88],
                                        "garis": True, "tanggal": True,
                                        "billing": True}),
    ("Duotone", "duotone", {"judul": [0.06, 0.70, 0.94, 0.87], "garis": True,
                            "tanggal": True, "billing": True}),
    ("Bingkai", "bingkai", {"judul": [0.09, 0.78, 0.91, 0.90], "garis": True,
                            "tanggal": True, "billing": True}),
    ("Badge", "badge", {"judul": [0.06, 0.74, 0.94, 0.88], "garis": True,
                        "tanggal": True, "billing": True}),
    ("Kolom Tiga", "kolom-tiga", {"judul": [0.06, 0.06, 0.94, 0.20],
                                  "garis": False, "tanggal": False,
                                  "billing": True}),
    ("Vignette", "vignette", {"judul": [0.06, 0.72, 0.94, 0.88], "garis": True,
                              "tanggal": True, "billing": True}),
    ("Sisi Gelap", "sisi-gelap", {"judul": [0.64, 0.70, 0.965, 0.88],
                                  "garis": True, "tanggal": True,
                                  "billing": True}),
    ("Skrim Puncak", "skrim-puncak", {"judul": [0.06, 0.10, 0.94, 0.30],
                                      "garis": True, "tanggal": False,
                                      "billing": True}),
]


def scrim(d, y0, y1, warna, a0, a1):
    """Gradasi alpha vertikal dari fraksi y0 ke y1."""
    for y in range(int(y0 * H), int(y1 * H)):
        t = (y - y0 * H) / max(1, (y1 - y0) * H)
        d.line([(0, y), (W, y)], fill=(*warna, int(a0 + (a1 - a0) * t)))


def laurel(d, cx, y, warna, skala=1.0):
    """Karangan laurel sederhana (dua lengkung + daun) di atas judul."""
    r = int(120 * skala)
    for sisi in (-1, 1):
        x0 = cx + sisi * r - r
        d.arc([x0, y, x0 + 2 * r, y + int(1.55 * r)], 90, 230 if sisi < 0 else 310,
              fill=warna, width=6)
        for i in range(7):
            t = i / 6.0
            lx = cx + sisi * (r * 0.15 + r * 0.85 * t)
            ly = y + int(r * 1.45 - r * 1.3 * t ** 1.3)
            d.ellipse([lx - 7 * skala, ly - 14 * skala, lx + 7 * skala, ly],
                      fill=warna)


def bintang(d, cx, cy, r, warna):
    import math
    pts = []
    for i in range(10):
        rad = r if i % 2 == 0 else r * 0.45
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
    d.polygon(pts, fill=warna)


def gambar(fam_slug, pal):
    """Bangun overlay RGBA untuk satu keluarga + palet."""
    _, accent_hex, tint = pal
    accent = tuple(int(accent_hex[i:i + 2], 16) for i in (1, 3, 5))
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    if fam_slug in ("klasik", "gradien-penuh"):
        if fam_slug == "klasik":
            scrim(d, 0.55, 1.0, (0, 0, 0), 0, 225)
        else:
            scrim(d, 0.0, 1.0, tint, 95, 225)
        d.rectangle([int(W * 0.42), int(H * 0.020), int(W * 0.58), int(H * 0.024)],
                    fill=(*accent, 200))

    elif fam_slug == "judul-atas":
        scrim(d, 0.0, 0.34, (0, 0, 0), 235, 0)
        d.rectangle([int(W * 0.42), int(H * 0.976), int(W * 0.58), int(H * 0.980)],
                    fill=(*accent, 200))

    elif fam_slug == "letterbox":
        d.rectangle([0, 0, W, int(H * 0.115)], fill=(5, 5, 5, 255))
        d.rectangle([0, int(H * 0.858), W, H], fill=(5, 5, 5, 255))
        d.rectangle([0, int(H * 0.115) - 3, W, int(H * 0.115)], fill=(*accent, 255))
        d.rectangle([0, int(H * 0.858), W, int(H * 0.858) + 3], fill=(*accent, 255))

    elif fam_slug == "panel-samping":
        d.rectangle([0, 0, int(W * 0.17), H], fill=(*tint, 225))
        d.rectangle([int(W * 0.17), 0, int(W * 0.172), H], fill=(*accent, 255))
        for i in range(5):
            d.rectangle([int(W * 0.06), int(H * (0.30 + i * 0.035)),
                         int(W * 0.11), int(H * (0.30 + i * 0.035)) + 4],
                        fill=(*accent, 170))

    elif fam_slug == "festival":
        scrim(d, 0.52, 1.0, (0, 0, 0), 0, 210)
        laurel(d, W // 2, int(H * 0.055), (*accent, 235), 1.0)
        scrim(d, 0.0, 0.16, (0, 0, 0), 150, 0)

    elif fam_slug == "komedi":
        d.rounded_rectangle([int(W * 0.04), int(H * 0.745), int(W * 0.96),
                             int(H * 0.945)], radius=48, fill=(*tint, 205),
                            outline=(*accent, 255), width=5)
        d.rounded_rectangle([int(W * 0.06), int(H * 0.70), int(W * 0.94),
                             int(H * 0.725)], radius=12, fill=(*accent, 220))

    elif fam_slug == "minimalis":
        band = int(W * 0.045)
        d.rectangle([0, 0, W, band], fill=(250, 250, 250, 255))
        d.rectangle([0, H - int(H * 0.175), W, H], fill=(250, 250, 250, 255))
        d.rectangle([0, 0, band, H], fill=(250, 250, 250, 255))
        d.rectangle([W - band, 0, W, H], fill=(250, 250, 250, 255))
        d.rectangle([band + 14, H - int(H * 0.175) - 14, W - band - 14,
                     H - int(H * 0.175) - 10], fill=(*accent, 255))

    elif fam_slug == "duotone":
        d.rectangle([0, int(H * 0.575), W, H], fill=(*tint, 195))
        d.rectangle([0, int(H * 0.558), W, int(H * 0.575)], fill=(*accent, 230))

    elif fam_slug == "bingkai":
        d.rectangle([int(W * 0.030), int(H * 0.018), W - int(W * 0.030),
                     H - int(H * 0.018)], outline=(*accent, 230), width=5)
        d.rectangle([int(W * 0.042), int(H * 0.030), W - int(W * 0.042),
                     H - int(H * 0.030)], outline=(*accent, 160), width=2)
        for cx, cy in ((int(W * 0.030), int(H * 0.018)),
                       (W - int(W * 0.030), int(H * 0.018)),
                       (int(W * 0.030), H - int(H * 0.018)),
                       (W - int(W * 0.030), H - int(H * 0.018))):
            d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=(*accent, 255))

    elif fam_slug == "badge":
        scrim(d, 0.58, 1.0, (0, 0, 0), 0, 200)
        r = int(W * 0.075)
        cx, cy = W - r - int(W * 0.05), r + int(H * 0.045)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*accent, 240),
                  outline=(255, 255, 255, 230), width=4)
        bintang(d, cx, cy, int(r * 0.52), (255, 255, 255, 255))

    elif fam_slug == "kolom-tiga":
        for i, a in ((0, 80), (1, 130), (2, 80)):
            d.rectangle([int(W * i / 3), 0, int(W * (i + 1) / 3), H],
                        fill=(*tint, a))
        d.rectangle([0, 0, W, int(H * 0.30)], fill=(*tint, 150))
        d.rectangle([int(W * 0.42), int(H * 0.30) - 4, int(W * 0.58),
                     int(H * 0.30)], fill=(*accent, 255))

    elif fam_slug == "vignette":
        msk = Image.new("L", (W, H), 0)
        dm = ImageDraw.Draw(msk)
        dm.ellipse([-int(W * 0.25), -int(H * 0.18), int(W * 1.25), int(H * 1.18)],
                   fill=255)
        msk = msk.filter(ImageFilter.GaussianBlur(140))
        vin = Image.new("RGBA", (W, H), (*tint, 235))
        img = Image.composite(img, vin, msk)
        d = ImageDraw.Draw(img)

    elif fam_slug == "sisi-gelap":
        d.rectangle([int(W * 0.62), 0, W, H], fill=(*tint, 215))
        d.rectangle([int(W * 0.62) - 5, 0, int(W * 0.62), H], fill=(*accent, 255))
        for i in range(4):
            d.rectangle([int(W * 0.66), int(H * (0.22 + i * 0.045)),
                         int(W * 0.90), int(H * (0.22 + i * 0.045)) + 3],
                        fill=(*accent, 150))

    elif fam_slug == "skrim-puncak":
        scrim(d, 0.0, 0.44, (0, 0, 0), 240, 0)
        d.rectangle([int(W * 0.42), int(H * 0.415), int(W * 0.58),
                     int(H * 0.419)], fill=(*accent, 220))

    return img


def main():
    os.makedirs("templates", exist_ok=True)
    n = 0
    # urut slug keluarga + nama palet supaya nomor file = urutan alfabetis
    for label, slug, cfg in sorted(FAMILI, key=lambda f: f[1]):
        for nama_p, accent, _tint in sorted(PALET, key=lambda p: p[0]):
            if n >= 131:
                break
            n += 1
            pal = (nama_p, accent, _tint)
            img = gambar(slug, pal)
            nama_file = f"{slug}-{nama_p}-{n:03d}"
            img.save(os.path.join("templates", nama_file + ".png"))
            cfg_full = dict(cfg)
            cfg_full["aksen"] = accent
            cfg_full["warna"] = "#141414" if slug == "minimalis" else "#F7F6F4"
            cfg_full["keluarga"] = label
            cfg_full["palet"] = nama_p.replace("-", " ").title()
            with open(os.path.join("templates", nama_file + ".json"), "w",
                      encoding="utf-8") as fh:
                json.dump(cfg_full, fh, ensure_ascii=False, indent=1)
    print("template dibuat:", n)


if __name__ == "__main__":
    main()
