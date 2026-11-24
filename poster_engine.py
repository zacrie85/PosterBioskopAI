# -*- coding: utf-8 -*-
"""
PosterBioskopAI — mesin tipografi & finishing poster (Pillow, 100% offline).

Setelah AI menggambar key art (poster_ai.py), modul ini yang:
  1. memasang scrim gelap agar tulisan terbaca,
  2. menulis JUDUL (otomatis dari nama video) dengan auto-fit dan — penting —
     JAMINAN MARGIN AMAN: setiap baris teks diukur dan dipaksa muat di dalam
     batas kiri-kanan (max_width), tidak pernah melewati pinggir gambar,
  3. menambah tagline / pemain / sutradara bila diisi, garis aksen emas,
     strip rilis dan studio.

Ukuran output mengikuti rasio: 9:16 (Story/Reels), 16:9 (Layar), atau
mengikuti rasio video sumber.
"""

import math
import os

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

RESAMPLE = getattr(Image, "Resampling", Image).LANCZOS

# ---------------------------------------------------------------------------
# Font: pakai font bawaan aplikasi di assets/fonts dulu (Anton & Bebas Neue,
# gaya poster sinematik), lalu font Windows (Impact), lalu fallback bebas.
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIRS = [
    os.path.join(_HERE, "assets", "fonts"),
    "C:/Windows/Fonts",
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/truetype/liberation",
    "/usr/share/fonts",
]

FONT_CANDIDATES = {
    "display": ["Anton-Regular.ttf", "impact.ttf", "BebasNeue-Regular.ttf",
                "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"],
    "credit":  ["BebasNeue-Regular.ttf", "Anton-Regular.ttf",
                "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"],
    "serif":   ["BebasNeue-Regular.ttf", "georgiab.ttf",
                "DejaVuSerif-Bold.ttf", "LiberationSerif-Bold.ttf"],
}

_font_files = {}
_font_cache = {}


def _resolve_font_files():
    for role, names in FONT_CANDIDATES.items():
        for name in names:
            for d in FONT_DIRS:
                p = os.path.join(d, name)
                if os.path.isfile(p):
                    _font_files[role] = p
                    break
            if role in _font_files:
                break
    fallback = _font_files.get("display")
    for role in set(FONT_CANDIDATES):
        if _font_files.get(role) is None:
            _font_files[role] = fallback


def get_font(role, size):
    if not _font_files:
        _resolve_font_files()
    if _font_files.get(role) is None:
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


# ---------------------------------------------------------------------------
# Util gambar
# ---------------------------------------------------------------------------
def cover_crop(img, ratio, focus=0.45):
    """Potong gambar agar pas rasio (cover). focus: 0=atas, 0.5=tengah."""
    w, h = img.size
    if w / h > ratio:
        tw = int(h * ratio)
        x0 = (w - tw) // 2
        return img.crop((x0, 0, x0 + tw, h))
    th = int(w / ratio)
    y0 = int(max(0, min(h - th, (h - th) * focus)))
    return img.crop((0, y0, w, y0 + th))


def finish_art(img):
    """Sentuhan akhir ringan pasca-AI: kontras & warna sedikit dipertegas,
    plus grain film tipis. Tidak mengubah struktur gambar hasil AI."""
    img = ImageEnhance.Contrast(img).enhance(1.05)
    img = ImageEnhance.Color(img).enhance(1.08)
    img = ImageEnhance.Sharpness(img).enhance(1.15)
    return img


def _scrim(img, y_from, y_to, max_alpha, reverse=False):
    """Gradasi gelap dari y_from ke y_to (fraksi tinggi) untuk zona teks."""
    w, h = img.size
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    a, b = int(h * y_from), min(h, int(h * y_to))
    for y in range(a, b):
        t = (y - a) / max(1, (b - a))
        v = int(max_alpha * (1 - t) ** 1.3) if reverse else int(max_alpha * (t ** 1.3))
        d.line([(0, y), (w, y)], fill=v)
    m = m.filter(ImageFilter.GaussianBlur(max(2, int(h * 0.008))))
    return Image.composite(Image.new("RGB", (w, h), (0, 0, 0)), img, m)


# ---------------------------------------------------------------------------
# Util teks — SEMUA menghormati max_width (margin aman kiri/kanan)
# ---------------------------------------------------------------------------
def text_w(font, text, tracking=0):
    return font.getlength(text) + tracking * max(0, len(text) - 1)


