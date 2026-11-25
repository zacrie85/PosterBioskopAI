# -*- coding: utf-8 -*-
"""Penghapus subtitle hardsub — PosterBioskopAI v2.6.0.

Frame video sering membawa subtitle yang MENEMPEL di gambar (bukan file
terpisah). AI img2img dengan kekuatan "paling setia" hampir selalu
menggambar ulang subtitle itu — jadi ia harus DIHAPUS DULU sebelum frame
dikirim ke AI. Setelah dihapus (jadi area buram lembut), AI justru
"menyembuhkan" area itu menjadi latar sinematik yang wajar.

Cara kerja (murni numpy+PIL, instan, tanpa unduhan):
1. Pindai pita bawah frame (subtitle selalu di bawah).
2. Temukan piksel "goresan teks": piksel yang jauh lebih terang (atau lebih
   gelap) daripada sekitarnya (kontras lokal) — ini teks, bukan film.
3. Subtitle punya pola 1-3 BARIS teks: baris dengan kepadatan goresan
   tinggi & berkelompok. Tanpa pola itu -> tidak ada subtitle -> frame
   DIBIARKAN UTUH (anti-rusak: key art bersih tidak disentuh).
4. Goresan diperbesar (dilasi) agar garis tepi/glow ikut, lalu ditimpa
   hasil blur bertingkat dari sekelilingnya (inpaint sederhana).
"""
import numpy as np
from PIL import Image, ImageFilter

_PITA = 0.32          # pindai 32% bagian bawah frame (subtitle selalu di sana)
_MIN_BARIS = 0.012    # subtitle minimal ~1,2% tinggi frame (fraksi baris teks)
_MAX_BARIS = 0.16     # lebih dari ini = bukan subtitle (mis. langit terang)
_KONTRAS = 16.0       # selisih luminance minimum goresan vs sekeliling


def _luminance(a):
    return a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114


def ada_subtitel(img):
    """Heuristik cepat: True bila pita bawah memuat pola baris subtitle."""
    W, H = img.size
    y0 = int(H * (1 - _PITA))
    a = np.asarray(img.convert("RGB").crop((0, y0, W, H)), dtype=np.float32)
    L = _luminance(a)
    return _polo_baris(L, H, W)[0]


def _polo_baris(L, H_full, W_full):
    """Return (ada, mask_goresan uint8 untuk pita). mask: 255 = goresan teks.
    Diskriminator subtitle (bukan fitur film): baris teks berkelompok di
    bawah, MELEBAR >= 30% lebar, goresan terangnya SERAGAM kecerahannya,
    dan fraksi goresan kecil (bukan blok luas seperti langit/lampu)."""
    hb, wb = L.shape
    lembut = np.asarray(Image.fromarray(L.astype(np.uint8), "L")
                        .filter(ImageFilter.GaussianBlur(4)), dtype=np.float32)
    terang = ((L - lembut) > _KONTRAS) & (L > 140)
    goresan = terang              # hardsub = teks TERANG (putih/kuning);
    # goresan gelap diabaikan (terlalu banyak kemiripan dengan tepi film)
    if not (0.0008 < goresan.mean() < 0.14):
        return False, None
    baris = goresan.mean(axis=1) > 0.02
    jumlah = int(baris.sum())
    # dibandingkan ke TINGGI FRAME PENUH (subtitle biasanya 2-10% tinggi)
    if jumlah < H_full * _MIN_BARIS or jumlah > H_full * _MAX_BARIS:
        return False, None
    idx = np.where(baris)[0]
    if not len(idx):
        return False, None
    rentang = idx[-1] - idx[0] + 1
    if rentang > hb * 0.75:
        return False, None                       # tersebar merata = film
    # garis teks harus MELEBAR: kolom berisi goresan >= 30% lebar frame
    kolom_ada = (goresan[idx[0]:idx[-1] + 1, :].sum(axis=0) > 0)
    if kolom_ada.mean() < 0.30:
        return False, None                       # titik/objek kecil saja
    # kecerahan goresan terang harus SERAGAM (teks subtitle satu warna)
    px = L[terang]
    if len(px) >= 60 and float(np.std(px)) > 50:
        return False, None
    mask = (goresan & baris[:, None]).astype(np.uint8) * 255
    return True, mask


def hapus(img, progress=None):
    """Hapus subtitle hardsub dari frame. Return PIL RGB (ukuran sama).
    Tanpa pola subtitle yang yakin -> gambar dikembalikan apa adanya."""

    def log(m):
        if progress:
            progress("subtitel", m)

    W, H = img.size
    y0 = int(H * (1 - _PITA))
    band = img.convert("RGB").crop((0, y0, W, H))
    a = np.asarray(band, dtype=np.float32)
    ada, mask = _polo_baris(_luminance(a), H, W)
    if not ada:
        return img.convert("RGB") if img.mode != "RGB" else img

    log("Subtitle terdeteksi — menghapus sebelum AI menggambar…")
    m = Image.fromarray(mask, "L").filter(
        ImageFilter.MaxFilter(11)).filter(                # garis tepi + glow
        ImageFilter.GaussianBlur(3))
    m = np.asarray(m)
    m3 = (m > 40)[..., None]
    out = a.copy()
    for radius in (31, 19, 9):                            # blur bertingkat:
        blur = np.asarray(Image.fromarray(                # isi dari sekeliling
            out.astype(np.uint8), "RGB").filter(
            ImageFilter.GaussianBlur(radius)), dtype=np.float32)
        out = np.where(m3, blur, out)
    hasil = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")
    gab = img.convert("RGB").copy()
    gab.paste(hasil, (0, y0))
    return gab
