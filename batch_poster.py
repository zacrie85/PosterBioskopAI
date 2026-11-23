# -*- coding: utf-8 -*-
"""
PosterBioskopAI — MODE BATCH: satu folder video/foto → banyak poster sekaligus.

Tiap file dianalisis sendiri-sendiri: frame terbaik diekstraksi, judul diambil
dari nama file, dan gaya poster di-auto-match dari 999 referensi (atau dipakai
satu gaya yang sama untuk semua). Hasil disimpan sebagai PNG resolusi tinggi.

Dipakai dua cara:
  1. Dari GUI     : tombol "MODE BATCH" di aplikasi (poster_app.py).
  2. Dari terminal: python batch_poster.py <folder> [--out DIR]
                    [--rasio "Wallpaper 16:9"] [--gaya REF-289]
"""

import argparse
import os
import re
import sys
import time

from PIL import Image

import poster_engine as eng
import frame_picker as fp
import style_library as lib

IMG_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


def collect_media(folder):
    """Daftar file video + foto di folder, urut abjad. Raise kalau folder tak ada."""
    if not os.path.isdir(folder):
        raise NotADirectoryError(f"Bukan folder: {folder}")
    files = []
    for name in sorted(os.listdir(folder)):
        p = os.path.join(folder, name)
        if os.path.isfile(p) and name.lower().endswith(fp.VIDEO_EXTS + IMG_EXTS):
            files.append(p)
    return files


def _unique_name(judul, used):
    """'Kebun Raya' -> 'Kebun Raya.png'; kalau duplikat jadi 'Kebun Raya 2.png'."""
    base = re.sub(r"[^\w\- ]", "", judul).strip() or "poster"
    name, n = base, 2
    while name.lower() in used:
        name = f"{base} {n}"
        n += 1
    used.add(name.lower())
    return name


def process_one(path, out_dir, ratio_key, fixed_style=None, used=None):
    """Render satu file menjadi poster. Return dict ringkasan (ok/gagal + detail)."""
    t0 = time.time()
    is_vid = fp.is_video(path)
    info_detik = None
    if is_vid:
        img, stats, info = fp.extract_best_frame(path)
        info_detik = info.get("waktu_detik")
    else:
        img = Image.open(path)
        stats = lib.analyze_image(img)
    judul = fp.title_from_filename(path)

    if fixed_style is not None:
        style = fixed_style
    else:
        style = lib.match_styles(stats, top_n=1)[0][1]

    poster = eng.render_poster(img, style, judul,
                               size=eng.FULL_SIZES.get(ratio_key, (1000, 1500)))
    out_path = os.path.join(out_dir, _unique_name(judul, used) + ".png")
    poster.save(out_path, quality=92)
    return {
        "ok": True,
        "sumber": path,
        "judul": judul,
        "gaya": f"{style['id']} · {style['name']}",
        "keluar": out_path,
        "detik": info_detik,
        "ukuran": poster.size,
        "durasi_proses": round(time.time() - t0, 1),
        "video": is_vid,
    }


def run_batch(folder, out_dir=None, ratio_key="Poster 2:3", style_id=None,
              log=None, progress=None, should_continue=None):
    """Proses SEMUA video/foto di folder.

    log(msg)               -> pesan kemajuan (mis. untuk Text di GUI / print)
    progress(selesai, total, nama_file)
    should_continue()      -> False untuk membatalkan
    Return: dict ringkasan {total, ok, gagal, dibatalkan, out_dir, hasil, errors}
    """
    log = log or (lambda s: None)
    progress = progress or (lambda *a: None)
    cont = should_continue or (lambda: True)

    files = collect_media(folder)
    if not files:
        raise ValueError("Tidak ada video/foto di folder itu. "
                         "Format yang dikenal: " + " ".join(fp.VIDEO_EXTS + IMG_EXTS))

    if out_dir is None:                       # folder hasil = folder sebelah, mis. /video → /video_poster
        folder = os.path.abspath(folder)
        out_dir = folder.rstrip(os.sep) + "_poster"
    os.makedirs(out_dir, exist_ok=True)

    fixed = None
    if style_id:                              # "REF-289" -> satu gaya untuk semua
        sid = style_id.strip().upper()
        fixed = next((s for s in lib.library() if s["id"].upper() == sid), None)
        if fixed is None:
            raise ValueError(f"Gaya {style_id} tidak ada di perpustakaan "
                             f"(999 referensi, contoh: REF-302).")

    lib.library()                             # pastikan perpustakaan sudah dibangun
    used, hasil, errors = set(), [], []
    n = len(files)
    log(f"Batch dimulai: {n} file → folder hasil: {out_dir}")
    log(f"Rasio: {ratio_key} · Gaya: {'pilih per video (auto-match)' if fixed is None else fixed['id']}")
    done = 0
    for i, path in enumerate(files):
        name = os.path.basename(path)
        if not cont():
            log("Dibatalkan oleh pengguna.")
            return {"total": n, "ok": len(hasil), "gagal": len(errors),
                    "dibatalkan": True, "out_dir": out_dir, "hasil": hasil,
                    "errors": errors}
        progress(done, n, name)
        log(f"[{i + 1}/{n}] {name} …")
        try:
            r = process_one(path, out_dir, ratio_key, fixed_style=fixed, used=used)
            hasil.append(r)
            done += 1
            sumber = f"detik {r['detik']} dari video" if r["video"] else "foto"
            log(f"    ✔ {r['judul']} — gaya {r['gaya']} ({sumber}, {r['durasi_proses']} dtk)")
        except Exception as exc:              # noqa: BLE001 — satu file gagal, lanjut yang lain
            errors.append({"sumber": path, "error": str(exc)})
            log(f"    ✘ GAGAL: {exc}")
    progress(done, n, "")
    log(f"SELESAI: {len(hasil)} poster berhasil, {len(errors)} gagal → {out_dir}")
    return {"total": n, "ok": len(hasil), "gagal": len(errors), "dibatalkan": False,
            "out_dir": out_dir, "hasil": hasil, "errors": errors}


def open_folder(path):
    """Buka folder di file manager (Windows/macOS/Linux), kalau bisa."""
    try:
        if os.name == "nt" and hasattr(os, "startfile"):
            os.startfile(path)                # noqa: S606
        elif sys.platform == "darwin":
            os.system(f'open "{path}" &')     # noqa: S605
        else:
            os.system(f'xdg-open "{path}" &')  # noqa: S605
    except Exception:                         # noqa: BLE001
        pass


def main():
    ap = argparse.ArgumentParser(
        description="PosterBioskopAI MODE BATCH: satu folder video/foto → banyak poster")
    ap.add_argument("folder", help="folder berisi video/foto")
    ap.add_argument("--out", default=None, help="folder hasil (bawaan: <folder>_poster)")
    ap.add_argument("--rasio", default="Poster 2:3", choices=list(eng.RATIOS.keys()))
    ap.add_argument("--gaya", default=None,
                    help="pakai SATU gaya untuk semua, mis. REF-289 (bawaan: auto-match per video)")
    a = ap.parse_args()

    res = run_batch(a.folder, a.out, a.rasio, a.gaya, log=print)
    for e in res["errors"]:
        print(f"  gagal: {e['sumber']} — {e['error']}")
    print(f"\nPoster tersimpan di: {res['out_dir']}")
    sys.exit(0 if (res["ok"] > 0 and res["gagal"] == 0) else 1)


if __name__ == "__main__":
    main()
