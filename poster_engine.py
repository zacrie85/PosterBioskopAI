# -*- coding: utf-8 -*-
"""
PosterBioskopAI — mesin render poster film sinematik, 100% offline (Pillow).

Alur: foto/frame video -> color grading sinematik per genre -> efek (vignette,
grain, bloom, letterbox) -> tipografi ala poster Hollywood (judul auto-fit,
tagline, billing block, strip rilis).
"""

import math
import random

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageChops, ImageOps, ImageFont

RESAMPLE = getattr(Image, "Resampling", Image).LANCZOS

# ---------------------------------------------------------------------------
# Font: cari font bawaan Windows dulu (Impact, Arial Black, Georgia), lalu
# fallback ke font bebas (DejaVu / Liberation / Noto) supaya jalan di mana saja.
# ---------------------------------------------------------------------------
FONT_DIRS = [
    "C:/Windows/Fonts",
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/truetype/liberation",
    "/usr/share/fonts/truetype/chinese",
    "/usr/share/fonts",
    "/System/Library/Fonts",
    "/Library/Fonts",
]

_DISPLAY_FONTS = ["impact.ttf", "ariblk.ttf", "DejaVuSans-Bold.ttf",
                  "LiberationSans-Bold.ttf", "NotoSansSC-Bold.ttf"]
FONT_CANDIDATES = {
    "impact": _DISPLAY_FONTS,
    "display": _DISPLAY_FONTS,
    "block":    ["ariblk.ttf", "impact.ttf", "DejaVuSans-Bold.ttf",
                 "LiberationSans-Bold.ttf", "NotoSansSC-Bold.ttf"],
    "serif":    ["georgiab.ttf", "timesbd.ttf", "DejaVuSerif-Bold.ttf",
                 "LiberationSerif-Bold.ttf", "NotoSerifSC-Bold.ttf"],
    "condensed": ["consolab.ttf", "arial.ttf", "DejaVuSansMono-Bold.ttf",
                  "LiberationMono-Bold.ttf", "NotoSansSC-Regular.ttf"],
}

_font_files = {}   # role -> path
_font_cache = {}   # (role, size) -> ImageFont


def _resolve_font_files():
    import os
    for role, names in FONT_CANDIDATES.items():
        for name in names:
            for d in FONT_DIRS:
                p = os.path.join(d, name)
                if os.path.isfile(p):
                    _font_files[role] = p
                    break
            if role in _font_files:
                break
    # jaring pengaman: role apa pun yang gagal resolve memakai font display
    fallback = _font_files.get("display") or _font_files.get("condensed")
    for role in set(FONT_CANDIDATES) | {"impact"}:
        if _font_files.get(role) is None:
            _font_files[role] = fallback


def get_font(role, size):
    if not _font_files:
        _resolve_font_files()
    if _font_files.get(role) is None:      # role tak dikenal -> pakai display
        role = "display"
    key = (role, int(size))
    if key not in _font_cache:
        path = _font_files.get(role)
        try:
            _font_cache[key] = ImageFont.truetype(path, int(size)) if path else \
                ImageFont.load_default()
        except Exception:
            _font_cache[key] = ImageFont.load_default()
    return _font_cache[key]


def font_file_for(role):
    if not _font_files:
        _resolve_font_files()
    return _font_files.get(role)


# ---------------------------------------------------------------------------
# Ukuran render
# ---------------------------------------------------------------------------
RATIOS = {          # nama yang tampil di UI -> rasio (w/h)
    "Poster 2:3": 2 / 3,
    "Potret 3:4": 3 / 4,
    "Kotak 1:1": 1.0,
    "Wallpaper 16:9": 16 / 9,
}

FULL_SIZES = {
    "Poster 2:3": (1000, 1500),
    "Potret 3:4": (1125, 1500),
    "Kotak 1:1": (1200, 1200),
    "Wallpaper 16:9": (1600, 900),
}


