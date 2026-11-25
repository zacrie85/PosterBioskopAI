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


def _wrap_lines(text, font, max_w, max_lines=None):
    """Pecah teks jadi baris-baris; setiap baris dijamin <= max_w.
    TIDAK ADA teks yang dibuang: kata lebih panjang dari max_w (kasus
    ekstrem, nama tanpa spasi) dipecah menjadi beberapa baris, dan jumlah
    baris tidak pernah dipangkas dengan tanda '…'. fit_title yang menjaga
    tinggi total dengan mengecilkan font."""
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
    # kata tunggal raksasa -> pecah per potongan karakter ke baris berikut
    fixed = []
    for ln in lines:
        while font.getlength(ln) > max_w and len(ln) > 1:
            potong = len(ln)
            while potong > 1 and font.getlength(ln[:potong]) > max_w:
                potong -= 1
            fixed.append(ln[:potong])
            ln = ln[potong:]
        if ln:
            fixed.append(ln)
    return fixed


def fit_title(text, role, max_w, max_h, start_size, min_size=18, max_lines=3):
    """Cari ukuran font terbesar agar JUDUL muat dalam max_w x max_h.
    Ini menjamin tulisan tidak melewati batas KIRI/KANAN/BLOK judul, dan
    SEMUA teks SELALU tampil: judul tidak pernah dipotong '…'. Kalau dengan
    <= max_lines baris tidak muat, pencarian menerus ke font lebih kecil
    dengan baris lebih banyak (fase 2), lalu pengaman font paling kecil."""
    # fase 1: font besar, baris sedikit (estetika poster biasa)
    size = int(start_size)
    while size >= min_size:
        font = get_font(role, size)
        lh = size * 1.12
        for ml in range(1, max_lines + 1):
            lines = _wrap_lines(text, font, max_w, ml)
            if len(lines) * lh <= max_h and all(l for l in lines):
                return font, lines, size, lh
        size = int(size * 0.93)
    # fase 2: judul sangat panjang — font kecil, baris lebih banyak
    for ml in (max_lines + 2, max_lines + 5, max_lines + 10):
        size = min_size
        while size >= 9:
            font = get_font(role, size)
            lh = size * 1.12
            lines = _wrap_lines(text, font, max_w, ml)
            if len(lines) * lh <= max_h and all(l for l in lines):
                return font, lines, size, lh
            size = int(size * 0.9)
    # pengaman terakhir: font terkecil, baris tanpa batas (teks tetap utuh)
    for sz in (9, 8, 7):
        font = get_font(role, sz)
        lines = _wrap_lines(text, font, max_w)
        if len(lines) * sz * 1.12 <= max_h:
            return font, lines, sz, sz * 1.12
    return font, lines, 7, 7 * 1.12


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


import bingkai as bingkai_mod
import objek_ai as objek_ai_mod
import penata as penata_mod


# ---------------------------------------------------------------------------
# Variasi gaya judul: ukuran per kata menyesuaikan panjang judul, seperti
# poster bioskop sungguhan (kata penting besar, kata sambung kecil, atau
# kata akhir miring berwarna aksen). SEMUA teks tetap tampil utuh.
# ---------------------------------------------------------------------------
_KATA_SAMBUNG = {"DI", "KE", "DARI", "YANG", "DAN", "ATAU", "SI", "PADA",
                 "DENGAN", "UNTUK", "TANPA", "ADALAH", "DALAM", "OLEH", "BAGI",
                 "SAAT", "SANG", "THE", "OF", "IN", "A", "AN", "DG", "DGN",
                 "INI", "ITU", "JUGA", "KETIKA", "SERTA", "TAPI", "PUN"}

GAYA_JUDUL = ("Otomatis (menyesuaikan judul)", "Klasik (seragam besar)",
              "Menonjol (kata penting besar)", "Miring (kata akhir aksen)")


def _pilih_gaya(gaya, n_kata):
    g = (gaya or "").strip().lower()
    if g.startswith("klasik"):
        return "klasik"
    if g.startswith("menonjol"):
        return "menonjol"
    if g.startswith("miring"):
        return "miring"
    if n_kata >= 8:                    # judul panjang -> kontras besar/kecil
        return "menonjol"
    if n_kata >= 3:                    # sedang -> kata akhir miring aksen
        return "miring"
    return "klasik"                    # pendek -> satu blok besar


