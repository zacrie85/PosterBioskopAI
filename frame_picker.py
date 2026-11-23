# -*- coding: utf-8 -*-
"""
PosterBioskopAI — ekstraksi frame terbaik dari video (OpenCV) + judul otomatis
yang diambil dari nama file video.

Cara kerja pemilihan frame:
  - video disampling merata (menghindari 3% awal & 6% akhir yang sering hitam),
  - tiap sampel dinilai: ketajaman (variance of Laplacian) x kecocokan exposure
    x kontras,
  - frame dengan skor tertinggi dipakai sebagai bahan poster,
  - statistik warna keseluruhan diambil dari rata-rata sampel, untuk auto-match gaya.
"""

import math
import os
import re

import cv2
import numpy as np
from PIL import Image

VIDEO_EXTS = (".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".mpg", ".mpeg", ".ts", ".wmv", ".3gp")

# Kata kecil yang hurufnya tetap kecil saat dibuat judul
_SMALL_WORDS = {"di", "ke", "dari", "dan", "yang", "untuk", "pada", "dengan",
                "the", "of", "a", "an", "vs", "in", "on", "at", "to"}

# Prefiks nama file kamera/HP yang dibuang agar judul bersih
_PREFIX_RE = re.compile(
    r"^(vid|video|img|image|mov|movie|rec|recording|new|photo|snap|screenshot|"
    r"whatsapp[\s_-]*video|wa[\s_-]*video)[\s_-]+", re.IGNORECASE)


def title_from_filename(path):
    """Bersihkan nama file video jadi judul poster: 'VID_20240102_lomba_fisika'
    -> 'Lomba Fisika'. Hasil tetap bisa diedit manual di aplikasi."""
    stem = os.path.splitext(os.path.basename(str(path)))[0]
    t = _PREFIX_RE.sub("", stem)
    t = re.sub(r"[_\-.]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    tokens = t.split()
    # buang angka/tanggal (timestamp kamera) selama masih ada kata huruf tersisa
    alpha = [w for w in tokens if not re.fullmatch(r"\d+", w)]
    if not alpha or not any(len(w) >= 3 for w in alpha):
        return "Tanpa Judul"     # nama file kamera murni angka/tanggal -> tanpa judul
    tokens = alpha
    out = []
    for i, w in enumerate(tokens):
        if w.isupper() and len(w) > 1:      # hormati singkatan, mis. "HD", "VIP"
            out.append(w)
            continue
        m = re.fullmatch(r"([a-z]{1,5})(\d{1,4})", w.lower())
        if m:                               # akronim+angka: "jkt48" -> "JKT48"
            out.append(m.group(1).upper() + m.group(2))
            continue
        lw = w.lower()
        if i > 0 and lw in _SMALL_WORDS:
            out.append(lw)
        else:
            out.append(lw[:1].upper() + lw[1:])
    res = " ".join(out).strip()
    return res if res else "Tanpa Judul"


def _frame_stats(frame_bgr):
    small = cv2.resize(frame_bgr, (96, 96), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY).astype(np.float64)
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV).astype(np.float64)
    bri = float(gray.mean()) / 255.0
    con = min(1.0, float(gray.std()) / 70.0)
    dark = float((gray < 60).mean())
    sat = float(hsv[:, 1, 0].mean()) / 255.0
    b_ch = small[:, :, 0].astype(np.float64).mean()
    r_ch = small[:, :, 2].astype(np.float64).mean()
    warm = (r_ch - b_ch) / 255.0
    sharp = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    return {"bri": bri, "con": con, "sat": sat, "warm": warm, "dark": dark, "sharp": sharp}


def extract_best_frame(video_path, max_samples=48, progress=None):
    """Ambil frame terbaik dari video.

    Returns:
        (PIL.Image frame, stats gabungan, info dict)
        stats = statistik warna ringan (tidak dipakai AI, disimpan untuk info).
    Raises:
        ValueError bila video tidak bisa dibuka.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Video tidak bisa dibuka: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total / fps if total and fps else 0.0

    if total > 8:
        a = int(total * 0.03)
        b = max(a + 2, int(total * 0.94))
        idxs = np.unique(np.linspace(a, b, max_samples).astype(int))
    else:
        idxs = None  # video pendek: baca berurutan

    samples = []
    pos = 0
    while True:
        if idxs is None:
            ok, frame = cap.read()
            if not ok:
                break
            fi = pos
            pos += 1
        else:
            if pos >= len(idxs):
                break
            fi = int(idxs[pos])
            pos += 1
            cap.set(cv2.CAP_PROP_POS_FRAMES, fi)
            ok, frame = cap.read()
            if not ok:
                continue
        st = _frame_stats(frame)
        st["frame"] = fi
        samples.append(st)
        if progress:
            progress(pos / (len(idxs) if idxs is not None else max_samples))
        if idxs is None and pos >= max_samples:
            break
    cap.release()

    if not samples:
        raise ValueError("Tidak ada frame yang bisa dibaca dari video ini.")

    # skor: ketajaman x faktor exposure x bonus kontras
    for st in samples:
        expo = max(0.15, 1.0 - abs(st["bri"] - 0.5) * 1.4)
        st["score"] = math.log1p(st["sharp"]) * expo * (0.45 + 0.55 * st["con"])
        del st["sharp"]

    samples.sort(key=lambda s: -s["score"])
    best = samples[0]
    # statistik gaya: rata-rata 30% sampel teratas (mewakili tampilan video)
    top = samples[: max(1, int(math.ceil(len(samples) * 0.3)))]
    stats = {k: float(np.mean([s[k] for s in top]))
             for k in ("bri", "con", "sat", "warm", "dark")}

    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, best["frame"])
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise ValueError("Frame terbaik tidak bisa dibaca ulang.")

    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    info = {
        "frame": best["frame"],
        "waktu_detik": round(best["frame"] / fps, 2) if fps else 0,
        "skor": round(best["score"], 2),
        "durasi_detik": round(duration, 1),
        "jumlah_sampel": len(samples),
    }
    return img, stats, info


def is_video(path):
    return str(path).lower().endswith(VIDEO_EXTS)
