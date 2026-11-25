# -*- coding: utf-8 -*-
"""Mesin template poster: layout siap pakai di folder templates/.

Dua mode:
- overlay (PNG transparan)     : key art AI jadi latar penuh, template
  (scrim, bingkai, laurel, band warna) dipasang DI ATAS art.
- latar (JPEG/PNG tanpa alpha) : template jadi latar, key art AI dilebur
  di atasnya (blend 38%) lalu teks dipasang.

Setiap template boleh punya file JSON pendamping (<nama>.json) yang mengatur
zona teks — fraksi 0-1 terhadap ukuran poster:
  judul   : [x0, y0, x1, y1]  kotak area judul (di dalam margin aman)
  warna   : warna teks judul (mis. "#F2C14E")
  aksen   : warna garis aksen & tagline
  garis   : true/false  gambar garis aksen di bawah judul
  tanggal : true/false  strip "SEGERA DI BIOSKOP" di bawah judul
  billing : true/false  kredit pemain/sutradara di bawah judul
  scrim   : true/false  gelapkan area teks supaya tulisan terbaca
Tanpa JSON dipakai zona bawaan (judul bawah-tengah, teks putih, aksen emas).
"""

import json
import os

from PIL import Image, ImageDraw, ImageFilter, ImageOps

import poster_engine as eng

RESAMPLE = eng.RESAMPLE
_BAWAAN = {"judul": [0.06, 0.70, 0.94, 0.88], "warna": "#F7F6F4",
           "aksen": "#F2C14E", "garis": True, "tanggal": True,
           "billing": True, "scrim": False}