def _baris(segs, gap, ukuran, ekstra=0.0):
    return {"segs": segs, "gap": gap, "ukuran": ukuran, "ekstra": ekstra}


def _susun_seragam(text, max_w, max_h, start, max_lines):
    """Klasik: satu ukuran untuk semua baris (perilaku lama)."""
    font, lines, size, lh = fit_title(text, "display", max_w, max_h, start,
                                      max_lines=max_lines)
    baris = [_baris([(ln, font, False, False)], 0.0, size) for ln in lines]
    return {"baris": baris, "tinggi": lh * len(lines), "ukuran_max": size}


def _susun_menonjol(text, max_w, max_h, start, max_lines):
    """Kata penting besar, kata sambung (di/yang/dan...) lebih kecil."""
    kata = text.split()
    s = 1.0
    while True:
        besar = max(9, int(start * s))
        kecil = max(8, int(besar * 0.56))
        fb, fk = get_font("display", besar), get_font("display", kecil)
        gap = besar * 0.20
        baris, cur, cur_w = [], [], 0.0
        for w in kata:
            penting = w.strip(",.!?;:") not in _KATA_SAMBUNG
            font = fb if penting else fk
            lw = font.getlength(w)
            if cur and cur_w + gap + lw > max_w:
                baris.append(cur)
                cur, cur_w = [], 0.0
            if cur:
                cur_w += gap
            cur.append((w, font, False, False))
            cur_w += lw
            if w.endswith(","):
                baris.append(cur)
                cur, cur_w = [], 0.0
        if cur:
            baris.append(cur)
        tinggi = sum(max(f.size for _, f, _, _ in b) * 1.12 for b in baris)
        if (tinggi <= max_h and len(baris) <= max_lines + 2) or besar <= 9:
            baris = [_baris(b, gap, max(f.size for _, f, _, _ in b))
                     for b in baris]
            return {"baris": baris, "tinggi": tinggi, "ukuran_max": besar}
        s *= 0.90


def _susun_miring(text, max_w, max_h, start, max_lines):
    """Seragam, tapi kata terakhir (bukan kata sambung) miring + aksen."""
    font, lines, size, lh = fit_title(text, "display", max_w, max_h, start,
                                      max_lines=max_lines)
    kata_akhir = lines[-1].split()[-1] if lines[-1].split() else ""
    if (len(lines[-1].split()) >= 2
            and kata_akhir.strip(",.!?;:") not in _KATA_SAMBUNG):
        segs = []
        for wd in lines[-1].split():
            miring = wd == kata_akhir
            segs.append((wd, font, miring, miring))
        baris = [_baris([(ln, font, False, False)], 0.0, size)
                 for ln in lines[:-1]]
        baris.append(_baris(segs, font.getlength(" "), size, ekstra=size * 0.12))
        tinggi = lh * len(lines) + size * 0.12
    else:
        baris = [_baris([(ln, font, False, False)], 0.0, size) for ln in lines]
        tinggi = lh * len(lines)
    return {"baris": baris, "tinggi": tinggi, "ukuran_max": size}


def susun_judul(text, max_w, max_h, start_size,
                gaya="Otomatis (menyesuaikan judul)", max_lines=4):
    """Susun judul multi-ukuran sesuai gaya. Return dict:
      baris      : list baris; tiap baris = dict segs [(teks, font, aksen,
                   miring)], gap antar kata, ukuran (font terbesar di baris)
                   dan ekstra tinggi utk kata miring
      tinggi     : tinggi total blok judul (px)
      ukuran_max : font terbesar di seluruh judul
    Semua kata SELALU ikut — tidak ada teks yang dipotong."""
    mode = _pilih_gaya(gaya, len(text.split()))
    if mode == "menonjol":
        return _susun_menonjol(text, max_w, max_h, start_size, max_lines)
    if mode == "miring":
        return _susun_miring(text, max_w, max_h, start_size, max_lines)
    return _susun_seragam(text, max_w, max_h, start_size, max_lines)


