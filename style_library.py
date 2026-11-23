# -*- coding: utf-8 -*-
"""
PosterBioskopAI — perpustakaan 999 referensi gaya poster Hollywood + mesin
pencocok otomatis (auto-match). Semuanya di-generate prosedural dan deterministik,
jadi 100% offline, tanpa berhak cipta poster film asli.
"""

import colorsys
import hashlib
import math

# ---------------------------------------------------------------------------
# Dimensi gaya: 7 genre x 6 era x 8 palet x 3 komposisi = 1008 -> dipotong 999
# ---------------------------------------------------------------------------
GENRES = [
    ("action", "AKSI"),
    ("scifi", "SCI-FI"),
    ("horror", "HORROR"),
    ("thriller", "THRILLER"),
    ("romance", "ROMANS"),
    ("comedy", "KOMEDI"),
    ("adventure", "PETUALANGAN"),
]

ERAS = [
    ("70s", "Grindhouse 70-an"),
    ("80s", "Blokbuster 80-an"),
    ("90s", "Noir 90-an"),
    ("00s", "Epik 2000-an"),
    ("10s", "Indie 2010-an"),
    ("20s", "Teaser Modern"),
]

LAYOUTS = ["bottom", "split", "center"]
FILL_BY_LAYOUT = {"bottom": "gradient", "split": "accent", "center": "white"}
FONT_BY_ERA = {"70s": "block", "80s": "block", "90s": "impact",
               "00s": "impact", "10s": "serif", "20s": "impact"}

# Palet dasar per genre: (nama, shadow, highlight, accent)
PALETTE_SEEDS = {
    "action":    ("Teal-Orange", (8, 40, 66), (255, 160, 64), (255, 196, 84)),
    "scifi":     ("Nebula", (10, 14, 52), (120, 220, 255), (110, 200, 255)),
    "horror":    ("Daruh", (12, 24, 14), (140, 200, 90), (190, 40, 30)),
    "thriller":  ("Asap Kota", (16, 20, 28), (170, 190, 210), (200, 190, 120)),
    "romance":   ("Senja Mawar", (70, 20, 44), (255, 200, 190), (255, 140, 150)),
    "comedy":    ("Pasar Ceria", (40, 30, 10), (255, 220, 110), (255, 170, 60)),
    "adventure": ("Cakrawala", (20, 36, 52), (255, 190, 90), (255, 205, 110)),
}

# Varian palet: (nama, geser_hue, geser_saturasi, geser_kecerahan)
PALETTE_VARIANTS = [
    ("Klasik", 0.0, 0.0, 0.0),
    ("Neon", 0.07, 0.18, 0.06),
    ("Malam", -0.45, 0.05, -0.18),
    ("Fajar", 0.12, -0.12, 0.12),
    ("Gelap", 0.02, -0.22, -0.20),
    ("Emas", 0.48, -0.05, 0.10),
    ("Es", -0.72, -0.10, 0.06),
    ("Api", 0.85, 0.16, 0.02),
]

GENRE_GRADE = {
    "action":    dict(bri=1.00, con=1.12, sat=1.12, shadow_k=0.38, hl_k=0.30, focus=0.42),
    "scifi":     dict(bri=0.96, con=1.08, sat=1.00, shadow_k=0.45, hl_k=0.28, focus=0.42),
    "horror":    dict(bri=0.85, con=1.18, sat=0.72, shadow_k=0.55, hl_k=0.12, focus=0.38),
    "thriller":  dict(bri=0.92, con=1.15, sat=0.68, shadow_k=0.45, hl_k=0.15, focus=0.40),
    "romance":   dict(bri=1.05, con=0.95, sat=1.05, shadow_k=0.30, hl_k=0.38, focus=0.40),
    "comedy":    dict(bri=1.08, con=0.98, sat=1.15, shadow_k=0.22, hl_k=0.30, focus=0.35),
    "adventure": dict(bri=1.02, con=1.06, sat=1.10, shadow_k=0.34, hl_k=0.32, focus=0.40),
}

ERA_FX = {
    "70s": dict(grain=0.45, vignette=0.52, bloom=0.10, sat=1.12, con=1.10),
    "80s": dict(grain=0.20, vignette=0.40, bloom=0.30, sat=1.20, con=1.06),
    "90s": dict(grain=0.24, vignette=0.44, bloom=0.10, sat=0.88, con=1.14),
    "00s": dict(grain=0.12, vignette=0.36, bloom=0.20, sat=1.04, con=1.10),
    "10s": dict(grain=0.16, vignette=0.30, bloom=0.08, sat=0.78, con=0.96),
    "20s": dict(grain=0.08, vignette=0.30, bloom=0.16, sat=1.00, con=1.05),
}