def folder_templates():
    """Folder berisi template (di samping aplikasi)."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


def _muat(path):
    info = Image.open(path)
    ada_alpha = info.mode in ("RGBA", "LA") or "transparency" in info.info
    t = {"nama": os.path.splitext(os.path.basename(path))[0],
         "path": path, "overlay": ada_alpha}
    sisi = os.path.splitext(path)[0] + ".json"
    if os.path.isfile(sisi):
        try:
            with open(sisi, encoding="utf-8") as fh:
                cfg = json.load(fh)
            if isinstance(cfg, dict):
                t.update(cfg)
        except Exception:
            pass
    return t


def list_templates():
    """Semua template di folder templates/, urut nama:
    [{'nama','path','overlay'}] — nama = nama file tanpa .png/.json."""
    d = folder_templates()
    out = []
    if os.path.isdir(d):
        for name in sorted(os.listdir(d)):
            if name.lower().endswith(".png") and not name.startswith("_"):
                try:
                    out.append(_muat(os.path.join(d, name)))
                except Exception:
                    pass
    return out


def cari_template(nama):
    """Nama template -> path lengkap; None kalau "tanpa" / tidak ketemu.
    Boleh juga path file langsung (template buatan sendiri)."""
    nama = (nama or "").strip()
    if not nama or nama.lower() in ("tanpa", "tanpa template", "none"):
        return None
    if os.path.isfile(nama):
        return nama
    for t in list_templates():
        if t["nama"].lower() == nama.lower():
            return t["path"]
    return None


def _warna(hexstr, fallback):
    """'#RRGGBB' -> tuple RGB; salah bentuk -> fallback."""
    try:
        h = str(hexstr).strip().lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        if len(h) != 6:
            raise ValueError
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return fallback


def compose(art, title, template_path, size=(1080, 1920), tagline="",
            pemain="", sutradara="", release="SEGERA DI BIOSKOP",
            studio="POSTER BIOSKOP PICTURES",
            gaya_judul="Otomatis (menyesuaikan judul)"):
    """Key art AI + template + tipografi sesuai zona template.
    Return PIL RGB image berukuran `size`."""
    W, H = size
    art = ImageOps.exif_transpose(art).convert("RGB")
    art = eng.cover_crop(art, W / H, focus=0.45).resize((W, H), RESAMPLE)
    art = eng.finish_art(art)

    cfg = dict(_BAWAAN)
    info = _muat(template_path)
    cfg.update({k: v for k, v in info.items() if k in _BAWAAN})
    tpl = ImageOps.exif_transpose(Image.open(template_path))
    if cfg.get("overlay", True):
        tpl = tpl.convert("RGBA").resize((W, H), RESAMPLE)
        img = Image.alpha_composite(art.convert("RGBA"), tpl).convert("RGB")
    else:                                    # mode latar: template dominan
        tpl = tpl.convert("RGB").resize((W, H), RESAMPLE)
        img = Image.blend(art, tpl, 0.38)

    j_x0, j_y0, j_x1, j_y1 = [float(v) for v in cfg.get("judul", _BAWAAN["judul"])]
    x0, y0 = max(int(W * 0.04), int(j_x0 * W)), max(int(H * 0.03), int(j_y0 * H))
    x1 = min(W - int(W * 0.04), int(j_x1 * W))
    y1 = min(H - int(H * 0.02), int(j_y1 * H))
    warna = _warna(cfg.get("warna"), (247, 246, 244))
    aksen = _warna(cfg.get("aksen"), (242, 193, 78))
    margin = max(int(W * 0.055), int(min(W, H) * 0.05), 24)

    if cfg.get("scrim", False):
        img = eng._scrim(img, y0 / H - 0.02, min(1.0, (y1 + int(H * 0.03)) / H), 190)

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx = (x0 + x1) / 2
    max_w = x1 - x0

    judul = (title or "").strip().upper() or "TANPA JUDUL"
    box_h = y1 - y0
    sus = eng.susun_judul(judul, max_w, box_h,
                          min(int(box_h * 0.62), int(H * 0.16)),
                          gaya=gaya_judul, max_lines=4)
    y_top = int(y1 - sus["tinggi"])          # rata bawah di dalam kotak
    img, t_end = eng.gambar_judul(img, sus, cx, y_top, (*warna, 255),
                                  (*aksen, 255))

    if cfg.get("garis", True):
        ry = int(min(t_end + H * 0.010, y1 + int(H * 0.02)))
        d.rectangle([cx - max_w * 0.16, ry, cx + max_w * 0.16,
                     ry + max(2, int(H * 0.003))], fill=(*aksen, 255))

    if tagline and tagline.strip():
        f_tag = eng.get_font("serif", max(12, int(H * 0.024)))
        t = "\u201c" + tagline.strip().upper() + "\u201d"
        tr = eng._tracked_fit(t, f_tag, max_w, max(1, int(H * 0.002)))
        ty = max(margin, int(y0 - H * 0.052))
        if eng.text_w(f_tag, t, tr) <= max_w:
            eng.draw_tracked(d, cx, ty, t, f_tag, (*aksen, 235), tracking=tr,
                             shadow=(1, 1, (0, 0, 0, 170)))

    if release and release.strip() and cfg.get("tanggal", True):
        f_rel = eng.get_font("credit", max(12, int(H * 0.022)))
        r = release.strip().upper()
        tr = eng._tracked_fit(r, f_rel, max_w, max(3, int(H * 0.007)))
        ry2 = min(int(y1 + H * 0.030), int(H * 0.950))
        if ry2 + H * 0.03 < H:
            eng.draw_tracked(d, cx, ry2, r, f_rel, (250, 250, 250, 245),
                             tracking=tr, shadow=(1, 1, (0, 0, 0, 170)))
            rw = eng.text_w(f_rel, r, tr)
            d.rectangle([cx - rw / 2, ry2 + H * 0.026, cx + rw / 2,
                         ry2 + H * 0.026 + max(2, int(H * 0.0025))],
                        fill=(*aksen, 255))
    else:
        ry2 = int(y1 + H * 0.012)

    if cfg.get("billing", True) and (pemain or sutradara):
        f_bill = eng.get_font("credit", max(10, int(H * 0.016)))
        segs = []
        if pemain:
            segs.append("DIBINTANGI " + ", ".join(
                p.strip().upper() for p in pemain.split(",") if p.strip()))
        if sutradara and sutradara.strip():
            segs.append("SUTRADARA " + sutradara.strip().upper())
        btxt = "   ".join(segs)
        by = min(max(ry2 + H * 0.024, t_end + H * 0.022), H - int(H * 0.075))
        for ln in eng._wrap_lines(btxt, f_bill, max_w, 2):
            d.text((cx - f_bill.getlength(ln) / 2, by), ln, font=f_bill,
                   fill=(230, 230, 230, 210))
            by += H * 0.020

    if cfg.get("studio", True) and studio and studio.strip():
        f_std = eng.get_font("credit", max(9, int(H * 0.012)))
        s = studio.strip().upper()
        tr = eng._tracked_fit(s, f_std, max_w, max(2, int(H * 0.004)))
        eng.draw_tracked(d, cx, int(H * 0.985) - f_std.size, s, f_std,
                         (215, 215, 215, 150), tracking=tr)

    img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
    return img