def _teks_miring(teks, font, warna):
    """Render satu kata miring -4 derajat ke gambar RGBA transparan."""
    pad = max(8, int(font.size * 0.35))
    bbox = font.getbbox(teks)
    w = int(font.getlength(teks)) + pad * 2
    h = int(font.size * 1.5) + pad * 2
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    dd.text((pad - bbox[0], pad - bbox[1]), teks, font=font, fill=warna)
    return im.rotate(-4, expand=True, resample=Image.BICUBIC)


def gambar_judul(img, susunan, cx, y_top, utama=(247, 246, 244, 255),
                 aksen=(242, 193, 78, 255)):
    """Gambar hasil susun_judul ke img: bayangan lembut + teks multi-ukuran.
    Return (img_rgb_baru, y_bawah_blok_judul)."""
    W, H = img.size
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds, d = ImageDraw.Draw(sh), ImageDraw.Draw(layer)
    y = int(y_top)
    uk_max = susunan["ukuran_max"]
    soff_x, soff_y = max(2, int(uk_max * 0.05)), max(3, int(uk_max * 0.06))
    for ln in susunan["baris"]:
        segs, gap = ln["segs"], ln["gap"]
        lebar = 0.0
        for i, (teks, font, _, miring) in enumerate(segs):
            lw = font.getlength(teks)
            if miring:
                lw = lw * 1.06 + font.size * 0.14
            if i:
                lebar += gap
            lebar += lw
        x = cx - lebar / 2.0
        for teks, font, pk, miring in segs:
            warna = aksen if pk else utama
            yb = y + (ln["ukuran"] - font.size)   # sejajarkan garis dasar
            if miring:
                im_t = _teks_miring(teks, font, warna)
                im_s = _teks_miring(teks, font, (0, 0, 0, 210))
                sh.paste(im_s, (int(x + soff_x), int(yb + soff_y)), im_s)
                layer.paste(im_t, (int(x), int(yb - int(ln["ekstra"] / 2))), im_t)
            else:
                ds.text((x + soff_x, yb + soff_y), teks, font=font,
                        fill=(0, 0, 0, 220))
                d.text((x, yb), teks, font=font, fill=warna)
            lw = font.getlength(teks)
            if miring:
                lw = lw * 1.06 + font.size * 0.14
            x += lw + gap
        y += ln["ukuran"] * 1.12 + ln["ekstra"]
    sh = sh.filter(ImageFilter.GaussianBlur(max(2, int(uk_max * 0.03))))
    img = Image.alpha_composite(img.convert("RGBA"), sh)
    img = Image.alpha_composite(img, layer)
    return img.convert("RGB"), y