# Profil afinitas: statistik gambar seperti apa yang cocok dengan genre ini.
# bri=kecerahan, con=kontras, sat=saturasi, warm=hangat/dingin, dark=fraksi gelap
GENRE_AFFINITY = {
    "action":    dict(bri=0.50, con=0.62, sat=0.50, warm=0.05,  dark=0.24),
    "scifi":     dict(bri=0.40, con=0.55, sat=0.38, warm=-0.12, dark=0.32),
    "horror":    dict(bri=0.30, con=0.60, sat=0.28, warm=-0.02, dark=0.42),
    "thriller":  dict(bri=0.36, con=0.58, sat=0.22, warm=-0.05, dark=0.34),
    "romance":   dict(bri=0.62, con=0.42, sat=0.46, warm=0.14,  dark=0.14),
    "comedy":    dict(bri=0.66, con=0.40, sat=0.55, warm=0.08,  dark=0.10),
    "adventure": dict(bri=0.55, con=0.50, sat=0.50, warm=0.06,  dark=0.18),
}

ERA_AFFINITY_DELTA = {
    "70s": dict(sat=0.08, dark=0.05, bri=-0.04),
    "80s": dict(sat=0.05),
    "90s": dict(sat=-0.06, bri=-0.03),
    "00s": dict(),
    "10s": dict(sat=-0.08, con=-0.05),
    "20s": dict(bri=0.03),
}

TOTAL_STYLES = 999


