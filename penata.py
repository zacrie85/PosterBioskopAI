# -*- coding: utf-8 -*-
"""Penata AI — PosterBioskopAI v2.4.0.

Membaca key art poster lalu memutuskan: warna aksen, gaya judul, kekuatan
scrim (penjaga kontras), dan bingkai yang paling cocok.

Cara kerjanya jujur & lokal: bukan jaringan syaraf baru yang harus diunduh,
melainkan ANALISIS PENGUKURAN gambar dengan numpy — palet dominan (k-means),
kecerahan, saturasi, kehangatan warna, keramaian tepi, dan kecerahan di zona
judul. Dari ukuran-ukuran itu diputuskan gaya seperti tata letak yang dilakukan
desainer poster. 100% offline, instan (± 50 ms), tanpa unduhan baru.
"""
import numpy as np
from PIL import Image, ImageFilter

GOLD_KLASIK = (242, 193, 78)
PUTIH_POSTER = (247, 246, 244)

OTOMATIS_BINGKAI = "Otomatis (dari gambar)"
TANPA_BINGKAI = "Tanpa bingkai"


def _lum(c):
    r, g, b = c
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0


def analisa_gambar(art):
    """Analisis key art. Return dict: palet (urut dominan), lum, sat, warm,
    ramai (kerapatan tepi), lum_judul (kecerahan zona judul), mood."""
    im = art.convert("RGB")
    w, h = im.size
    kecil = im.resize((80, max(8, int(80 * h / w))))
    a = np.asarray(kecil, dtype=np.float32)
    hh, ww, _ = a.shape
    px = a.reshape(-1, 3)

    # --- palet dominan: k-means ringan k=5 (deterministik) ---
    rng = np.random.default_rng(7)
    idx = rng.choice(len(px), size=5, replace=False)
    centers = px[idx]
    lab = np.zeros(len(px), dtype=np.int32)
    for _ in range(8):
        d = ((px[:, None, :] - centers[None, :, :]) ** 2).sum(-1)
        lab = d.argmin(1)
        for k in range(centers.shape[0]):
            m = lab == k
            if m.any():
                centers[k] = px[m].mean(0)
    freq = np.bincount(lab, minlength=centers.shape[0])
    urut = freq.argsort()[::-1]
    palet = [tuple(int(v) for v in centers[i]) for i in urut]

    # --- metrik gambar (luminance 0-1) ---
    lum = (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]) / 255.0
    lum_rata = float(lum.mean())
    sat = float((a.max(-1) - a.min(-1)).mean() / 255.0)
    hangat = float((a[..., 0].mean() - a[..., 2].mean()) / 255.0)
    tepi = np.asarray(kecil.convert("L").filter(ImageFilter.FIND_EDGES),
                      dtype=np.float32) / 255.0
    ramai = float(tepi.mean())
    lum_judul = float(lum[int(hh * 0.62):int(hh * 0.92), :].mean())

    # --- mood ---
    if ramai > 0.30 and sat > 0.22:
        mood = "ramai-aksi"
    elif lum_rata > 0.62:
        mood = "terang-ceria"
    elif lum_rata < 0.32:
        mood = "gelap-dramatis"
    elif hangat > 0.06:
        mood = "hangat-romantis"
    else:
        mood = "dingin-misterius"

    return {"palet": palet, "lum": lum_rata, "sat": sat, "warm": hangat,
            "ramai": ramai, "lum_judul": lum_judul, "mood": mood}


def pilih_akses(analisa):
    """Pilih warna aksen dari palet: warna paling jelas yang BUKAN latar
    dominan dan cukup terang untuk garis/hiasan. Fallback: emas klasik."""
    kandidat = analisa["palet"][1:] if len(analisa["palet"]) > 1 else []
    ambang = max(0.25, analisa["lum"] + 0.08)   # harus lebih terang dari latar
    terbaik, skor_b = None, -1.0
    for c in kandidat:
        l = _lum(c)
        sat = (max(c) - min(c)) / 255.0
        if l < ambang or l > 0.86:          # terlalu gelap / hampir putih
            continue
        skor = sat * 2.0 + (1.0 - abs(l - 0.55))
        if skor > skor_b:
            terbaik, skor_b = tuple(int(v) for v in c), skor
    if terbaik is None:
        terbaik = GOLD_KLASIK
    return terbaik


def pilih_tipografi(analisa, gaya_pref="Otomatis (menyesuaikan judul)",
                    klasik=False):
    """Keputusan tipografi dari hasil analisis. Return dict:
    utama  : warna judul (RGB)
    aksen  : warna aksen/garis (RGB)
    gaya   : label gaya judul (None = ikuti aturan panjang judul)
    scrim  : kekuatan scrim zona judul (190-240) — penjaga kontras
    klasik=True (atau pengguna memilih "Klasik (putih-emas)") -> warna
    putih-emas bawaan dan scrim standar, tanpa penyesuaian gambar."""
    if klasik:
        return {"utama": PUTIH_POSTER, "aksen": GOLD_KLASIK, "gaya": None,
                "scrim": 215}
    aksen = pilih_akses(analisa)

    # penjaga kontras: latar judul terang -> scrim lebih kuat
    lj = analisa["lum_judul"]
    scrim = 200
    if lj > 0.50:
        scrim = 218
    if lj > 0.66:
        scrim = 236
    if analisa["ramai"] > 0.32:
        scrim = min(245, scrim + 12)

    # gaya dari mood (hanya saat pengguna memilih Otomatis):
    mood = analisa["mood"]
    gaya = {"gelap-dramatis": "Miring (kata akhir aksen)",
            "terang-ceria": "Klasik (seragam besar)",
            "ramai-aksi": "Menonjol (kata penting besar)",
            "hangat-romantis": "Miring (kata akhir aksen)",
            "dingin-misterius": "Menonjol (kata penting besar)"}.get(mood)
    return {"utama": PUTIH_POSTER, "aksen": aksen, "gaya": gaya,
            "scrim": scrim}


def pilih_bingkai(analisa, prefer=OTOMATIS_BINGKAI):
    """Resolve pilihan bingkai. Return (nama_bingkai_atau_None, mood)."""
    p = (prefer or OTOMATIS_BINGKAI).strip()
    if p.lower().startswith("tanpa"):
        return None, analisa["mood"]
    if not p.lower().startswith("otomatis"):
        return p, analisa["mood"]           # nama gaya eksplisit dari GUI/CLI
    bingkai_mood = {"gelap-dramatis": "Neon glow",
                    "ramai-aksi": "Splat aksen",
                    "terang-ceria": "Halftone",
                    "hangat-romantis": "Gradien warna",
                    "dingin-misterius": "Art deco"}
    return bingkai_mood.get(analisa["mood"], "Garis klasik"), analisa["mood"]