# ---------------------------------------------------------------------------
# Komposisi akhir: key art AI + teks
# ---------------------------------------------------------------------------
def compose_poster(art, title, size=(1080, 1920), tagline="", pemain="",
                   sutradara="", studio="POSTER BIOSKOP PICTURES",
                   release="SEGERA DI BIOSKOP", seed=7, template=None,
                   gaya_judul="Otomatis (menyesuaikan judul)",
                   penata="Otomatis dari gambar",
                   bingkai="Otomatis (dari gambar)",
                   objek="Tanpa objek", ai=None, mood_neural_aktif=False):
    """Susun poster final: key art AI + tipografi dengan margin aman.
    Kalau `template` diisi (path file di folder templates/ atau path
    langsung), susunan visual mengikuti template itu (template_engine).
    Return PIL RGB image berukuran `size`."""
    if template:
        import template_engine                       # hindari impor melingkar
        return template_engine.compose(art, title, template, size=size,
                                       tagline=tagline, pemain=pemain,
                                       sutradara=sutradara, release=release,
                                       studio=studio, gaya_judul=gaya_judul,
                                       penata=penata, bingkai=bingkai,
                                       seed=seed)
    W, H = size
    art = ImageOps.exif_transpose(art).convert("RGB")
    art = cover_crop(art, W / H, focus=0.45).resize((W, H), RESAMPLE)
    img = finish_art(art)

    # --- PENATA AI: baca palet & mood gambar, putuskan warna/gaya/kontras ---
    an = penata_mod.analisa_gambar(img)
    if mood_neural_aktif:
        try:
            import mood_neural
            an = mood_neural.dengan_neural(an, mood_neural.deteksi(img))
        except Exception:                                      # noqa: BLE001
            pass
    keputusan = penata_mod.pilih_tipografi(
        an, gaya_pref=gaya_judul,
        klasik=(penata or "").lower().startswith("klasik"))
    nama_bingkai, _mood = penata_mod.pilih_bingkai(an, bingkai)
    warna_judul = keputusan["utama"]
    warna_aksen = keputusan["aksen"]
    gold = (*warna_aksen, 255)

    landscape = W > H
    img = _scrim(img, 0.42 if not landscape else 0.52, 1.0,
                 keputusan["scrim"] or 215)
    if pemain:
        img = _scrim(img, 0.0, 0.13, 150, reverse=True)

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    # ====== MARGIN AMAN: semua teks dipaksa muat di dalam [margin, W-margin] ======
    inset_bingkai = 0
    if nama_bingkai:
        img, inset_bingkai = bingkai_mod.gambar(img, nama_bingkai, an["palet"],
                                                warna_aksen, seed=seed)

    # --- objek semantik AI (v2.5.0): pisau/mahkota/dll di pojok kanan-atas ---
    jenis_obj = objek_ai_mod.resolusi_objek(objek, an["mood"])
    if jenis_obj:
        try:
            _obj = objek_ai_mod.buat(ai, jenis_obj, an["palet"], warna_aksen,
                                     seed=seed)
        except Exception:                                      # noqa: BLE001
            _obj = None
        if _obj is not None:
            img = objek_ai_mod.tempel(img, _obj, skala=0.16)
    margin = max(int(W * 0.055), int(min(W, H) * 0.05), 24) + inset_bingkai
    max_w = W - 2 * margin
    cx = W / 2

    # gold di-set dari warna aksen penata di atas

    # --- nama pemain (opsional, zona atas) ---
    if pemain:
        f_cast = get_font("credit", max(12, int(H * 0.020)))
        names = "   ·   ".join(p.strip().upper() for p in pemain.split(",") if p.strip())
        tr = _tracked_fit(names, f_cast, max_w, max(2, int(H * 0.004)))
        if text_w(f_cast, names, tr) <= max_w:
            draw_tracked(d, cx, int(H * 0.045), names, f_cast, (245, 245, 245, 230),
                         tracking=tr, shadow=(1, 1, (0, 0, 0, 170)))

    # --- judul: variasi gaya + auto-fit, SEMUA teks selalu tampil ---
    title_text = (title or "").strip().upper() or "TANPA JUDUL"
    start = int(H * (0.155 if landscape else 0.135))
    max_h_title = H * (0.30 if landscape else 0.27)
    gaya_eff = gaya_judul
    if gaya_judul.startswith("Otomatis") and keputusan.get("gaya"):
        gaya_eff = keputusan["gaya"]           # mood gambar menentukan
    sus = susun_judul(title_text, max_w, max_h_title, start,
                      gaya=gaya_eff, max_lines=4)
    bottom_anchor = H * (0.90 if not sutradara and not release else 0.885)
    y_top = int(bottom_anchor - sus["tinggi"])
    img, t_end = gambar_judul(img, sus, cx, y_top,
                              utama=(*warna_judul, 255), aksen=gold)

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
    y_strip = min(H * 0.955, H - int(H * 0.033) - inset_bingkai)
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
        s_txt = studio.strip().upper()
        tr = _tracked_fit(s_txt, f_std, max_w, max(2, int(H * 0.004)))
        if release and release.strip():
            # tepat di bawah garis bawah strip — tidak lagi menimpanya
            y_std = y_strip + int(H * 0.026) + max(4, int(H * 0.006))
        else:
            y_std = int(H * 0.985) - f_std.size
        if y_std + f_std.size > H - max(2, inset_bingkai) - 2:
            y_std = None            # tak muat di atas bingkai -> lewati
        if y_std is not None:
            draw_tracked(d, cx, y_std, s_txt, f_std,
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
