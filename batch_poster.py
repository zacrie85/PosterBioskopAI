# -*- coding: utf-8 -*-
"""
PosterBioskopAI — MODE BATCH AI: satu folder video/foto → banyak poster AI.

Tiap file dianalisis sendiri-sendiri: frame terbaik diekstraksi, judul diambil
dari nama file, lalu MESIN AI (Stable Diffusion Turbo lokal) mengubah frame
menjadi key art poster sesuai SATU PROMPT yang sama untuk semua file
(persis tombol "Terapkan ke Semua Video" di GUI). Hasil disimpan sebagai PNG
resolusi tinggi.

Dipakai dua cara:
  1. Dari GUI     : tombol MODE BATCH di aplikasi (poster_app.py).
  2. Dari terminal: python batch_poster.py <folder> [--out DIR]
                    [--rasio "9:16"] [--prompt "teks prompt"]
                    [--kualitas "Foto asli + sentuhan AI (paling setia)"]
"""

import argparse
import os
import re
import sys
import time

from PIL import Image

import poster_ai as ai
import poster_engine as eng
import bingkai as bingkai_mod
import frame_picker as fp
import template_engine as te

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


def process_one(path, out_dir, ratio_key, prompt, kualitas, used, log=None,
                template=None, rilis="SEGERA DI BIOSKOP",
                gaya_judul="Otomatis (menyesuaikan judul)",
                penata="Otomatis dari gambar", bingkai="Otomatis (dari gambar)",
                tekstur_ai=False):
    """Proses satu file: frame -> AI -> poster tipografi. Return dict ringkasan."""
    t0 = time.time()
    is_vid = fp.is_video(path)
    info_detik = None
    if is_vid:
        img, _, info = fp.extract_best_frame(path)
        info_detik = info.get("waktu_detik")
    else:
        img = Image.open(path)
    judul = fp.title_from_filename(path)

    video_ratio = img.size[0] / max(1, img.size[1])
    canvas = ai.ai_canvas(ratio_key, video_ratio)
    full = ai.poster_full_size(ratio_key, video_ratio)

    def prog(fase, info):
        if log:
            log("      " + info)

    engine = getattr(process_one, "_engine", None)
    if engine is None:
        engine = ai.PosterAI(keep_loaded=True)
        process_one._engine = engine                  # sesi model dipakai ulang
    art = engine.generate(img, prompt, canvas, quality_key=kualitas, progress=prog)
    poster = eng.compose_poster(art, judul, size=full, template=template,
                                release=rilis, gaya_judul=gaya_judul,
                                penata=penata, bingkai=bingkai)
    if tekstur_ai and bingkai and not bingkai.lower().startswith("tanpa"):
        try:
            poster = process_one._engine.tekstur(poster, prompt)
        except Exception:                                  # noqa: BLE001
            pass
    out_path = os.path.join(out_dir, _unique_name(judul, used) + ".png")
    poster.save(out_path, quality=92)
    return {
        "ok": True,
        "sumber": path,
        "judul": judul,
        "keluar": out_path,
        "detik": info_detik,
        "ukuran": poster.size,
        "durasi_proses": round(time.time() - t0, 1),
        "video": is_vid,
    }