def _wrap_lines(text, font, max_w, max_lines):
    """Pecah teks jadi baris-baris; setiap baris dijamin <= max_w.
    Kata lebih panjang dari max_w (kasus ekstrem) dipotong dengan tanda -."""
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
    if len(lines) > max_lines:                       # terlalu banyak baris
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(" -") + "…"
    # kata tunggal raksasa -> potong karakter per karakter agar tetap <= max_w
    fixed = []
    for ln in lines:
        while font.getlength(ln) > max_w and len(ln) > 4:
            ln = ln[:-2].rstrip(" -") + "…"
        fixed.append(ln)
    return fixed


def fit_title(text, role, max_w, max_h, start_size, min_size=18, max_lines=3):
    """Cari ukuran font terbesar agar JUDUL muat dalam max_w x max_h
    dengan <= max_lines baris. Ini yang menjamin tulisan tidak melewati batas."""
    size = int(start_size)
    while size >= min_size:
        font = get_font(role, size)
        lines = _wrap_lines(text, font, max_w, max_lines)
        lh = size * 1.12
        if len(lines) * lh <= max_h and all(l for l in lines):
            return font, lines, size, lh
        size = int(size * 0.93)
    font = get_font(role, min_size)
    return font, _wrap_lines(text, font, max_w, max_lines), min_size, min_size * 1.12


def draw_tracked(d, cx, y, text, font, fill, tracking=0, shadow=None):
    """Teks ber-letter-spacing, dipusatkan di cx (dipakai hanya bila sudah
    pasti muat; cek lebar sebelum memanggil)."""
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
        d.text((xx, y), ch, font=font, fill=fill)
        xx += font.getlength(ch) + tracking
    return w


def _tracked_fit(text, font, max_w, base_tracking):
    """Kurangi letter-spacing sampai teks muat dalam max_w."""
    tr = base_tracking
    while tr > 0 and text_w(font, text, tr) > max_w:
        tr = int(tr * 0.7)
    if text_w(font, text, tr) <= max_w:
        return tr
    return 0