# ---------------------------------------------------------------------------
# Util warna
# ---------------------------------------------------------------------------
def _shift(rgb, dh, ds, dv):
    r, g, b = [c / 255.0 for c in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    h = (h + dh) % 1.0
    l = min(0.92, max(0.05, l + dv * 0.5))
    s = min(1.0, max(0.0, s + ds * 0.5))
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return tuple(int(round(c * 255)) for c in (r, g, b))


def _palette_variants(seed):
    name, shadow, highlight, accent = seed
    out = []
    for vname, dh, ds, dv in PALETTE_VARIANTS:
        sh = _shift(shadow, dh, ds, dv)
        hl = _shift(highlight, dh, ds, dv)
        ac = _shift(accent, dh, ds, dv)
        g1 = _shift(accent, dh, ds, 0.22)            # ujung atas judul: aksen terang
        g2 = tuple(min(255, int(c * 0.35 + 165)) for c in ac)  # ujung bawah: menyatu ke putih
        out.append({
            "name": f"{name} {vname}",
            "shadow": sh, "highlight": hl, "accent": ac,
            "title_grad": [g1, g2],
        })
    return out


def _clamp01(v):
    return min(1.0, max(0.0, v))


# ---------------------------------------------------------------------------
# Bangun perpustakaan
# ---------------------------------------------------------------------------
def build_library():
    styles = []
    for gkey, glabel in GENRES:
        pals = _palette_variants(PALETTE_SEEDS[gkey])
        for ekey, elabel in ERAS:
            era_fx = ERA_FX[ekey]
            for pal in pals:
                for lay in LAYOUTS:
                    if len(styles) >= TOTAL_STYLES:
                        return styles
                    idx = len(styles) + 1
                    g = GENRE_GRADE[gkey]
                    aff = {k: GENRE_AFFINITY[gkey][k] + ERA_AFFINITY_DELTA[ekey].get(k, 0)
                           for k in GENRE_AFFINITY[gkey]}
                    aff = {k: (_clamp01(v) if k != "warm" else max(-1.0, min(1.0, v)))
                           for k, v in aff.items()}
                    sat = min(1.7, g["sat"] * era_fx["sat"])
                    con = min(1.8, g["con"] * era_fx["con"])
                    styles.append({
                        "id": f"REF-{idx:03d}",
                        "index": idx,
                        "name": f"{glabel} · {elabel} · {pal['name']}",
                        "genre": gkey, "genre_label": glabel,
                        "era": ekey, "era_label": elabel,
                        "layout": lay,
                        "palette": pal,
                        "grading": {
                            "bri": g["bri"], "con": con, "sat": sat,
                            "shadow": pal["shadow"], "highlight": pal["highlight"],
                            "shadow_k": g["shadow_k"], "hl_k": g["hl_k"],
                        },
                        "fx": {
                            "grain": era_fx["grain"], "vignette": era_fx["vignette"],
                            "bloom": era_fx["bloom"], "letterbox": ekey == "20s",
                        },
                        "typo": {
                            "font_role": FONT_BY_ERA[ekey],
                            "case": "upper",
                            "title_fill": FILL_BY_LAYOUT[lay],
                        },
                        "focus": g["focus"],
                        "affinity": aff,
                        "tags": [gkey, glabel.lower(), ekey, elabel.lower(),
                                 pal["name"].lower(), lay],
                    })
    return styles


_LIB = None


def library():
    global _LIB
    if _LIB is None:
        _LIB = build_library()
    return _LIB


def by_id(style_id):
    for s in library():
        if s["id"] == style_id:
            return s
    return None


def filter_styles(genre=None, era=None, query=None):
    q = (query or "").strip().lower()
    out = []
    for s in library():
        if genre and s["genre"] != genre:
            continue
        if era and s["era"] != era:
            continue
        if q and q not in s["name"].lower() and not any(q in t for t in s["tags"]):
            continue
        out.append(s)
    return out


# ---------------------------------------------------------------------------
# Analisis gambar + auto-match ("AI" lokal, deterministik, offline)
# ---------------------------------------------------------------------------
def analyze_image(img):
    """Statistik visual: kecerahan, kontras, saturasi, kehangatan, area gelap."""
    im = img.convert("RGB").resize((96, 96))
    total = 96 * 96
    g = im.convert("L")
    hist = g.histogram()
    mean = sum(i * c for i, c in enumerate(hist)) / total
    bri = mean / 255.0
    var = sum(((i - mean) ** 2) * c for i, c in enumerate(hist)) / total
    con = min(1.0, (var ** 0.5) / 70.0)
    dark = sum(c for i, c in enumerate(hist) if i < 60) / total

    hsv_hist = im.convert("HSV").histogram()
    sat = sum(i * c for i, c in enumerate(hsv_hist[256:512])) / total / 255.0

    r_h, g_h, b_h = im.split()[0].histogram(), im.split()[1].histogram(), im.split()[2].histogram()
    rm = sum(i * c for i, c in enumerate(r_h)) / total
    bm = sum(i * c for i, c in enumerate(b_h)) / total
    warm = (rm - bm) / 255.0
    return {"bri": bri, "con": con, "sat": sat, "warm": warm, "dark": dark}


_SIGMA = {"bri": 0.18, "con": 0.22, "sat": 0.22, "warm": 0.18, "dark": 0.20}


def match_styles(stats, top_n=8, library_override=None):
    """Beri skor semua 999 gaya terhadap statistik foto/video. Hasil: [(skor, style)]."""
    lib = library_override if library_override is not None else library()
    scored = []
    for s in lib:
        a = s["affinity"]
        score = 0.0
        for k, sig in _SIGMA.items():
            d = (stats[k] - a[k]) / sig
            score += math.exp(-0.5 * d * d)
        score /= len(_SIGMA)
        # tie-break deterministik supaya urutan stabil & bervariasi
        jitter = int(hashlib.md5(s["id"].encode()).hexdigest()[:4], 16) / 65535.0
        score += (jitter - 0.5) * 0.02
        scored.append((score, s))
    scored.sort(key=lambda t: -t[0])
    return scored[:top_n]


def _deskripsi_stats(s):
    p = []
    if s["bri"] < 0.35:
        p.append("foto cenderung gelap")
    elif s["bri"] > 0.62:
        p.append("foto terang")
    if s["con"] > 0.55:
        p.append("kontras tinggi")
    elif s["con"] < 0.30:
        p.append("kontras lembut")
    if s["sat"] > 0.45:
        p.append("warna kuat")
    elif s["sat"] < 0.18:
        p.append("warna kalem")
    if s["warm"] > 0.06:
        p.append("nuansa hangat")
    elif s["warm"] < -0.06:
        p.append("nuansa dingin")
    if s["dark"] > 0.32:
        p.append("banyak area gelap")
    return p[:3]


def explain_match(stats, style):
    p = _deskripsi_stats(stats)
    if not p:
        p = ["karakter gambarnya seimbang"]
    return "Karena " + " dan ".join(p) + " → dipadukan dengan gaya " + style["name"]
