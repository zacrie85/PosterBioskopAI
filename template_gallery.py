# -*- coding: utf-8 -*-
"""Galeri pemilih template PosterBioskopAI.

Memudahkan memilih 1 dari 131 template secara MANUAL:
- jendela galeri: semua template tampil sebagai pratinjau poster kecil
  (klik satu gambar -> langsung terpasang di dropdown aplikasi);
- nama ramah Indonesia dari tabel FAMILI/PALET di buat_template131.py,
  mis. "Festival Senja #034" untuk berkas festival-senja-034;
- pratinjau di-cache di templates\\_pratinjau\\<nama>.jpg (dibuat sekali,
  ikut dibundel di EXE) supaya galeri terbuka seketika;
- katalog besar (templates\\_katalog-template.jpg) bisa dibuka sebagai
  gambar biasa tanpa menjalankan aplikasi.
Berkas pratinjau/katalog memakai awalan "_" sehingga tidak dianggap
template oleh template_engine.list_templates().
"""

import os
import queue

from PIL import Image, ImageDraw

import poster_engine as eng
import template_engine as te
from buat_template131 import FAMILI, PALET

RESAMPLE = eng.RESAMPLE
UK_TN = (270, 480)              # ukuran thumbnail pratinjau (portrait)

# slug keluarga/palet -> nama Indonesia (dari tabel generator)
_NAMA_KELUARGA = {slug: label for label, slug, _cfg in FAMILI}
_NAMA_PALET = {slug: slug.capitalize() for slug, _hex, _bg in PALET}


def art_contoh(size=UK_TN):
    """Key art sintetis (gradasi senja + matahari + bukit) untuk pratinjau."""
    W, H = size
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / max(1, H - 1)
        d.line([(0, y), (W, y)],
               fill=(int(88 + 120 * t), int(52 + 62 * t), int(40 + 130 * (1 - t))))
    d.ellipse([W * 0.33, H * 0.24, W * 0.67, H * 0.42], fill=(255, 206, 104))
    d.polygon([(0, H), (W, H), (W, H * 0.70), (0, H * 0.76)], fill=(26, 18, 34))
    d.polygon([(0, H), (W * 0.55, H), (W * 0.30, H * 0.80)], fill=(14, 10, 20))
    return img


def folder_pratinjau():
    """Folder cache pratinjau: templates\\_pratinjau."""
    return os.path.join(te.folder_templates(), "_pratinjau")


def path_pratinjau(nama):
    return os.path.join(folder_pratinjau(), nama + ".jpg")


def render_thumbnail(nama, judul="BENANG CAHAYA", tagline="Sebuah kisah nyata",
                     size=UK_TN):
    """Compose template + art contoh pada ukuran thumbnail. Return PIL RGB."""
    return eng.compose_poster(art_contoh(size), judul, size=size,
                              tagline=tagline, template=te.cari_template(nama))


def pastikan_pratinjau(daftar=None, progress=None):
    """Pastikan cache pratinjau lengkap; buat yang belum ada.
    progress(selesai, total, nama) opsional. Return list path cache."""
    daftar = daftar if daftar is not None else te.list_templates()
    os.makedirs(folder_pratinjau(), exist_ok=True)
    out = []
    n = len(daftar)
    for i, t in enumerate(daftar):
        p = path_pratinjau(t["nama"])
        if not os.path.isfile(p):
            try:
                render_thumbnail(t["nama"]).save(p, quality=85)
            except Exception:
                continue
        if progress:
            progress(i + 1, n, t["nama"])
        out.append(p)
    return out


def nama_tampil(t):
    """Nama ramah pengguna, mis. 'Festival Senja #034'."""
    m = t["nama"].rsplit("-", 1)          # festival-senja-034 -> [festival-senja, 034]
    nomor = m[1] if len(m) == 2 and m[1].isdigit() else ""
    bagian = m[0].split("-")
    # slug berformat keluarga[-varian]-palet: palet = token terakhir
    slug_kel = "-".join(bagian[:-1])
    slug_pal = bagian[-1] if len(bagian) > 1 else ""
    kel = _NAMA_KELUARGA.get(slug_kel) or slug_kel.replace("-", " ").capitalize()
    pal = _NAMA_PALET.get(slug_pal, slug_pal.capitalize())
    dasar = (kel + " " + pal).strip()
    return f"{dasar} #{nomor}" if nomor else dasar


def buat_katalog(kolom=8, cell=(200, 356), label_px=26):
    """Katalog besar semua template (grid + nama) -> _katalog-template.jpg.
    Return path gambar katalog."""
    daftar = te.list_templates()
    pastikan_pratinjau(daftar)
    baris = (len(daftar) + kolom - 1) // kolom
    margin, lebar_kolom = 12, cell[0]
    W = margin * 2 + kolom * lebar_kolom + (kolom - 1) * 8
    tinggi_sel = cell[1] + label_px
    H = margin * 2 + baris * (tinggi_sel + 8)
    lembar = Image.new("RGB", (W, H), (24, 24, 34))
    d = ImageDraw.Draw(lembar)
    for i, t in enumerate(daftar):
        r, c = divmod(i, kolom)
        x = margin + c * (lebar_kolom + 8)
        y = margin + r * (tinggi_sel + 8)
        try:
            tn = Image.open(path_pratinjau(t["nama"])).resize(cell, RESAMPLE)
            lembar.paste(tn, (x, y))
        except Exception:
            d.rectangle([x, y, x + cell[0], y + cell[1]], fill=(60, 60, 70))
        nama = nama_tampil(t)
        f = eng.get_font("credit", 13)
        tw = eng.text_w(f, nama)
        d.text((x + (cell[0] - tw) / 2, y + cell[1] + 5), nama, font=f,
               fill=(235, 231, 222))
    out = os.path.join(te.folder_templates(), "_katalog-template.jpg")
    lembar.save(out, quality=82)
    return out