# ---------------------------------------------------------------------------
# Komposisi akhir: key art AI + teks
# ---------------------------------------------------------------------------
def compose_poster(art, title, size=(1080, 1920), tagline="", pemain="",
                   sutradara="", studio="POSTER BIOSKOP PICTURES",
                   release="SEGERA DI BIOSKOP", seed=7, template=None):
    """Susun poster final: key art AI + tipografi dengan margin aman.
    Kalau `template` diisi (path file di folder templates/ atau path
    langsung), susunan visual mengikuti template itu (template_engine).
    Return PIL RGB image berukuran `size`."""
    if template:
        import template_engine                       # hindari impor melingkar
        return template_engine.compose(art, title, template, size=size,
                                       tagline=tagline, pemain=pemain,
                                       sutradara=sutradara, release=release,
                                       studio=studio)
    W, H = size
    art = ImageOps.exif_transpose(art).convert("RGB")
    art = cover_crop(art, W / H, focus=0.45).resize((W, H), RESAMPLE)
    img = finish_art(art)

    landscape = W > H
    img = _scrim(img, 0.42 if not landscape else 0.52, 1.0, 215)
    if pemain:
        img = _scrim(img, 0.0, 0.13, 150, reverse=True)

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    # ====== MARGIN AMAN: semua teks dipaksa muat di dalam [margin, W-margin] ======
    margin = max(int(W * 0.055), int(min(W, H) * 0.05), 24)
    max_w = W - 2 * margin
    cx = W / 2

    gold = (242, 193, 78, 255)

    # --- nama pemain (opsional, zona atas) ---
    if pemain:
        f_cast = get_font("credit", max(12, int(H * 0.020)))
        names = "   ·   ".join(p.strip().upper() for p in pemain.split(",") if p.strip())
        tr = _tracked_fit(names, f_cast, max_w, max(2, int(H * 0.004)))
        if text_w(f_cast, names, tr) <= max_w:
            draw_tracked(d, cx, int(H * 0.045), names, f_cast, (245, 245, 245, 230),
                         tracking=tr, shadow=(1, 1, (0, 0, 0, 170)))

    # --- judul: auto-fit, 1-3 baris, dijamin <= max_w ---
    title_text = (title or "").strip().upper() or "TANPA JUDUL"
    start = int(H * (0.155 if landscape else 0.135))
    max_h_title = H * (0.30 if landscape else 0.27)
    f_title, lines, tsize, lh = fit_title(title_text, "display", max_w, max_h_title,
                                          start, max_lines=3)
    bottom_anchor = H * (0.90 if not sutradara and not release else 0.885)
    y_top = bottom_anchor - lh * len(lines)

    # bayangan lembut judul
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sh)
    yy = y_top
    for ln in lines:
        ds.text((cx - text_w(f_title, ln) / 2 + max(2, tsize * 0.05),
                 yy + max(3, tsize * 0.06)), ln, font=f_title, fill=(0, 0, 0, 220))
        yy += lh
    sh = sh.filter(ImageFilter.GaussianBlur(max(2, int(tsize * 0.03))))
    img = Image.alpha_composite(img.convert("RGBA"), sh).convert("RGB")

    # judul itu sendiri
    yy = y_top
    for ln in lines:
        d.text((cx - text_w(f_title, ln) / 2, yy), ln, font=f_title,
               fill=(247, 246, 244, 255))
        yy += lh
    t_end = yy

    # garis aksen emas di bawah judul (selalu di dalam margin)
    ry = int(min(t_end + H * 0.012, H * 0.915))
    d.rectangle([cx - max_w * 0.16, ry, cx + max_w * 0.16, ry + max(2, int(H * 0.003))],
                fill=gold)

    # --- tagline (opsional, di atas judul) ---
    if tagline and tagline.strip():
        f_tag = get_font("serif", max(12, int(H * 0.024)))
        t = "“" + tagline.strip().upper() + "”"
        tr = _tracked_fit(t, f_tag, max_w, max(1, int(H * 0.002)))
        ty = max(int(H * 0.62), int(y_top - H * 0.055))
        if text_w(f_tag, t, tr) <= max_w:
            draw_tracked(d, cx, ty, t, f_tag, (*gold[:3], 235),
                         tracking=tr, shadow=(1, 1, (0, 0, 0, 170)))

    # --- billing block (opsional): pemain & sutradara, kecil di bawah judul ---
    if pemain or sutradara:
        f_bill = get_font("credit", max(10, int(H * 0.016)))
        segs = []
        if pemain:
            segs.append("DIBINTANGI " + ", ".join(
                p.strip().upper() for p in pemain.split(",") if p.strip()))
        if sutradara and sutradara.strip():
            segs.append("SUTRADARA " + sutradara.strip().upper())
        btxt = "   ".join(segs)
        by = ry + max(6, int(H * 0.018))
        for ln in _wrap_lines(btxt, f_bill, max_w, 2):
            d.text((cx - f_bill.getlength(ln) / 2, by), ln,
                   font=f_bill, fill=(228, 228, 228, 210))
            by += H * 0.020
            ry = by                                  # geser strip rilis ke bawah
    # --- strip rilis + studio ---
    y_strip = min(H * 0.955, H - int(H * 0.033))
    if release and release.strip():
        f_rel = get_font("credit", max(12, int(H * 0.022)))
        tr = _tracked_fit(release.strip().upper(), f_rel, max_w, max(3, int(H * 0.007)))
        rw = text_w(f_rel, release.strip().upper(), tr)
        draw_tracked(d, cx, int(y_strip), release.strip().upper(), f_rel,
                     (250, 250, 250, 245), tracking=tr, shadow=(1, 1, (0, 0, 0, 170)))
        d.rectangle([cx - rw / 2, y_strip + H * 0.026, cx + rw / 2,
                     y_strip + H * 0.026 + max(2, int(H * 0.0025))], fill=gold)
    if studio and studio.strip():
        f_std = get_font("credit", max(9, int(H * 0.012)))
        s = studio.strip().upper()
        tr = _tracked_fit(s, f_std, max_w, max(2, int(H * 0.004)))
        draw_tracked(d, cx, int(H * 0.985) - f_std.size, s, f_std,
                     (215, 215, 215, 150), tracking=tr)

    img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
    return img


def preview_size(rasio_full, max_h=760, max_w=920):
    """Ukuran preview yang pas di jendela (menjaga rasio)."""
    w, h = rasio_full
    r = w / h
    pw, ph = int(max_h * r), max_h
    if pw > max_w:
        pw, ph = max_w, int(max_w / r)
    return (max(2, pw // 2 * 2), max(2, ph // 2 * 2))
