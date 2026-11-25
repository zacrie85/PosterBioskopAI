# -*- coding: utf-8 -*-
"""Bingkai & hiasan poster — PosterBioskopAI v2.5.0.

10 gaya bingkai prosedural yang warnanya diambil dari palet key art
(lihat penata.analisa_gambar). Digambar lokal dengan PIL + numpy: instan,
deterministik (seed), tanpa unduhan.

v2.5.0: setiap gaya kini mengembalikan (LAYER_RGBA, inset_px) — sehingga:
  gambar()     : komposit bingkai ke poster (dipakai mesin komposisi)
  transparan() : layer bingkai MURNI di atas transparan -> ekspor PNG
                 yang bisa dipakai ulang di Canva/Photoshop/dll.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

NAMA = ("Garis klasik", "Emas mewah", "Film strip", "Kertas sobek",
        "Halftone", "Neon glow", "Art deco", "Vignet lembut",
        "Splat aksen", "Gradien warna")

EMAS_TERANG = (244, 210, 132)
EMAS_GELAP = (168, 122, 56)


def _gabung(a, b):
    """alpha_composite dua layer RGBA (a di bawah, b di atas)."""
    return Image.alpha_composite(a, b)


# ---------------------------------------------------------------- 1
def _garis_klasik(img, palet, aksen, seed):
    W, H = img.size
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    m = int(0.030 * min(W, H))
    lw = max(3, W // 320)
    d.rectangle([m, m, W - m, H - m], outline=(247, 246, 244, 225), width=lw)
    m2 = m + lw + int(0.008 * min(W, H))
    d.rectangle([m2, m2, W - m2, H - m2], outline=(*aksen, 255),
                width=max(2, lw // 2))
    s = max(6, int(m * 0.9))
    for cx, cy in ((m, m), (W - m, m), (m, H - m), (W - m, H - m)):
        d.rectangle([cx - s, cy - s, cx + s, cy + s], fill=(*aksen, 255))
    return layer, m2 + lw


# ---------------------------------------------------------------- 2
def _emas_mewah(img, palet, aksen, seed):
    W, H = img.size
    t = max(10, int(0.034 * min(W, H)))
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    tt = np.linspace(0, 1, t)
    profil = 1 - np.abs(tt - 0.5) * 2
    warna = np.zeros((t, 4), dtype=np.uint8)
    for i in range(3):
        warna[:, i] = (EMAS_GELAP[i] + (np.array(EMAS_TERANG[i], dtype=float)
                                        - EMAS_GELAP[i]) * profil).astype(np.uint8)
    warna[:, 3] = 255
    pita = Image.fromarray(warna.reshape(t, 1, 4), "RGBA")
    layer.paste(pita.resize((W, t)), (0, 0))
    layer.paste(pita.resize((W, t)), (0, H - t))
    layer.paste(pita.resize((t, H)), (0, 0))
    layer.paste(pita.resize((t, H)), (W - t, 0))
    d = ImageDraw.Draw(layer)
    gar = (58, 42, 18, 255)
    d.rectangle([t, t, W - t, H - t], outline=gar, width=2)
    d.rectangle([2, 2, W - 2, H - 2], outline=gar, width=2)
    s = int(t * 0.85)
    for cx, cy in ((t, t), (W - t, t), (t, H - t), (W - t, H - t)):
        d.polygon([(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)],
                  fill=(*EMAS_TERANG, 255), outline=gar)
    return layer, t + 6


# ---------------------------------------------------------------- 3
def _film_strip(img, palet, aksen, seed):
    W, H = img.size
    band = max(14, int(0.050 * W))
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rectangle([0, 0, band, H], fill=(16, 16, 18, 255))
    d.rectangle([W - band, 0, W, H], fill=(16, 16, 18, 255))
    d.rectangle([0, 0, W, 8], fill=(16, 16, 18, 255))
    d.rectangle([0, H - 8, W, H], fill=(16, 16, 18, 255))
    hw, hh = int(band * 0.44), int(band * 0.52)
    langkah = max(int(0.055 * H), hh + 10)
    y = int(langkah * 0.4)
    while y + hh < H - 10:
        d.rounded_rectangle([band // 2 - hw // 2, y,
                             band // 2 + hw // 2, y + hh], radius=6,
                            fill=(232, 230, 226, 95))
        d.rounded_rectangle([W - band + band // 2 - hw // 2, y,
                             W - band + band // 2 + hw // 2, y + hh],
                            radius=6, fill=(232, 230, 226, 95))
        y += langkah
    return layer, band + 8


# ---------------------------------------------------------------- 4
def _kertas_sobek(img, palet, aksen, seed):
    W, H = img.size
    b = max(12, int(0.028 * min(W, H)))
    rng = np.random.default_rng(seed)
    n = 240
    t = np.linspace(0, 1, n)

    def keliling(shrink):
        x0, y0, x1, y1 = shrink, shrink, W - shrink, H - shrink
        panjang = 2 * ((x1 - x0) + (y1 - y0))
        pts = []
        for u in t:
            j = u * panjang
            if j < x1 - x0:
                pts.append((x0 + j, y0))
            elif j < (x1 - x0) + (y1 - y0):
                pts.append((x1, y0 + (j - (x1 - x0))))
            elif j < 2 * (x1 - x0) + (y1 - y0):
                pts.append((x1 - (j - (x1 - x0) - (y1 - y0)), y1))
            else:
                pts.append((x0, y1 - (j - 2 * (x1 - x0) - (y1 - y0))))
        return pts

    luar = keliling(2)
    dalam = keliling(b)
    mask = Image.new("L", img.size, 0)
    dm = ImageDraw.Draw(mask)
    dm.polygon([(p[0] + rng.uniform(-7, 7), p[1] + rng.uniform(-7, 7))
                for p in luar], fill=255)
    dm.polygon([(p[0] + rng.uniform(-6, 6), p[1] + rng.uniform(-6, 6))
                for p in dalam], fill=0)
    layer = Image.new("RGBA", img.size, (245, 243, 240, 255))
    layer.putalpha(mask)
    return layer, b + 6


# ---------------------------------------------------------------- 5
def _halftone(img, palet, aksen, seed):
    W, H = img.size
    band = max(16, int(0.055 * min(W, H)))
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    jarak = max(9, int(band * 0.52))
    deret = [(band * 0.34, band * 0.30), (band * 0.66, band * 0.20),
             (band * 1.0, band * 0.12)]
    x = np.arange(jarak // 2, W, jarak)
    for off, r in deret:
        r = int(r)
        for px_ in x:
            for py_ in (int(off), int(H - off)):
                d.ellipse([px_ - r, py_ - r, px_ + r, py_ + r],
                          fill=(*aksen, 240))
    y = np.arange(jarak // 2, H, jarak)
    for off, r in deret:
        r = int(r)
        for py_ in y:
            for px_ in (int(off), int(W - off)):
                d.ellipse([px_ - r, py_ - r, px_ + r, py_ + r],
                          fill=(*aksen, 240))
    return layer, int(band) + 6


# ---------------------------------------------------------------- 6
def _neon_glow(img, palet, aksen, seed):
    W, H = img.size
    m = int(0.030 * min(W, H))
    lw = max(3, W // 300)
    garis = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(garis)
    d.rectangle([m, m, W - m, H - m], outline=(*aksen, 255), width=lw)
    g1 = garis.filter(ImageFilter.GaussianBlur(W // 90))
    g2 = garis.filter(ImageFilter.GaussianBlur(W // 38))
    return _gabung(_gabung(g2, g1), garis), m + lw + int(W // 90) + 4


# ---------------------------------------------------------------- 7
def _art_deco(img, palet, aksen, seed):
    import math
    W, H = img.size
    m = int(0.032 * min(W, H))
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    lw = max(3, W // 340)
    d.rectangle([m, m, W - m, H - m], outline=(236, 234, 230, 230), width=lw)
    m2 = m + 14
    d.rectangle([m2, m2, W - m2, H - m2], outline=(*aksen, 255), width=lw)
    pan = int(0.048 * min(W, H))
    for cx, cy in ((m2, m2), (W - m2, m2), (m2, H - m2), (W - m2, H - m2)):
        sx = 1 if cx < W / 2 else -1
        sy = 1 if cy < H / 2 else -1
        for sudut in (18, 45, 72):
            dx = math.cos(math.radians(sudut)) * pan * sx
            dy = math.sin(math.radians(sudut)) * pan * sy
            d.line([(cx, cy), (cx + dx, cy + dy)], fill=(*aksen, 255), width=2)
        r = max(4, lw + 2)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*aksen, 255))
    return layer, m2 + lw + 4


# ---------------------------------------------------------------- 8
def _vignet_lembut(img, palet, aksen, seed):
    W, H = img.size
    yy, xx = np.mgrid[0:H, 0:W]
    cx, cy = W / 2, H / 2
    r = np.sqrt(((xx - cx) / cx) ** 2 + ((yy - cy) / cy) ** 2) / np.sqrt(2)
    alpha = np.clip((r - 0.60) / 0.40, 0, 1) ** 1.4 * 145
    m = np.zeros((H, W, 4), dtype=np.uint8)
    m[..., 0:3] = 6
    m[..., 3] = alpha.astype(np.uint8)
    radial = Image.fromarray(m, "RGBA")
    hair = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(hair)
    mm = int(0.020 * min(W, H))
    d.rectangle([mm, mm, W - mm, H - mm], outline=(250, 248, 244, 80), width=1)
    return _gabung(radial, hair), mm + 2


# ---------------------------------------------------------------- 9
def _splat_aksen(img, palet, aksen, seed):
    W, H = img.size
    rng = np.random.default_rng(seed)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    band = int(0.14 * min(W, H))
    for cx, cy in ((0, 0), (W, 0), (0, H), (W, H)):
        for _ in range(3):
            r = rng.integers(int(band * 0.10), int(band * 0.34))
            px_ = int(cx + (band - r) * rng.random() * (1 if cx == 0 else -1))
            py_ = int(cy + (band - r) * rng.random() * (1 if cy == 0 else -1))
            d.ellipse([px_ - r, py_ - r, px_ + r, py_ + r],
                      fill=(*aksen, int(rng.integers(150, 230))))
        for _ in range(14):
            r = int(rng.integers(1, 5))
            px_ = int(cx + band * rng.random() * (1 if cx == 0 else -1))
            py_ = int(cy + band * rng.random() * (1 if cy == 0 else -1))
            d.ellipse([px_ - r, py_ - r, px_ + r, py_ + r], fill=(*aksen, 255))
    return layer, int(0.018 * min(W, H)) + 2


# ---------------------------------------------------------------- 10
def _gradien_wash(img, palet, aksen, seed):
    W, H = img.size
    yy, xx = np.mgrid[0:H, 0:W]
    g = (xx / W + (H - yy) / H) / 2.0
    alpha1 = np.clip((g - 0.52) / 0.48, 0, 1) ** 1.5 * 95
    alpha2 = np.clip((yy / H - 0.80) / 0.20, 0, 1) * 120
    m = np.zeros((H, W, 4), dtype=np.uint8)
    for i in range(3):
        m[..., i] = np.clip(aksen[i] * (alpha1 / 255.0)
                            + 10 * (alpha2 / 255.0), 0, 255).astype(np.uint8)
    m[..., 3] = np.clip(alpha1 + alpha2, 0, 255).astype(np.uint8)
    return Image.fromarray(m, "RGBA"), 0


_FUNGSI = {"Garis klasik": _garis_klasik, "Emas mewah": _emas_mewah,
           "Film strip": _film_strip, "Kertas sobek": _kertas_sobek,
           "Halftone": _halftone, "Neon glow": _neon_glow,
           "Art deco": _art_deco, "Vignet lembut": _vignet_lembut,
           "Splat aksen": _splat_aksen, "Gradien warna": _gradien_wash}


def gambar(img, nama, palet, aksen, seed=7):
    """Gambar bingkai `nama` di atas img (RGB). Return (img_baru, inset_px).
    Nama tak dikenal -> bingkai tidak digambar (inset 0)."""
    fn = _FUNGSI.get((nama or "").strip())
    if fn is None:
        return img.convert("RGB") if img.mode != "RGB" else img, 0
    layer, inset = fn(img.convert("RGB"), palet, aksen, seed)
    out = Image.alpha_composite(img.convert("RGBA"), layer)
    return out.convert("RGB"), inset


def transparan(nama, size, palet, aksen, seed=7):
    """Layer bingkai MURNI (RGBA di latar transparan) + inset_px — untuk
    ekspor PNG dipakai ulang di Canva/Photoshop/dll. Nama tak dikenal -> None."""
    fn = _FUNGSI.get((nama or "").strip())
    if fn is None:
        return None, 0
    dummy = Image.new("RGB", size, (0, 0, 0))
    layer, inset = fn(dummy, palet, aksen, seed)
    return layer, inset
