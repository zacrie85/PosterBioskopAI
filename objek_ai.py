# -*- coding: utf-8 -*-
"""Objek semantik AI — PosterBioskopAI v2.6.0.

Menambahkan OBJEK kecil yang berhubungan dengan cerita poster (pisau untuk
thriller, mahkota untuk kerajaan, dll.) di pojok kanan-atas poster.

Cara kerja tanpa model inpaint:
1. Siluet objek digambar prosedural (PIL) di atas latar warna art.
2. Jika model AI siap: img2img SD-Turbo kualitas "paling setia" (~0,4 sGPU)
   melukis siluet itu menjadi objek sinematik bertekstur.
3. Latar diekstrak jadi transparan (jarak warna + mask siluet) -> objek RGBA.
4. Ditempel dengan bayangan lembut di pojok kanan-atas.
Tanpa model AI: siluet prosedural tetap dipakai (tetap rapi, cuma flat).
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

JENIS = ("Pisau", "Pedang", "Mahkota", "Cincin", "Kapal", "Kapal Selam",
         "Ular")

PROMPT = {
    "pisau": "ornate golden ceremonial dagger blade on plain dark "
             "background, cinematic studio lighting, centered, sharp metal",
    "pedang": "medieval golden longsword on plain dark background, "
              "cinematic studio lighting, centered, sharp metal",
    "mahkota": "royal golden crown with gems on plain dark background, "
               "cinematic studio lighting, centered",
    "cincin": "golden ring with glowing gem on plain dark background, "
              "cinematic studio lighting, centered",
    "kapal": "wooden sailing ship with masts on plain dark background, "
             "cinematic studio lighting, centered",
    "kapal selam": "military submarine with periscope on plain dark "
                   "background, cinematic studio lighting, centered",
    "ular": "giant python snake coiled on plain dark background, "
            "cinematic studio lighting, centered, detailed scales",
}

OTOMATIS = "Otomatis (dari mood)"
PINTAR = "Pintar (baca judul & prompt)"
TANPA = "Tanpa objek"

# mood -> jenis (terang-ceria tidak butuh objek)
MOOD_OBJEK = {"gelap-dramatis": "Pisau", "ramai-aksi": "Pedang",
              "dingin-misterius": "Mahkota", "hangat-romantis": "Cincin",
              "terang-ceria": None}

# kata kunci -> objek (urutan = prioritas; yang spesifik lebih dulu)
KATA_KUNCI = (
    ("kapal selam", "Kapal Selam"), ("submarin", "Kapal Selam"),
    ("kapal", "Kapal"), ("perahu", "Kapal"), ("layar", "Kapal"),
    ("ular", "Ular"), ("naga", "Ular"), ("boa", "Ular"), ("sanca", "Ular"),
    ("kobra", "Ular"), ("piton", "Ular"),
    ("mahkota", "Mahkota"), ("kerajaan", "Mahkota"), ("ratu", "Mahkota"),
    ("sultan", "Mahkota"), ("putri", "Mahkota"), ("raja", "Mahkota"),
    ("cincin", "Cincin"), ("pernikahan", "Cincin"), ("lamaran", "Cincin"),
    ("pedang", "Pedang"), ("kesatria", "Pedang"), ("samurai", "Pedang"),
    ("pisau", "Pisau"), ("parang", "Pisau"), ("keris", "Pisau"),
    ("pembunuh", "Pisau"), ("senjata", "Pisau"),
)


def dari_teks(konteks):
    """Baca judul + prompt: kata kunci cerita -> jenis objek (atau None)."""
    t = (konteks or "").lower()
    for kata, jenis in KATA_KUNCI:
        if kata in t:
            return jenis
    return None


def resolusi_objek(pilihan, mood, konteks=""):
    p = (pilihan or TANPA).strip().lower()
    if p.startswith("tanpa"):
        return None
    if p.startswith("pintar"):
        return dari_teks(konteks)
    if p.startswith("otomatis"):
        return MOOD_OBJEK.get(mood)
    for j in sorted(JENIS, key=len, reverse=True):   # terpanjang dulu:
        if j.lower() in p:                           # "kapal selam" menang
            return j                                 # atas "kapal"
    return None


def _kotak(d, x0, y0, x1, y1, r=0):
    if r:
        d.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=255)
    else:
        d.rectangle([x0, y0, x1, y1], fill=255)


def siluet(jenis, size=(384, 384)):
    """Mask siluet putih di latar hitam (L). Bentuk menghadap ke bawah."""
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    W, H = size
    cx = W // 2
    if jenis == "pisau":
        d.polygon([(cx, 30), (cx + 22, 66), (cx + 18, 210), (cx, 240),
                   (cx - 18, 210), (cx - 22, 66)], fill=255)
        _kotak(d, cx - 24, 240, cx + 24, 254)
        _kotak(d, cx - 15, 254, cx + 15, 344, r=10)
    elif jenis == "pedang":
        d.polygon([(cx, 24), (cx + 9, 40), (cx + 9, 236), (cx, 244),
                   (cx - 9, 236), (cx - 9, 40)], fill=255)
        _kotak(d, cx - 44, 240, cx + 44, 254)
        _kotak(d, cx - 11, 254, cx + 11, 330, r=8)
        d.ellipse([cx - 16, 330, cx + 16, 362], fill=255)
    elif jenis == "mahkota":
        d.polygon([(cx - 82, 250), (cx - 82, 160), (cx - 50, 208),
                   (cx - 22, 142), (cx, 200), (cx + 22, 142),
                   (cx + 50, 208), (cx + 82, 160), (cx + 82, 250)], fill=255)
        _kotak(d, cx - 82, 250, cx + 82, 300)
        for tx, ty in ((cx - 82, 152), (cx - 22, 134), (cx + 22, 134),
                       (cx + 82, 152)):
            d.ellipse([tx - 11, ty - 11, tx + 11, ty + 11], fill=255)
    elif jenis == "cincin":
        d.ellipse([cx - 76, 130, cx + 76, 282], outline=255, width=28)
        d.polygon([(cx, 96), (cx + 30, 126), (cx, 156), (cx - 30, 126)],
                  fill=255)
    elif jenis == "kapal":
        d.polygon([(46, 236), (338, 236), (306, 302), (78, 302)], fill=255)
        _kotak(d, 92, 206, 292, 236)
        d.line([(128, 206), (128, 108)], fill=255, width=9)
        d.line([(256, 206), (256, 128)], fill=255, width=9)
        d.polygon([(132, 112), (196, 168), (132, 168)], fill=255)
        d.polygon([(260, 132), (316, 182), (260, 182)], fill=255)
        d.polygon([(46, 236), (14, 214), (46, 196)], fill=255)
    elif jenis == "kapal selam":
        d.ellipse([42, 196, 342, 288], fill=255)
        _kotak(d, 156, 150, 226, 200, r=8)
        _kotak(d, 184, 118, 196, 152)
        d.polygon([(310, 196), (342, 160), (342, 250), (310, 250)], fill=255)
        d.ellipse([18, 218, 52, 266], fill=255)
        for wx in (110, 160, 210):
            d.ellipse([wx - 9, 232, wx + 9, 250], fill=0)
    elif jenis == "ular":
        pts = []
        for i in range(46):
            t = i / 45.0
            pts.append((36 + t * 312,
                        286 - 96 * np.sin(t * np.pi * 1.7 + 0.4)
                        - t * 8))
        r0, r1 = 9, 21
        for i, (x, y) in enumerate(pts):
            r = r0 + (r1 - r0) * (i / 45.0)
            d.ellipse([x - r, y - r, x + r, y + r], fill=255)
        hx, hy = pts[-1]
        d.ellipse([hx - 26, hy - 15, hx + 26, hy + 15], fill=255)
        d.polygon([(hx + 24, hy - 4), (hx + 44, hy), (hx + 24, hy + 4)],
                  fill=255)
    return m


def buat(ai, jenis, palet, aksen, seed=7, progress=None, size=(384, 384)):
    """Objek RGBA siap tempel. ai=None / model tak siap -> siluet prosedural."""
    jenis = (jenis or "").strip()
    if jenis.lower() not in [j.lower() for j in JENIS]:
        return None
    mask = siluet(jenis.lower(), size)
    W, H = size

    # latar gelap dari palet art + objek terang dari aksen (kontras utk AI)
    dom = palet[0] if palet else (26, 18, 34)
    latar = tuple(int(c * 0.45) for c in dom)
    terang = tuple(int(a * 0.55 + 255 * 0.45) for a in aksen)
    init = Image.new("RGB", size, latar)
    init.paste(Image.new("RGB", size, terang), (0, 0), mask)
    init = init.filter(ImageFilter.GaussianBlur(1.2))

    hasil = init
    if ai is not None:
        try:
            if ai.ready():
                hasil = ai.generate(init, PROMPT.get(jenis.lower(), PROMPT["pisau"]),
                                    size,
                                    quality_key="Foto asli + sentuhan AI "
                                                "(paling setia)",
                                    seed=seed, progress=progress)
        except Exception:                                      # noqa: BLE001
            hasil = init

    # ekstraksi alpha: jarak warna dari latar (median 4 pojok) x mask siluet
    a = np.asarray(hasil.convert("RGB"), dtype=np.float32)
    pojok = np.stack([a[:16, :16], a[:16, -16:], a[-16:, :16], a[-16:, -16:]
                      ]).reshape(-1, 3)
    bg = np.median(pojok, axis=0)
    dist = np.sqrt(((a - bg) ** 2).sum(-1))
    alpha = np.clip((dist - 30.0) / 50.0, 0, 1) * 255.0
    m = np.asarray(mask, dtype=np.float32)
    m_dil = np.asarray(mask.filter(ImageFilter.MaxFilter(9))
                       .filter(ImageFilter.GaussianBlur(5)), dtype=np.float32)
    alpha = np.minimum(alpha, np.maximum(m_dil, (m > 40) * 255.0))
    alpha = np.asarray(Image.fromarray(alpha.astype(np.uint8), "L")
                       .filter(ImageFilter.GaussianBlur(1.5)))
    if float(alpha.max()) < 10:
        return None
    obj = Image.fromarray(np.dstack([a.astype(np.uint8),
                                     alpha.astype(np.uint8)]), "RGBA")
    bbox = obj.getbbox()
    if bbox is None:
        return None
    return obj.crop(bbox)


def tempel(poster, obj_rgba, skala=0.16, sudut="kanan-atas", seed=7):
    """Tempel objek di pojok dengan bayangan lembut. Return poster RGB."""
    W, H = poster.size
    ow, oh = obj_rgba.size
    target = max(24, int(min(W, H) * skala * 1.6))
    skala_f = target / max(ow, oh)
    obj = obj_rgba.resize((max(1, int(ow * skala_f)),
                           max(1, int(oh * skala_f))), Image.LANCZOS)
    obj = obj.rotate(-8, expand=True, resample=Image.BICUBIC)
    pad = int(min(W, H) * 0.02)
    if sudut == "kanan-atas":
        x = W - pad - obj.width
        y = pad + int(H * 0.02)
    elif sudut == "kanan-bawah":
        x = W - pad - obj.width
        y = H - pad - obj.height - int(H * 0.10)
    else:
        x = pad + int(W * 0.02)
        y = pad + int(H * 0.02)

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bay.paste((0, 0, 0, 130), (x + 5, y + 7), obj.split()[3])
    bay = bay.filter(ImageFilter.GaussianBlur(7))
    layer.alpha_composite(bay)
    layer.alpha_composite(obj, (x, y))
    out = Image.alpha_composite(poster.convert("RGBA"), layer)
    return out.convert("RGB")
