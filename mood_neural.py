# -*- coding: utf-8 -*-
"""Mood neural (CLIP) — PosterBioskopAI v2.6.0.

Deteksi mood poster oleh jaringan syaraf sungguhan: CLIP ViT-B/32 (ONNX,
terkuantisasi ± 89 MB) menjalankan TOWER VISION di komputer pengguna; tower
teks TIDAK perlu — embedding teks untuk 5 mood sudah dihitung sebelumnya dan
ikut dalam aplikasi (mood_embeddings.npz, ± 4 KB). Sama tokenizer CLIP yang
sudah ada di aplikasi untuk SD-Turbo (kosakata identik).

Jika model belum diunduh, aplikasi otomatis memakai analisis statistik
(penata.analisa_gambar) — fitur mood neural murni penambah presisi.
"""
import json
import os
import threading
import urllib.request
import zipfile

import numpy as np
from PIL import Image

NAMA_ASSET = "PosterBioskopAI-Mood-CLIP.zip"
URL_RILIS = ("https://github.com/zacrie85/PosterBioskopAI/releases/"
             "latest/download/" + NAMA_ASSET)
LABELS = ("gelap-dramatis", "terang-ceria", "hangat-romantis",
          "dingin-misterius", "ramai-aksi")
AMBANG = 0.40          # p mood neural dipakai bila probabilitas >= ini

_lock = threading.Lock()
_sesi = None
_embed = None

# normalisasi CLIP standar
_MEAN = np.array([0.48145466, 0.4578275, 0.40821073], dtype=np.float32)
_STD = np.array([0.26862954, 0.26130258, 0.27577711], dtype=np.float32)


def berkas_model():
    """Lokasi onnx vision: <model_dir>/clip/mood_vision.onnx."""
    import poster_ai
    return os.path.join(poster_ai.model_dir(), "clip", "mood_vision.onnx")


def siap():
    p = berkas_model()
    try:
        import onnxruntime                       # noqa: F401
        return os.path.exists(p) and os.path.getsize(p) > 1_000_000
    except Exception:                            # noqa: BLE001
        return False


def _muat_sesi():
    global _sesi
    with _lock:
        if _sesi is None:
            import onnxruntime as ort
            _sesi = ort.InferenceSession(berkas_model(),
                                         providers=["CPUExecutionProvider"])
        return _sesi


def _muat_embed():
    global _embed
    with _lock:
        if _embed is None:
            d = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "mood_embeddings.npz"))
            mat = d["mat"].astype(np.float32)
            mat = mat / np.linalg.norm(mat, axis=1, keepdims=True)
            _embed = mat
        return _embed


def pra_proses(img, ukuran=224):
    """CLIP: resize sisi pendek -> crop tengah -> normalisasi."""
    im = img.convert("RGB")
    w, h = im.size
    skala = ukuran / min(w, h)
    im = im.resize((max(1, int(w * skala + 0.5)),
                    max(1, int(h * skala + 0.5))), Image.BICUBIC)
    w, h = im.size
    x0, y0 = (w - ukuran) // 2, (h - ukuran) // 2
    im = im.crop((x0, y0, x0 + ukuran, y0 + ukuran))
    a = np.asarray(im, dtype=np.float32) / 255.0
    a = (a - _MEAN) / _STD
    return a.transpose(2, 0, 1)[None].astype(np.float32)


def deteksi(img):
    """Return dict label -> probabilitas + 'tepercaya'; None bila tak siap."""
    if not siap():
        return None
    sesi = _muat_sesi()
    px = pra_proses(img)
    nama_in = sesi.get_inputs()[0].name
    out = sesi.run(None, {nama_in: px})
    emb = np.asarray(out[-1]).reshape(-1).astype(np.float32)
    n = float(np.linalg.norm(emb))
    if n <= 0:
        return None
    emb = emb / n
    sim = _muat_embed() @ emb
    e = np.exp((sim - float(sim.max())) / 0.04)
    p = e / e.sum()
    return {k: float(v) for k, v in zip(LABELS, p)} | {
        "tepercaya": float(p.max()), "mood_neural": LABELS[int(p.argmax())]}


def dengan_neural(an, hasil):
    """Gabungkan hasil neural ke hasil analisis statistik penata."""
    if not hasil:
        return an
    if hasil.get("tepercaya", 0) >= AMBANG:
        an["mood"] = hasil["mood_neural"]
        an["p_neural"] = {k: hasil[k] for k in LABELS}
    an["mood_neural_skor"] = {k: hasil[k] for k in LABELS}
    return an


def unduh(progress=None, cancel=None):
    """Unduh & pasang model mood dari rilis (± 89 MB). Return (ok, pesan)."""

    def log(m):
        if progress:
            progress(m)

    dst = berkas_model()
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    tmp = dst + ".unduh"
    try:
        log("Mengunduh model mood CLIP (± 89 MB)…")
        urllib.request.urlretrieve(URL_RILIS, tmp)
        if cancel is not None and cancel():
            os.remove(tmp)
            return False, "dibatalkan"
        log("Memasang…")
        with zipfile.ZipFile(tmp) as z:
            z.extractall(os.path.dirname(dst))
        os.remove(tmp)
        if not siap():
            return False, "berkas model tidak ditemukan di paket"
        log("Model mood siap ✓")
        return True, "ok"
    except Exception as e:                       # noqa: BLE001
        if os.path.exists(tmp):
            os.remove(tmp)
        return False, str(e)
