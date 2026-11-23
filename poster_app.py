# -*- coding: utf-8 -*-
"""
PosterBioskopAI — aplikasi desktop OFFLINE pembuat poster film ala Hollywood.

Alur utama:
  1. Pilih VIDEO  -> judul poster otomatis dari NAMA VIDEO, frame terbaik dipilih
     otomatis (ketajaman + exposure + kontras).
     Pilih FOTO    -> judul diketik manual.
  2. Gaya poster dipilih otomatis dari 999 referensi gaya (auto-match lokal),
     atau dipilih manual lewat Galeri Referensi.
  3. Simpan poster resolusi tinggi (PNG/JPG).

Jalankan:  python poster_app.py
Build EXE: lihat README_ID.txt / build_windows.bat
"""

import os
import queue
import re
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from functools import partial

from PIL import Image, ImageTk

import batch_poster as bp
import poster_engine as eng
import frame_picker as fp
import style_library as lib

BG = "#141420"
PANEL = "#1c1c2a"
FG = "#eceaf2"
FG_DIM = "#9a96ac"
GOLD = "#f2c14e"
ACCENT = "#e8543f"
VIDEO_TYPES = [("Video", " ".join("*" + e for e in fp.VIDEO_EXTS)), ("Semua file", "*.*")]
IMG_TYPES = [("Gambar", "*.jpg *.jpeg *.png *.bmp *.webp"), ("Semua file", "*.*")]


class PosterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PosterBioskopAI — Pembuat Poster Film (Offline)")
        self.geometry("1200x800")
        self.minsize(1000, 660)
        self.configure(bg=BG)

        self.lib_ref = None            # perpustakaan 999 gaya (dimuat async)
        self.source_path = None
        self.source_img = None         # PIL: frame terbaik / foto
        self.source_stats = None
        self.source_info = None
        self.style = None
        self.alternatives = []
        self.preview_img = None        # PhotoImage preview besar
        self._busy = False
        self._gal_gen = 0

        self._style_ui()
        self._build_vars()
        self._build_ui()
        self.after(80, self._load_library_async)

    # ------------------------------------------------------------------ UI
    def _style_ui(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background=BG, foreground=FG, fieldbackground="#22222f",
                    bordercolor="#33334a", lightcolor="#33334a", darkcolor="#181822")
        s.configure("TFrame", background=BG)
        s.configure("Panel.TFrame", background=PANEL)
        s.configure("TLabel", background=BG, foreground=FG)
        s.configure("Panel.TLabel", background=PANEL, foreground=FG)
        s.configure("Dim.TLabel", background=PANEL, foreground=FG_DIM)
        s.configure("Gold.TLabel", background=PANEL, foreground=GOLD)
        s.configure("TLabelframe", background=PANEL, bordercolor="#33334a")
        s.configure("TLabelframe.Label", background=PANEL, foreground=GOLD,
                    font=("Segoe UI", 9, "bold"))
        s.configure("TEntry", insertcolor=FG)
        s.configure("TCombobox", fieldbackground="#22222f", arrowcolor=GOLD)
        s.configure("TCheckbutton", background=PANEL, foreground=FG)
        s.configure("TButton", background="#2a2a3c", foreground=FG, padding=6)
        s.map("TButton", background=[("active", "#3a3a52")])
        s.configure("Big.TButton", background=ACCENT, foreground="white",
                    font=("Segoe UI", 12, "bold"), padding=10)
        s.map("Big.TButton", background=[("active", "#ff6a52")])
        s.configure("Gold.TButton", background=GOLD, foreground="#1a1408",
                    font=("Segoe UI", 10, "bold"), padding=8)
        s.map("Gold.TButton", background=[("active", "#ffd97a")])

    def _build_vars(self):
        self.var_judul = tk.StringVar()
        self.var_tagline = tk.StringVar()
        self.var_pemain = tk.StringVar()
        self.var_sutradara = tk.StringVar()
        self.var_rasio = tk.StringVar(value="Poster 2:3")
        self.var_batch_rasio = tk.StringVar(value="Poster 2:3")
        self.var_auto = tk.BooleanVar(value=True)
        self.var_file = tk.StringVar(value="Belum ada video/foto dipilih")
        self.var_gaya = tk.StringVar(value="Gaya: menunggu sumber…")
        self.var_status = tk.StringVar(value="Memuat 999 referensi gaya…")
        self.var_alt = tk.StringVar()

    def _build_ui(self):
        root = ttk.Frame(self)
        root.pack(fill="both", expand=True)

        # ---------------- kolom kiri: kontrol ----------------
        left = ttk.Frame(root, width=360)
        left.pack(side="left", fill="y", padx=(10, 6), pady=10)
        left.pack_propagate(False)

        f1 = ttk.Labelframe(left, text=" 1. SUMBER ", padding=8)
        f1.pack(fill="x")
        ttk.Button(f1, text="🎬  Pilih VIDEO (judul otomatis dari nama video)",
                   command=self.pilih_video).pack(fill="x", pady=2)
        ttk.Button(f1, text="🖼️  Pilih FOTO", command=self.pilih_foto).pack(fill="x", pady=2)
        ttk.Label(f1, textvariable=self.var_file, style="Dim.TLabel",
                  wraplength=330, justify="left").pack(fill="x", pady=(4, 0))

        f2 = ttk.Labelframe(left, text=" 2. TEKS POSTER ", padding=8)
        f2.pack(fill="x", pady=(8, 0))
        for label, var, hint in (
                ("Judul film", self.var_judul, "dari video: diisi otomatis"),
                ("Tagline (opsional)", self.var_tagline, "kalimat promosi"),
                ("Pemain (pisah koma)", self.var_pemain, "nama di atas poster"),
                ("Sutradara (opsional)", self.var_sutradara, "masuk billing block")):
            ttk.Label(f2, text=label, style="Panel.TLabel").pack(anchor="w", pady=(4, 0))
            ttk.Entry(f2, textvariable=var).pack(fill="x")
            if hint:
                ttk.Label(f2, text=hint, style="Dim.TLabel").pack(anchor="w")

        f3 = ttk.Labelframe(left, text=" 3. GAYA & FORMAT ", padding=8)
        f3.pack(fill="x", pady=(8, 0))
        ttk.Checkbutton(f3, text="Pilih gaya OTOMATIS dari 999 referensi (AI lokal)",
                        variable=self.var_auto, command=self._toggle_auto).pack(anchor="w")
        ttk.Label(f3, text="Alternatif teratas:", style="Panel.TLabel").pack(anchor="w", pady=(6, 0))
        self.cmb_alt = ttk.Combobox(f3, textvariable=self.var_alt, state="disabled",
                                    values=[""], font=("Segoe UI", 8))
        self.cmb_alt.pack(fill="x")
        self.cmb_alt.bind("<<ComboboxSelected>>", self._on_alt)
        ttk.Button(f3, text="🗂️  Buka Galeri 999 Referensi", style="Gold.TButton",
                   command=self.open_gallery).pack(fill="x", pady=(8, 2))
        ttk.Label(f3, textvariable=self.var_gaya, style="Dim.TLabel",
                  wraplength=330, justify="left").pack(fill="x", pady=(4, 0))
        row = ttk.Frame(f3)
        row.pack(fill="x", pady=(6, 0))
        ttk.Label(row, text="Rasio:", style="Panel.TLabel").pack(side="left")
        cmb = ttk.Combobox(row, textvariable=self.var_rasio, state="readonly",
                           values=list(eng.RATIOS.keys()), width=16)
        cmb.pack(side="left", padx=6)
        cmb.bind("<<ComboboxSelected>>", lambda e: self._render_async())

        ttk.Button(left, text="🎟️  BUAT POSTER!", style="Big.TButton",
                   command=self.buat_poster).pack(fill="x", pady=(12, 4))
        ttk.Button(left, text="💾  Simpan Poster Resolusi Tinggi…",
                   style="Gold.TButton", command=self.simpan).pack(fill="x")

        f4 = ttk.Labelframe(left, text=" MODE BATCH ", padding=8)
        f4.pack(fill="x", pady=(10, 0))
        ttk.Label(f4, text="Satu folder video/foto → poster untuk SEMUA file "
                           "(judul & gaya otomatis per file).",
                  style="Dim.TLabel", wraplength=330, justify="left").pack(anchor="w")
        rowb = ttk.Frame(f4)
        rowb.pack(fill="x", pady=(6, 0))
        ttk.Label(rowb, text="Gaya:", style="Panel.TLabel").pack(side="left")
        self.cmb_batch_gaya = ttk.Combobox(rowb, state="readonly", width=22,
                                           values=["Auto-match per video",
                                                   "Pakai gaya terpilih di atas"])
        self.cmb_batch_gaya.set("Auto-match per video")
        self.cmb_batch_gaya.pack(side="left", padx=6)
        rowb2 = ttk.Frame(f4)
        rowb2.pack(fill="x", pady=(4, 0))
        ttk.Label(rowb2, text="Rasio:", style="Panel.TLabel").pack(side="left")
        ttk.Combobox(rowb2, textvariable=self.var_batch_rasio, state="readonly",
                     values=list(eng.RATIOS.keys()), width=16).pack(side="left", padx=6)
        ttk.Button(f4, text="📦  Batch: Pilih Folder & Buat Semua…",
                   style="Gold.TButton", command=self.batch_folder).pack(fill="x", pady=(6, 2))

        # ---------------- kolom kanan: preview ----------------
        right = ttk.Frame(root)
        right.pack(side="left", fill="both", expand=True, padx=(6, 10), pady=10)
        self.canvas = tk.Canvas(right, bg="#0c0c14", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self._place_preview())

        ttk.Label(self, textvariable=self.var_status, style="Dim.TLabel",
                  padding=(12, 4)).pack(fill="x", side="bottom")

    # ------------------------------------------------------- perpustakaan
    def _load_library_async(self):
        def work():
            lib.library()                     # build sekali & cache
            self.after(0, self._library_ready)
        threading.Thread(target=work, daemon=True).start()

    def _library_ready(self):
        self.lib_ref = lib.library()
        self.var_status.set("Siap! 999 referensi gaya dimuat. Pilih video/foto untuk mulai.")

    # ------------------------------------------------------------ sumber
    def pilih_video(self):
        path = filedialog.askopenfilename(title="Pilih video", filetypes=VIDEO_TYPES)
        if not path:
            return
        self.var_file.set(os.path.basename(path))
        self.var_status.set("Menganalisis video… mencari frame terbaik.")
        self.source_path = path

        def work():
            try:
                img, stats, info = fp.extract_best_frame(path)
            except Exception as exc:                       # noqa: BLE001
                self.after(0, lambda: messagebox.showerror("Gagal", str(exc)))
                self.after(0, lambda: self.var_status.set("Gagal membaca video."))
                return
            self.after(0, lambda: self._source_ready(img, stats, info, from_video=True))
        threading.Thread(target=work, daemon=True).start()

    def pilih_foto(self):
        path = filedialog.askopenfilename(title="Pilih foto", filetypes=IMG_TYPES)
        if not path:
            return
        try:
            img = Image.open(path)
        except Exception as exc:                           # noqa: BLE001
            messagebox.showerror("Gagal", f"Foto tidak bisa dibuka:\n{exc}")
            return
        self.source_path = path
        self.var_file.set(os.path.basename(path))
        stats = lib.analyze_image(img)
        self._source_ready(img, stats, {"jumlah_sampel": 1}, from_video=False)

    def _source_ready(self, img, stats, info, from_video):
        self.source_img = img
        self.source_stats = stats
        self.source_info = info
        if from_video:
            judul = fp.title_from_filename(self.source_path)
            self.var_judul.set(judul)
            det = info.get("waktu_detik", 0)
            self.var_status.set(
                f"Frame terbaik dipilih otomatis: detik {det} "
                f"(skor {info.get('skor', '-')}, {info.get('jumlah_sampel', 0)} sampel). "
                f"Judul otomatis: “{judul}”.")
        else:
            self.var_status.set("Foto dimuat. Ketik judul, lalu klik BUAT POSTER!")
        self._auto_match()
        self._render_async()

    # ------------------------------------------------------- gaya / match
    def _auto_match(self):
        if not (self.var_auto.get() and self.source_stats):
            return
        scored = lib.match_styles(self.source_stats, top_n=6)
        self.alternatives = scored
        self.style = scored[0][1]
        alasan = lib.explain_match(self.source_stats, self.style)
        self.var_gaya.set(f"{self.style['id']} · {self.style['name']}\n{alasan}")
        self.cmb_alt.config(state="readonly",
                            values=[f"{s['id']} · {s['genre_label']} — {s['era_label']}"
                                    for _, s in scored])
        self.var_alt.set(self.cmb_alt.cget("values")[0])

    def _toggle_auto(self):
        if self.var_auto.get():
            self._auto_match()
            self._render_async()
        elif self.style:
            self.var_gaya.set(f"Dipilih manual: {self.style['id']} · {self.style['name']}")

    def _on_alt(self, _e=None):
        idx = self._combo_index()
        if 0 <= idx < len(self.alternatives):
            self.style = self.alternatives[idx][1]
            self.var_gaya.set(f"Alternatif: {self.style['id']} · {self.style['name']}")
            self._render_async()

    def _combo_index(self):
        val = self.var_alt.get()
        for i, v in enumerate(self.cmb_alt.cget("values")):
            if v == val:
                return i
        return -1

    # ------------------------------------------------------------ render
    def _texts(self):
        return (self.var_judul.get(), self.var_tagline.get(),
                self.var_pemain.get(), self.var_sutradara.get())

    def buat_poster(self):
        if not self.source_img:
            messagebox.showinfo("Belum ada sumber", "Pilih VIDEO atau FOTO dulu ya, kawan!")
            return
        if not self.style:
            self._auto_match()
        self._render_async()

    def _render_async(self):
        if not self.source_img or self._busy:
            return
        self._busy = True
        self.var_status.set("Merender poster…")
        style = self.style
        ratio = self.var_rasio.get()
        judul, tagline, pemain, sutradara = self._texts()
        img_src = self.source_img
        size = eng.preview_size(ratio)

        def work():
            try:
                poster = eng.render_poster(img_src, style, judul, tagline, pemain,
                                           sutradara, size=size)
            except Exception as exc:                       # noqa: BLE001
                self.after(0, lambda: self.var_status.set(f"Gagal render: {exc}"))
                self.after(0, self._render_done)
                return
            self.after(0, lambda: self._show_preview(poster))
        threading.Thread(target=work, daemon=True).start()

    def _render_done(self):
        self._busy = False

    def _show_preview(self, poster):
        self._busy = False
        self._poster_preview = poster
        self._tk_preview = ImageTk.PhotoImage(poster)
        self._place_preview()
        self.var_status.set(
            f"Poster siap! Gaya {self.style['id'] if self.style else '-'} · "
            f"{self.var_rasio.get()} · {poster.size[0]}×{poster.size[1]} px. "
            "Klik Simpan untuk resolusi tinggi.")

    def _place_preview(self):
        if not hasattr(self, "_tk_preview"):
            return
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 10 or ch < 10:
            return
        self.canvas.delete("all")
        im = self._tk_preview
        r = min(cw / im.width(), ch / im.height(), 1.0)
        if r < 1.0:
            w = max(1, int(im.width() * r))
            h = max(1, int(im.height() * r))
            im = ImageTk.PhotoImage(self._poster_preview.resize((w, h), eng.RESAMPLE))
            self._tk_scaled = im   # jaga referensi agar gambar tidak hilang
        self.canvas.create_image(cw // 2, ch // 2, image=im, anchor="center")

    def simpan(self):
        if not self.source_img:
            messagebox.showinfo("Belum ada sumber", "Pilih VIDEO atau FOTO dulu ya!")
            return
        judul = self.var_judul.get().strip() or "poster"
        safe = re.sub(r"[^\w\- ]", "", judul).strip() or "poster"
        path = filedialog.asksaveasfilename(
            title="Simpan poster", initialfile=safe,
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPG", "*.jpg")])
        if not path:
            return
        self.var_status.set("Merender resolusi tinggi…")
        style = self.style
        ratio = self.var_rasio.get()
        judul_v, tagline, pemain, sutradara = self._texts()
        size = eng.FULL_SIZES.get(ratio, (1000, 1500))
        img_src = self.source_img

        def work():
            try:
                poster = eng.render_poster(img_src, style, judul_v, tagline, pemain,
                                           sutradara, size=size)
                poster.save(path, quality=92)
                ok, err, p = True, None, path
            except Exception as exc:                       # noqa: BLE001
                ok, err, p = False, str(exc), path
            self.after(0, lambda: self._saved(ok, err, p))
        threading.Thread(target=work, daemon=True).start()

    def _saved(self, ok, err, path):
        if ok:
            self.var_status.set(f"Tersimpan: {path}")
            messagebox.showinfo("Tersimpan!", f"Poster tersimpan di:\n{path}")
        else:
            messagebox.showerror("Gagal simpan", err)

    # ------------------------------------------------------- mode batch
    def batch_folder(self):
        folder = filedialog.askdirectory(title="Pilih folder berisi video/foto untuk batch")
        if not folder:
            return
        pakai_gaya_terpilih = self.cmb_batch_gaya.get().startswith("Pakai")
        if pakai_gaya_terpilih and not self.style:
            messagebox.showinfo(
                "Belum ada gaya terpilih",
                "Untuk mode \"Pakai gaya terpilih\", pilih dulu video/foto atau gaya "
                "lewat Galeri. Atau pakai \"Auto-match per video\".")
            return
        try:
            files = bp.collect_media(folder)
        except (NotADirectoryError, ValueError) as exc:
            messagebox.showerror("Gagal", str(exc))
            return
        if not files:
            messagebox.showinfo(
                "Folder kosong",
                "Tidak ada video/foto yang dikenali di folder itu.\n"
                "Format yang didukung: " + " ".join(fp.VIDEO_EXTS + bp.IMG_EXTS))
            return
        style_id = self.style["id"] if pakai_gaya_terpilih else None
        self._open_batch_dialog(folder, len(files), self.var_batch_rasio.get(), style_id)

    def _open_batch_dialog(self, folder, n, ratio, style_id):
        q = queue.Queue()
        win = tk.Toplevel(self)
        win.title(f"Mode Batch — {n} file")
        win.geometry("640x440")
        win.configure(bg=BG)

        head = ttk.Frame(win, padding=(12, 10))
        head.pack(fill="x")
        ttk.Label(head, text=f"{n} file akan dirender ({ratio})", style="Gold.TLabel").pack(anchor="w")
        bar = ttk.Progressbar(win, maximum=n, length=560)
        bar.pack(fill="x", padx=12)
        lbl_file = ttk.Label(win, text="Menyiapkan…", style="TLabel", padding=(12, 6))
        lbl_file.pack(fill="x")

        body = ttk.Frame(win)
        body.pack(fill="both", expand=True, padx=12)
        txt = tk.Text(body, height=11, bg="#101018", fg=FG, bd=0,
                      insertbackground=FG, wrap="word")
        sb = ttk.Scrollbar(body, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)

        cancel = {"v": False}
        btn_cancel = ttk.Button(win, text="Batalkan", command=lambda: cancel.update(v=True))
        btn_cancel.pack(pady=8)

        def log(msg):
            q.put(("log", msg))

        def prog(done, total, name):
            q.put(("prog", done, total, name))

        def finish(res):
            bar["value"] = res.get("ok", 0)
            lbl_file.config(text=f"Selesai: {res.get('ok', 0)} poster berhasil, "
                                 f"{res.get('gagal', 0)} gagal"
                                 + (" (dibatalkan)" if res.get("dibatalkan") else ""))
            btn_cancel.config(state="disabled", text="Tutup")
            out = res.get("out_dir", folder)
            if messagebox.askyesno("Batch selesai",
                                   f"Poster: {res.get('ok', 0)} berhasil, {res.get('gagal', 0)} gagal.\n"
                                   f"Folder hasil:\n{out}\n\nBuka folder hasil?"):
                bp.open_folder(out)

        def poll():
            try:
                while True:
                    msg = q.get_nowait()
                    kind = msg[0]
                    if kind == "log":
                        txt.insert("end", msg[1] + "\n")
                        txt.see("end")
                    elif kind == "prog":
                        _, done, total, name = msg
                        bar["maximum"] = max(1, total)
                        bar["value"] = done
                        lbl_file.config(text=name or "Merender…")
                    elif kind == "done":
                        finish(msg[1])
                        return                      # berhenti polling
            except queue.Empty:
                pass
            win.after(120, poll)

        def work():
            try:
                res = bp.run_batch(folder, None, ratio, style_id,
                                   log=log, progress=prog,
                                   should_continue=lambda: not cancel["v"])
            except Exception as exc:                # noqa: BLE001
                q.put(("log", f"GAGAL: {exc}"))
                res = {"ok": 0, "gagal": 1, "dibatalkan": False, "out_dir": folder}
            q.put(("done", res))

        threading.Thread(target=work, daemon=True).start()
        poll()

    # ------------------------------------------------------- galeri 999
    def open_gallery(self):
        if not self.lib_ref:
            messagebox.showinfo("Sebentar", "Perpustakaan masih dimuat, coba lagi 1 detik lagi.")
            return
        self._gal_gen += 1
        win = tk.Toplevel(self)
        win.title("Galeri 999 Referensi Gaya — klik untuk pakai")
        win.geometry("980x660")
        win.configure(bg=BG)

        top = ttk.Frame(win, padding=6)
        top.pack(fill="x")
        ttk.Label(top, text="Cari:", style="TLabel").pack(side="left")
        q = ttk.Entry(top, width=24)
        q.pack(side="left", padx=6)
        ttk.Label(top, text="Genre:", style="TLabel").pack(side="left", padx=(12, 0))
        gf = ttk.Combobox(top, state="readonly", width=14,
                          values=["Semua"] + [gl for _, gl in lib.GENRES])
        gf.set("Semua")
        gf.pack(side="left", padx=6)
        ttk.Label(top, text="Era:", style="TLabel").pack(side="left", padx=(12, 0))
        ef = ttk.Combobox(top, state="readonly", width=18,
                          values=["Semua"] + [el for _, el in lib.ERAS])
        ef.set("Semua")
        ef.pack(side="left", padx=6)

        body = ttk.Frame(win)
        body.pack(fill="both", expand=True)
        cvs = tk.Canvas(body, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(body, orient="vertical", command=cvs.yview)
        inner = ttk.Frame(cvs)
        inner.bind("<Configure>",
                   lambda e: cvs.configure(scrollregion=cvs.bbox("all")))
        cvs.create_window((0, 0), window=inner, anchor="nw")
        cvs.configure(yscrollcommand=sb.set)
        cvs.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self._tk_imgs = []

        def refresh(*_a):
            self._gal_gen += 1
            for c in inner.winfo_children():
                c.destroy()
            genre = None if gf.get() == "Semua" else \
                next(k for k, gl in lib.GENRES if gl == gf.get())
            era = None if ef.get() == "Semua" else \
                next(k for k, el in lib.ERAS if el == ef.get())
            items = lib.filter_styles(genre, era, q.get())
            ttk.Label(inner, text=f"{len(items)} referensi ditemukan",
                      style="Gold.TLabel").grid(row=0, column=0, columnspan=8,
                                                sticky="w", padx=6, pady=4)
            self._populate(inner, items, self._gal_gen)

        q.bind("<KeyRelease>", refresh)
        gf.bind("<<ComboboxSelected>>", refresh)
        ef.bind("<<ComboboxSelected>>", refresh)
        refresh()

    def _populate(self, inner, items, gen):
        if not items:
            return
        cols = 7
        state = {"i": 0}

        def batch():
            if gen != self._gal_gen:
                return
            end = min(len(items), state["i"] + 28)
            for n in range(state["i"], end):
                s = items[n]
                r, c = divmod(n + 1, cols)
                self._make_thumb(inner, s, r, c)
            state["i"] = end
            if state["i"] < len(items):
                inner.after(30, batch)
        batch()

    def _make_thumb(self, inner, s, r, c):
        try:
            scene = eng.placeholder_scene(96, 144, s["palette"], seed=s["index"] % 19)
            thumb = eng.render_poster(scene, s, s["genre_label"], size=(96, 144),
                                      minimal=True)
        except Exception:                                  # noqa: BLE001
            return
        img = ImageTk.PhotoImage(thumb)
        self._tk_imgs.append(img)
        cell = ttk.Frame(inner)
        cell.grid(row=r, column=c, padx=4, pady=4)
        btn = tk.Button(cell, image=img, bd=0, bg="#000000", cursor="hand2",
                        command=partial(self._use_style, s, cell))
        btn.pack()
        ttk.Label(cell, text=s["id"], style="Dim.TLabel").pack()

    def _use_style(self, s, cell=None):
        self.style = s
        self.var_auto.set(False)
        self.var_gaya.set(f"Dipilih manual: {s['id']} · {s['name']}")
        self._render_async()
        for w in self.winfo_children():
            if isinstance(w, tk.Toplevel) and "Galeri" in w.title():
                w.destroy()
        self.lift()


def main():
    app = PosterApp()
    app.mainloop()


if __name__ == "__main__":
    main()