def preview_size(ratio_key, max_h=760, max_w=920):
    """Ukuran preview yang pas di jendela (menjaga rasio)."""
    r = RATIOS.get(ratio_key, 2 / 3)
    w, h = int(max_h * r), max_h
    if w > max_w:
        w, h = max_w, int(max_w / r)
    return (max(2, w // 2 * 2), max(2, h // 2 * 2))


# ---------------------------------------------------------------------------
# Util gambar dasar
# ---------------------------------------------------------------------------
def cover_crop(img, ratio, focus=0.45):
    """Potong gambar agar pas rasio (cover). focus: 0=atas, 0.5=tengah (untuk wajah)."""
    w, h = img.size
    if w / h > ratio:              # terlalu lebar -> potong kiri-kanan
        tw = int(h * ratio)
        x0 = (w - tw) // 2
        return img.crop((x0, 0, x0 + tw, h))
    th = int(w / ratio)            # terlalu tinggi -> potong atas-bawah (bias fokus)
    y0 = int(max(0, min(h - th, (h - th) * focus)))
    return img.crop((0, y0, w, y0 + th))


def color_grade(img, gr):
    """Color grading: brightness/contrast/saturation + split-toning shadow/highlight."""
    img = ImageEnhance.Brightness(img).enhance(gr.get("bri", 1.0))
    img = ImageEnhance.Contrast(img).enhance(gr.get("con", 1.0))
    img = ImageEnhance.Color(img).enhance(gr.get("sat", 1.0))
    w, h = img.size
    gray = img.convert("L")
    sk = gr.get("shadow_k", 0)
    if sk > 0:
        mask = gray.point(lambda v: int(((255 - v) / 255.0) ** 1.6 * 255 * sk))
        img = Image.composite(Image.new("RGB", (w, h), gr.get("shadow", (0, 20, 40))), img, mask)
    hk = gr.get("hl_k", 0)
    if hk > 0:
        mask = gray.point(lambda v: int((v / 255.0) ** 2.2 * 255 * hk))
        img = Image.composite(Image.new("RGB", (w, h), gr.get("highlight", (255, 180, 120))), img, mask)
    return img


def bloom(img, amount):
    if amount <= 0:
        return img
    gray = img.convert("L")
    mask = gray.point(lambda v: 255 if v > 185 else 0).filter(ImageFilter.GaussianBlur(10))
    glow = img.filter(ImageFilter.GaussianBlur(12))
    glow = ImageEnhance.Brightness(glow).enhance(1.25)
    return Image.composite(glow, img, mask.point(lambda v: int(v * min(1.0, amount))))


def vignette(img, strength):
    if strength <= 0:
        return img
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    cx, cy = w / 2.0, h / 2.0
    maxr = math.hypot(cx, cy)
    steps = 48
    for i in range(steps):                      # besar (gelap) -> kecil (terang)
        r = maxr * (1 - i / steps)
        v = int(255 * strength * (1 - i / steps) ** 1.8)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=v)
    mask = mask.filter(ImageFilter.GaussianBlur(max(2, w * 0.02)))
    return Image.composite(Image.new("RGB", (w, h), (0, 0, 0)), img, mask)


def grain(img, amount):
    if amount <= 0:
        return img
    noise = Image.effect_noise(img.size, 28).convert("RGB")
    noisy = ImageChops.overlay(img, noise)
    return Image.blend(img, noisy, min(1.0, amount))


def letterbox(img, bar=0.055):
    w, h = img.size
    d = ImageDraw.Draw(img)
    bh = int(h * bar)
    d.rectangle([0, 0, w, bh], fill=(0, 0, 0))
    d.rectangle([0, h - bh, w, h], fill=(0, 0, 0))
    return img


def _vgrad_mask(size, y0, y1, strength, reverse=False):
    """Mask L: gradasi vertikal (untuk zona teks gelap atas/bawah)."""
    w, h = size
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    a, b = int(h * y0), int(h * y1)
    smax = int(255 * strength)
    for y in range(a, min(b, h)):
        t = (y - a) / max(1, (b - a))
        v = smax - int(smax * (t ** 1.4)) if reverse else int(smax * (t ** 1.4))
        d.line([(0, y), (w, y)], fill=v)
    return m


def _vgrad_strip(c1, c2, w, h):
    """Gambar RGB gradasi vertikal c1 -> c2."""
    col = Image.new("RGB", (1, h))
    d = ImageDraw.Draw(col)
    for y in range(h):
        t = y / max(1, h - 1)
        d.point((0, y), fill=tuple(int(a + (b - a) * t) for a, b in zip(c1, c2)))
    return col.resize((w, h), RESAMPLE)


# ---------------------------------------------------------------------------
# Util teks
# ---------------------------------------------------------------------------
def text_w(font, text, tracking=0):
    return font.getlength(text) + tracking * max(0, len(text) - 1)


def draw_tracked(d, cx, y, text, font, fill, tracking=0, stroke=0, stroke_fill=(0, 0, 0, 255),
                 shadow=None):
    """Tulis teks dengan letter-spacing, dipusatkan di cx. shadow=(dx,dy,color)."""
    w = text_w(font, text, tracking)
    x = cx - w / 2.0
    if shadow:
        sx, sy, scolor = shadow
        xx = x
        for ch in text:
            d.text((xx + sx, y + sy), ch, font=font, fill=scolor)
            xx += font.getlength(ch) + tracking
    xx = x
    for ch in text:
        d.text((xx, y), ch, font=font, fill=fill,
               stroke_width=stroke, stroke_fill=stroke_fill)
        xx += font.getlength(ch) + tracking
    return w


def _split_two_lines(text, font, max_w):
    words = text.split()
    if len(words) < 2:
        return None
    best = None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        wa, wb = font.getlength(a), font.getlength(b)
        if wa <= max_w and wb <= max_w:
            diff = abs(wa - wb)
            if best is None or diff < best[0]:
                best = (diff, [a, b])
    return best[1] if best else None


def fit_title(text, role, max_w, max_h, start_size, min_size=16):
    """Cari ukuran font terbesar agar judul muat (1-2 baris seimbang)."""
    size = int(start_size)
    while size >= min_size:
        font = get_font(role, size)
        if text_w(font, text) <= max_w:
            return font, [text], size
        lines = _split_two_lines(text, font, max_w)
        if lines and len(lines) * size * 1.14 <= max_h:
            return font, lines, size
        size = int(size * 0.94)
    return get_font(role, min_size), [text], min_size


def _wrap_width(text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if font.getlength(trial) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def _billing_text(title, cast, director):
    seg = ["\u201c" + title.upper() + "\u201d"]
    if cast:
        names = ", ".join(c.strip().upper() for c in cast.split(",") if c.strip())[:120]
        seg.append("DIBINTANGI " + names)
    seg.append("MUSIK ORISINAL")
    seg.append("SUTRADARA " + (director.strip().upper() if director and director.strip() else "KAMU"))
    return "    ".join(seg)


# ---------------------------------------------------------------------------
# Render utama
# ---------------------------------------------------------------------------
def render_poster(photo, style, title, tagline="", cast="", director="",
                  size=(1000, 1500), seed=7, minimal=False,
                  studio="POSTER BIOSKOP PICTURES", release="SEGERA DI BIOSKOP"):
    W, H = size
    typo = style["typo"]
    pal = style["palette"]
    fx = style["fx"]
    layout = style["layout"]

    photo = ImageOps.exif_transpose(photo).convert("RGB")
    photo = cover_crop(photo, W / H, focus=style.get("focus", 0.45)).resize((W, H), RESAMPLE)

    img = color_grade(photo, style["grading"])
    img = bloom(img, fx.get("bloom", 0))
    img = vignette(img, fx.get("vignette", 0.3))
    img = grain(img, fx.get("grain", 0.15))

    lb = fx.get("letterbox", False) and abs(W / H - 16 / 9) < 0.02
    if lb:
        img = letterbox(img, 0.055)

    # Zona gelap atas (untuk nama pemain) & bawah (untuk judul/kredit)
    if not minimal and cast:
        img = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), img,
                              _vgrad_mask((W, H), 0.0, 0.16, 0.55, reverse=True))
    img = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), img,
                          _vgrad_mask((W, H), 0.50, 0.995, 0.92))

    title_case = typo.get("case", "upper")
    title_text = title.strip() if title and title.strip() else "TANPA JUDUL"
    if title_case == "upper":
        title_text = title_text.upper()

    role = typo.get("font_role", "impact")
    accent = pal["accent"]

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    # --- posisi zona per layout ---
    if layout == "center":
        tag_y, cast_y = 0.09, 0.045
        t_top, t_maxh = 0.34, 0.20
        bill_y, rel_y, std_y = 0.885, 0.945, 0.978
    elif layout == "split":
        tag_y, cast_y = 0.085, 0.045
        t_top, t_maxh = 0.64, 0.19
        bill_y, rel_y, std_y = 0.868, 0.945, 0.978
    else:  # "bottom" — one-sheet klasik
        tag_y, cast_y = 0.575, 0.042
        t_top, t_maxh = 0.625, 0.21
        bill_y, rel_y, std_y = 0.855, 0.945, 0.978

    if lb:   # letterbox menutup tepi -> tanpa strip bawah
        rel_y = std_y = None

    # --- nama pemain (billing atas) ---
    if not minimal and cast:
        f_cast = get_font("condensed", max(10, int(H * 0.021)))
        names = "   ·   ".join(c.strip().upper() for c in cast.split(",") if c.strip())[:90]
        draw_tracked(d, W / 2, int(H * cast_y), names, f_cast, (245, 245, 245, 225),
                     tracking=max(2, int(H * 0.004)),
                     shadow=(1, 1, (0, 0, 0, 160)))

    # --- tagline ---
    if not minimal and tagline:
        f_tag = get_font("serif", max(11, int(H * 0.024)))
        draw_tracked(d, W / 2, int(H * tag_y), "\u201c" + tagline + "\u201d", f_tag,
                     (*accent, 235), tracking=max(1, int(H * 0.002)),
                     shadow=(1, 1, (0, 0, 0, 160)))

    # --- judul: auto-fit ---
    max_tw = W * 0.86
    start = int(H * 0.128) if role in ("impact", "block") else int(H * 0.11)
    f_title, lines, tsize = fit_title(title_text, role, max_tw, H * t_maxh, start)
    track = max(1, int(tsize * 0.02)) if role == "serif" else 0
    lh = tsize * 1.14
    t_end = H * t_top + lh * len(lines)

    # bayangan lembut judul
    if not lb or t_end < H * 0.9:
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ds = ImageDraw.Draw(sh)
        yy = H * t_top
        for ln in lines:
            ds.text((W / 2 - text_w(f_title, ln, track) / 2 + max(2, tsize * 0.045),
                     yy + max(3, tsize * 0.05)), ln, font=f_title,
                    fill=(0, 0, 0, 200), stroke_width=max(1, tsize // 30),
                    stroke_fill=(0, 0, 0, 200))
            yy += lh
        sh = sh.filter(ImageFilter.GaussianBlur(max(2, tsize * 0.02)))
        img = Image.alpha_composite(img.convert("RGBA"), sh).convert("RGB")

    # judul itu sendiri
    fill_mode = typo.get("title_fill", "white")
    if fill_mode == "gradient":
        y_top = max(0, int(H * t_top))
        y_bot = min(H, int(t_end) + tsize // 3 + 2)
        gh = max(1, y_bot - y_top)
        tmask = Image.new("L", (W, H), 0)
        dm = ImageDraw.Draw(tmask)
        yy = H * t_top
        for ln in lines:
            dm.text((W / 2 - text_w(f_title, ln, track) / 2, yy), ln, font=f_title,
                    fill=255, stroke_width=max(1, tsize // 30), stroke_fill=255)
            yy += lh
        g1, g2 = pal["title_grad"]
        img.paste(_vgrad_strip(g1, g2, W, gh), (0, y_top),
                  tmask.crop((0, y_top, W, y_bot)))
    else:
        fill = (246, 246, 246, 255) if fill_mode == "white" else (*accent, 255)
        yy = H * t_top
        for ln in lines:
            d.text((W / 2 - text_w(f_title, ln, track) / 2, yy), ln, font=f_title,
                   fill=fill, stroke_width=max(1, tsize // 30), stroke_fill=(0, 0, 0, 255))
            yy += lh

    # garis aksen di bawah judul
    if not minimal:
        ry = int(min(t_end + H * 0.014, bill_y * H - H * 0.02))
        d.rectangle([W / 2 - W * 0.11, ry, W / 2 + W * 0.11, ry + max(2, H * 0.003)],
                    fill=(*accent, 230))

    # --- billing block + strip rilis ---
    if not minimal:
        f_bill = get_font("condensed", max(9, int(H * 0.0155)))
        btxt = _billing_text(title_text, cast, director)
        for i, ln in enumerate(_wrap_width(btxt, f_bill, W * 0.9)[:2]):
            d.text((W / 2 - f_bill.getlength(ln) / 2, H * bill_y + i * H * 0.021), ln,
                   font=f_bill, fill=(225, 225, 225, 215))
        if rel_y:
            f_rel = get_font("condensed", max(11, int(H * 0.022)))
            draw_tracked(d, W / 2, int(H * rel_y), release, f_rel, (250, 250, 250, 245),
                         tracking=max(3, int(H * 0.007)), shadow=(1, 1, (0, 0, 0, 170)))
            bw = max(text_w(f_rel, release, max(3, int(H * 0.007))), W * 0.2)
            d.rectangle([W / 2 - bw / 2, H * rel_y + H * 0.026,
                         W / 2 + bw / 2, H * rel_y + H * 0.026 + max(2, H * 0.0025)],
                        fill=(*accent, 200))
        if std_y:
            f_std = get_font("condensed", max(8, int(H * 0.012)))
            draw_tracked(d, W / 2, int(H * std_y), studio, f_std, (210, 210, 210, 140),
                         tracking=max(2, int(H * 0.004)))

    img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
    return img


# ---------------------------------------------------------------------------
# Adegan placeholder (untuk thumbnail galeri referensi)
# ---------------------------------------------------------------------------
def placeholder_scene(w, h, palette, seed=3):
    rng = random.Random(seed)
    dark = tuple(int(c * 0.35) for c in palette["highlight"])
    sky_top = tuple(int(c * 0.5) for c in palette["shadow"])
    base = _vgrad_strip(sky_top, dark, w, h)
    d = ImageDraw.Draw(base)
    # bulan / matahari
    r = int(min(w, h) * 0.11)
    mx, my = int(w * rng.uniform(0.3, 0.7)), int(h * rng.uniform(0.16, 0.3))
    d.ellipse([mx - r, my - r, mx + r, my + r], fill=palette["accent"])
    glow = base.filter(ImageFilter.GaussianBlur(w * 0.06))
    base = Image.blend(base, glow, 0.35)
    d = ImageDraw.Draw(base)
    # bintang
    for _ in range(int(w * h / 900)):
        x, y = rng.randrange(w), rng.randrange(int(h * 0.55))
        v = rng.randint(120, 220)
        d.point((x, y), fill=(v, v, min(255, v + 20)))
    # pegunungan 2 lapis
    for layer_i, dim in enumerate((0.55, 0.3)):
        col = tuple(int(c * dim) for c in palette["shadow"])
        pts = [(0, h)]
        y0 = h * (0.62 + 0.12 * layer_i)
        x = 0
        while x < w:
            step = max(4, w // 10)
            x2 = min(w, x + rng.randint(step, step * 2))
            pts.append((x2, y0 + rng.randint(-int(h * 0.09), int(h * 0.02))))
            x = x2
        pts.append((w, h))
        d.polygon(pts, fill=col)
    return base