def run_batch(folder, out_dir=None, ratio_key="Ikuti rasio video", prompt=None,
              kualitas="Foto asli + sentuhan AI (paling setia)", log=None,
                progress=None,
              should_continue=None, template=None,
              rilis="SEGERA DI BIOSKOP", gaya_judul="Otomatis (menyesuaikan judul)",
              penata="Otomatis dari gambar", bingkai="Otomatis (dari gambar)",
              tekstur_ai=False):
    """Proses SEMUA video/foto di folder dengan SATU prompt AI yang sama.

    log(msg)               -> pesan kemajuan (mis. untuk Text di GUI / print)
    progress(selesai, total, nama_file)
    should_continue()      -> False untuk membatalkan
    Return: dict ringkasan {total, ok, gagal, dibatalkan, out_dir, hasil, errors}
    """
    log = log or (lambda s: None)
    progress = progress or (lambda *a: None)
    cont = should_continue or (lambda: True)

    # template: "Tanpa" -> None; nama di folder templates/ atau path file
    template_path = te.cari_template(template)
    if (template and str(template).strip().lower()
            not in ("tanpa", "tanpa template", "none") and template_path is None):
        raise ValueError("Template tidak ditemukan: %r — cek nama di folder "
                         "templates\\ (tanpa .png) atau pakai path file." % template)

    ok_model, got, total_bytes, _ = ai.model_status()
    if not ok_model:
        raise ValueError("Model AI belum terunduh lengkap (%d%%). "
                         "Buka aplikasi → tombol 🤖 Status Model AI → Unduh."
                         % (got * 100 // max(1, total_bytes)))

    files = collect_media(folder)
    if not files:
        raise ValueError("Tidak ada video/foto di folder itu. "
                         "Format yang dikenal: " + " ".join(fp.VIDEO_EXTS + IMG_EXTS))

    if out_dir is None:                       # folder hasil = folder sebelah
        folder = os.path.abspath(folder)
        out_dir = folder.rstrip(os.sep) + "_poster"
    os.makedirs(out_dir, exist_ok=True)

    prompt = (prompt or "").strip() or ai.DEFAULT_PROMPT
    used, hasil, errors = set(), [], []
    n = len(files)
    prompt_pendek = (prompt[:60] + "…") if len(prompt) > 60 else prompt
    log(f"Batch AI dimulai: {n} file → folder hasil: {out_dir}")
    log(f"Rasio: {ratio_key} · Kualitas: {kualitas}")
    log(f"Gaya judul: {gaya_judul} · Strip bawah: {rilis if rilis else '(dihapus)'}")
    log(f"Bingkai: {bingkai} · Penata: {penata}"
        + (" · Tekstur AI aktif" if tekstur_ai and bingkai
           and not bingkai.lower().startswith("tanpa") else ""))
    if template_path:
        log(f"Template: {os.path.basename(template_path)}")
    log(f"Prompt untuk SEMUA file: {prompt_pendek}")
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
            r = process_one(path, out_dir, ratio_key, prompt, kualitas, used,
                            log=log, template=template_path, rilis=rilis,
                            gaya_judul=gaya_judul, penata=penata,
                            bingkai=bingkai, tekstur_ai=tekstur_ai)
            hasil.append(r)
            done += 1
            sumber = f"detik {r['detik']} dari video" if r["video"] else "foto"
            log(f"    ✔ {r['judul']} — poster AI {r['ukuran'][0]}×{r['ukuran'][1]} px "
                f"({sumber}, {r['durasi_proses']} dtk)")
        except Exception as exc:              # noqa: BLE001 — satu gagal, lanjut lain
            errors.append({"sumber": path, "error": str(exc)})
            log(f"    ✘ GAGAL: {exc}")
    try:
        process_one._engine.free_all()        # lepas memori model
    except AttributeError:
        pass
    progress(done, n, "")
    log(f"SELESAI: {len(hasil)} poster AI berhasil, {len(errors)} gagal → {out_dir}")
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
        description="PosterBioskopAI MODE BATCH AI: folder video/foto → poster AI semua")
    ap.add_argument("folder", help="folder berisi video/foto")
    ap.add_argument("--out", default=None, help="folder hasil (bawaan: <folder>_poster)")
    ap.add_argument("--rasio", default="Ikuti rasio video",
                    choices=["Ikuti rasio video", "9:16", "16:9"])
    ap.add_argument("--prompt", default=None,
                    help="prompt AI untuk SEMUA file (bawaan: prompt sinematik Hollywood)")
    ap.add_argument("--kualitas",
                        default="Foto asli + sentuhan AI (paling setia)",
                    choices=list(ai.QUALITY_PRESETS.keys()))
    ap.add_argument("--bingkai", default="Otomatis (dari gambar)",
                    help="Otomatis (dari gambar) | Tanpa bingkai | "
                         + " | ".join(bingkai_mod.NAMA))
    ap.add_argument("--penata", default="Otomatis dari gambar",
                    help="Otomatis dari gambar | Klasik (putih-emas)")
    ap.add_argument("--tekstur-bingkai", action="store_true",
                    help="1 langkah img2img ekstra agar bingkai menyatu "
                         "dengan key art (lebih lambat)")
    ap.add_argument("--rilis", default="SEGERA DI BIOSKOP",
                    help="teks strip di bawah judul; kosongkan ('') untuk "
                         "menghapus strip")
    ap.add_argument("--gaya-judul", default="Otomatis (menyesuaikan judul)",
                    choices=list(eng.GAYA_JUDUL))
    ap.add_argument("--template", default="Tanpa",
                    help="nama template di folder templates/ (mis. 'klasik-emas-063') "
                         "atau path file PNG/JPG; 'Tanpa' = tipografi bawaan")
    a = ap.parse_args()

    try:
        res = run_batch(a.folder, a.out, a.rasio, a.prompt, a.kualitas, log=print,
                        template=a.template, rilis=a.rilis,
                        gaya_judul=a.gaya_judul, penata=a.penata,
                        bingkai=a.bingkai, tekstur_ai=a.tekstur_bingkai)
    except (ValueError, RuntimeError) as exc:
        # pesan ramah (folder kosong, model belum lengkap, mesin AI gagal) —
        # bukan traceback mentah
        print(f"GAGAL: {exc}")
        sys.exit(1)
    for e in res["errors"]:
        print(f"  gagal: {e['sumber']} — {e['error']}")
    print(f"\nPoster AI tersimpan di: {res['out_dir']}")
    sys.exit(0 if (res["ok"] > 0 and res["gagal"] == 0) else 1)


if __name__ == "__main__":
    main()