def tampilkan_galeri(parent, var_template, status=None):
    """Jendela galeri: klik pratinjau untuk memilih template.
    var_template = tk.StringVar aplikasi; status = tk.StringVar status bar."""
    import threading
    import tkinter as tk
    from tkinter import ttk
    from PIL import ImageTk

    daftar = te.list_templates()

    win = tk.Toplevel(parent)
    win.title("Pilih Template — 131 desain Hollywood")
    win.configure(bg="#1a1a26")
    win.geometry("1080x700")
    win.transient(parent)

    info = ttk.Label(win, text="Klik satu pratinjau untuk memakai template itu. "
                     "Nama = Keluarga Palet (mis. Festival Senja).",
                     style="Dim.TLabel")
    info.pack(fill="x", padx=10, pady=(8, 2))
    bar = ttk.Progressbar(win, maximum=len(daftar), length=300)
    teks = ttk.Label(win, text="Menyiapkan pratinjau…", style="Dim.TLabel")
    teks.pack(fill="x", padx=10)
    bar.pack(fill="x", padx=10, pady=(2, 8))

    frame = ttk.Frame(win)
    kanvas = tk.Canvas(frame, bg="#1a1a26", highlightthickness=0)
    geser = ttk.Scrollbar(frame, orient="vertical", command=kanvas.yview)
    kanvas.configure(yscrollcommand=geser.set)
    dalam = ttk.Frame(kanvas, bg="#1a1a26")
    dalam.bind("<Configure>", lambda e: kanvas.configure(
        scrollregion=kanvas.bbox("all")))
    kanvas.create_window((0, 0), window=dalam, anchor="nw")
    kanvas.bind_all("<MouseWheel>", lambda e: kanvas.yview_scroll(
        int(-e.delta / 120), "units"))
    win.bind("<Destroy>", lambda e: kanvas.unbind_all("<MouseWheel>"))

    imgs = {}          # nama -> PhotoImage (jaga referensi agar tak di-GC)

    def pasang_grid():
        teks.pack_forget()
        bar.pack_forget()
        frame.pack(fill="both", expand=True)
        geser.pack(side="right", fill="y")
        kanvas.pack(side="left", fill="both", expand=True)
        sekarang = var_template.get()
        for i, t in enumerate(daftar):
            cell = ttk.Frame(dalam, padding=4)
            cell.grid(row=i // 5, column=i % 5, padx=3, pady=3)
            try:
                im = Image.open(path_pratinjau(t["nama"])).resize((186, 330),
                                                                  RESAMPLE)
                ph = ImageTk.PhotoImage(im)
                imgs[t["nama"]] = ph
            except Exception:
                ph = None
            nama = nama_tampil(t)
            ttk.Label(cell, text=nama + ("  ◀ dipakai" if t["nama"] == sekarang
                                         else ""), style="Dim.TLabel",
                      wraplength=186, justify="center").pack()
            if ph is None:
                ttk.Label(cell, text="(pratinjau gagal)",
                          style="Dim.TLabel").pack()
                continue
            klik = ttk.Label(cell, image=ph, cursor="hand2")
            klik.pack()
            klik.bind("<Button-1>", lambda e, tn=t: pilih(tn))
        kanvas.yview_moveto(0.0)

    def pilih(t):
        var_template.set(t["nama"])
        if status is not None:
            status.set("Template dipilih: %s — klik BUAT POSTER untuk "
                       "melihatnya di film kamu." % nama_tampil(t))
        win.destroy()

    def kerja():                       # thread: buat cache yang belum ada
        pastikan_pratinjau(daftar, progress=lambda i, n, nm: q.put((i, n)))
        q.put(("selesai", 0))

    q = queue.Queue()
    threading.Thread(target=kerja, daemon=True).start()

    def poll():
        try:
            i, n = q.get_nowait()
        except queue.Empty:
            win.after(80, poll)
            return
        if i == "selesai":
            pasang_grid()
            return
        bar["maximum"] = n
        bar["value"] = i
        teks.config(text="Menyiapkan pratinjau template… %d/%d" % (i, n))
        win.after(80, poll)

    win.after(80, poll)

    def tanpa():
        var_template.set("Tanpa template")
        if status is not None:
            status.set("Tanpa template — layout judul bawaan mesin tipografi.")
        win.destroy()

    ttk.Button(win, text="Tanpa template (AI penuh)", command=tanpa).pack(
        side="left", padx=10, pady=(0, 8))
    ttk.Button(win, text="✓ Tutup", command=win.destroy).pack(
        side="right", padx=10, pady=(0, 8))
