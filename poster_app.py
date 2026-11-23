# -*- coding: utf-8 -*-
"""
PosterBioskopAI — aplikasi desktop OFFLINE pembuat poster film ala Hollywood.

Versi 2.0.1 — perbaikan stabilitas: semua kesalahan (Python maupun crash level
  sistem) kini dicatat ke log_kesalahan.txt di samping aplikasi dan ditampilkan
  sebagai jendela pesan — tidak ada lagi mati diam-diam.
Versi 2.0 — ROMBAKAN TOTAL:
  * Perpustakaan 999 referensi gaya DIHAPUS. Digantikan MESIN AI generatif
    (Stable Diffusion Turbo, ONNX, berjalan lokal tanpa internet).
  * Frame terbaik video diubah AI menjadi key art poster sesuai PROMPT.
  * Prompt bawaan terisi otomatis; bisa diketik manual; bisa diterapkan ke
    SEMUA video yang diproses batch.
  * Rasio poster: ikuti rasio video, 9:16 (Story/Reels), atau 16:9 (Layar).
  * Tulisan judul dijamin tidak melewati batas kiri-kanan (margin aman).

Alur utama:
  1. Pilih VIDEO -> judul poster otomatis dari nama video, frame terbaik
     dipilih otomatis (ketajaman + exposure + kontras). Pilih FOTO -> judul
     diketik manual.
  2. Prompt AI (bawaan atau manual) menggambar ulang frame jadi key art.
  3. Judul & teks lain dipasang di atas key art dengan margin aman.
  4. Simpan poster resolusi tinggi (PNG/JPG).

Jalankan:  python poster_app.py
Build EXE: lihat README_ID.txt / build_windows.bat
"""

import faulthandler
import os
import queue
import re
import sys
import threading
import traceback
from datetime import datetime

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from PIL import Image, ImageTk

import batch_poster as bp
import poster_ai as ai
import poster_engine as eng
import frame_picker as fp

BG = "#141420"
PANEL = "#1c1c2a"
FG = "#eceaf2"
FG_DIM = "#9a96ac"
GOLD = "#f2c14e"
ACCENT = "#e8543f"
OK = "#5ec269"
VIDEO_TYPES = [("Video", " ".join("*" + e for e in fp.VIDEO_EXTS)), ("Semua file", "*.*")]
IMG_TYPES = [("Gambar", "*.jpg *.jpeg *.png *.bmp *.webp"), ("Semua file", "*.*")]


# ------------------------------------------------------------ log kesalahan
def _log_path():
    """Tempat log_kesalahan.txt: di samping aplikasi; kalau folder itu tidak
    bisa ditulisi, pakai folder sementara Windows."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(base, "log_kesalahan.txt")
    try:
        open(p, "a").close()
        return p
    except OSError:
        import tempfile
        return os.path.join(tempfile.gettempdir(), "PosterBioskopAI_log_kesalahan.txt")


def catat_kesalahan(logf, tipe, nilai, tb):
    """Catat traceback lengkap ke file log (semua penangkap crash memakai ini)."""
    try:
        logf.write("\n[%s] KESALAHAN: %s: %s\n" % (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tipe.__name__, nilai))
        traceback.print_exception(tipe, nilai, tb, file=logf)
        logf.flush()
    except Exception:                                  # noqa: BLE001
        pass


class PosterApp(tk.Tk):
    def __init__(self, log=None):
        super().__init__()
        self._log = log
        self.title("PosterBioskopAI — Pembuat Poster Film AI (Offline)")
        self.geometry("1200x800")
        self.minsize(1000, 660)
        self.configure(bg=BG)

        self.source_path = None
        self.source_img = None        # PIL: frame terbaik / foto
        self.source_info = None
        self.poster_ai = ai.PosterAI()
        self.preview_img = None
        self._busy = False

        self._style_ui()
        self._build_vars()
        self._build_ui()
        self.after(200, self._refresh_model_status)

    def report_callback_exception(self, exc, val, tb):
        """Tk memanggil ini untuk setiap error di callback UI:
        catat ke log lalu tampilkan — jangan biarkan mati diam-diam."""
        catat_kesalahan(self._log, exc, val, tb)
        nama = exc.__name__ if isinstance(exc, type) else type(exc).__name__
        messagebox.showerror(
            "Terjadi kesalahan",
            "%s: %s\n\nDetail teknis ada di log_kesalahan.txt di samping aplikasi."
            % (nama, val))

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
        s.configure("Green.TLabel", background=PANEL, foreground=OK)
        s.configure("TLabelframe", background=PANEL, bordercolor="#33334a")
        s.configure("TLabelframe.Label", background=PANEL, foreground=GOLD,
                    font=("Segoe UI", 9, "bold"))
        s.configure("TEntry", insertcolor=FG)
        s.configure("TCombobox", fieldbackground="#22222f", arrowcolor=GOLD)
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
        self.var_rasio = tk.StringVar(value=ai.RASIOS[0])
        self.var_batch_rasio = tk.StringVar(value=ai.RASIOS[0])
        self.var_kualitas = tk.StringVar(value="Normal (2 langkah)")
        self.var_file = tk.StringVar(value="Belum ada video/foto dipilih")
        self.var_model = tk.StringVar(value="Model AI: memeriksa…")
        self.var_status = tk.StringVar(value="Selamat datang! Pilih video/foto untuk mulai.")
        self.var_prompt_semua = tk.BooleanVar(value=True)   # prompt dipakai semua video

    def _build_ui(self):
        root = ttk.Frame(self)
        root.pack(fill="both", expand=True)

        # ---------------- kolom kiri: kontrol ----------------
        left = ttk.Frame(root, width=380)
        left.pack(side="left", fill="y", padx=(10, 6), pady=10)
        left.pack_propagate(False)

        f1 = ttk.Labelframe(left, text=" 1. SUMBER ", padding=8)
        f1.pack(fill="x")
        ttk.Button(f1, text="🎬  Pilih VIDEO (judul otomatis dari nama video)",
                   command=self.pilih_video).pack(fill="x", pady=2)
        ttk.Button(f1, text="🖼️  Pilih FOTO", command=self.pilih_foto).pack(fill="x", pady=2)
        ttk.Label(f1, textvariable=self.var_file, style="Dim.TLabel",
                  wraplength=350, justify="left").pack(fill="x", pady=(4, 0))

        # ---------------- panel PROMPT AI (inti baru) ----------------
        f2 = ttk.Labelframe(left, text=" 2. PROMPT AI (inti poster) ", padding=8)
        f2.pack(fill="x", pady=(8, 0))
        ttk.Label(f2, text="Intruksi untuk AI mengubah frame jadi poster:",
                  style="Dim.TLabel").pack(anchor="w")
        self.txt_prompt = tk.Text(f2, height=4, bg="#22222f", fg=FG, bd=0,
                                  insertbackground=FG, wrap="word",
                                  font=("Segoe UI", 9))
        self.txt_prompt.pack(fill="x", pady=(3, 4))
        self.txt_prompt.insert("1.0", ai.DEFAULT_PROMPT)

        rowp = ttk.Frame(f2)
        rowp.pack(fill="x")
        ttk.Button(rowp, text="↺ Prompt Default", command=self.pakai_prompt_default,
                   style="TButton").pack(side="left", pady=2)
        self.btn_prompt_semua = ttk.Button(
            rowp, text="✓ Terapkan ke Semua Video", style="Gold.TButton",
            command=self.toggle_prompt_semua)
        self.btn_prompt_semua.pack(side="left", padx=(6, 0), pady=2)
        ttk.Label(f2, text="Judul video otomatis ditulis sebagai judul poster "
                           "(teks dipasang rapi di dalam batas gambar).",
                  style="Dim.TLabel", wraplength=350, justify="left").pack(anchor="w",
                                                                          pady=(4, 0))

        # ---------------- teks poster ----------------
        f3 = ttk.Labelframe(left, text=" 3. TEKS POSTER (opsional) ", padding=8)
        f3.pack(fill="x", pady=(8, 0))
        for label, var, hint in (
                ("Judul film", self.var_judul, "dari video: diisi otomatis"),
                ("Tagline (opsional)", self.var_tagline, "kalimat promosi di atas judul"),
                ("Pemain (pisah koma)", self.var_pemain, "opsional"),
                ("Sutradara (opsional)", self.var_sutradara, "opsional")):
            ttk.Label(f3, text=label, style="Panel.TLabel").pack(anchor="w", pady=(3, 0))
            ttk.Entry(f3, textvariable=var).pack(fill="x")
            if hint:
                ttk.Label(f3, text=hint, style="Dim.TLabel").pack(anchor="w")

        # ---------------- format & AI ----------------
        f4 = ttk.Labelframe(left, text=" 4. FORMAT & MESIN AI ", padding=8)
        f4.pack(fill="x", pady=(8, 0))
        row = ttk.Frame(f4)
        row.pack(fill="x")
        ttk.Label(row, text="Rasio:", style="Panel.TLabel").pack(side="left")
        self.cmb_rasio = ttk.Combobox(row, textvariable=self.var_rasio, state="readonly",
                                      values=list(ai.RASIOS), width=20)
        self.cmb_rasio.pack(side="left", padx=6)
        ttk.Label(row, text="Kualitas:", style="Panel.TLabel").pack(side="left")
        ttk.Combobox(row, textvariable=self.var_kualitas, state="readonly",
                     values=list(ai.QUALITY_PRESETS.keys()), width=18).pack(side="left")
        rowv = ttk.Frame(f4)
        rowv.pack(fill="x", pady=(5, 0))
        ttk.Button(rowv, text="🎲 Variasi Baru (acak AI)",
                   command=self.buat_poster).pack(side="left", fill="x", expand=True)
        ttk.Button(rowv, text="🤖 Status Model AI…", command=self.dialog_model).pack(
            side="left", padx=(6, 0))
        ttk.Label(f4, textvariable=self.var_model, style="Dim.TLabel",
                  wraplength=350, justify="left").pack(anchor="w", pady=(5, 0))

        ttk.Button(left, text="🎬  BUAT POSTER DENGAN AI!", style="Big.TButton",
                   command=self.buat_poster).pack(fill="x", pady=(12, 4))
        ttk.Button(left, text="💾  Simpan Poster Resolusi Tinggi…",
                   style="Gold.TButton", command=self.simpan).pack(fill="x")

        f5 = ttk.Labelframe(left, text=" MODE BATCH ", padding=8)
        f5.pack(fill="x", pady=(10, 0))
        ttk.Label(f5, text="Satu folder video/foto → poster AI untuk SEMUA file, "
                           "memakai prompt yang sama di atas.",
                  style="Dim.TLabel", wraplength=350, justify="left").pack(anchor="w")
        rowb = ttk.Frame(f5)
        rowb.pack(fill="x", pady=(6, 0))
        ttk.Label(rowb, text="Rasio:", style="Panel.TLabel").pack(side="left")
        ttk.Combobox(rowb, textvariable=self.var_batch_rasio, state="readonly",
                     values=list(ai.RASIOS), width=20).pack(side="left", padx=6)
        ttk.Button(f5, text="📦  Batch: Pilih Folder & Buat Semua…",
                   style="Gold.TButton", command=self.batch_folder).pack(fill="x", pady=(6, 2))

        # ---------------- kolom kanan: preview ----------------
        right = ttk.Frame(root)
        right.pack(side="left", fill="both", expand=True, padx=(6, 10), pady=10)
        self.canvas = tk.Canvas(right, bg="#0c0c14", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self._place_preview())

        ttk.Label(self, textvariable=self.var_status, style="Dim.TLabel",
                  padding=(12, 4)).pack(fill="x", side="bottom")

    # ------------------------------------------------------- model AI
    def _refresh_model_status(self):
        ok, got, total, d = ai.model_status()
        if ok:
            self.var_model.set("Model AI: SIAP ✓ (offline). Folder: " + d)
        else:
            pct = got * 100 // max(1, total)
            self.var_model.set("Model AI: belum terunduh (%d%%). "
                               "Klik 🤖 untuk mengunduh sekali (~2,5 GB, "
                               "setelah itu tanpa internet)." % pct)

    def toggle_prompt_semua(self):
        v = not self.var_prompt_semua.get()
        self.var_prompt_semua.set(v)
        self.btn_prompt_semua.config(
            text=("✓ Terapkan ke Semua Video" if v else "✗ Hanya video ini"))
        self.var_status.set("Prompt ini AKAN DIPAKAI untuk semua video yang "
                            "diproses batch." if v else "Prompt ini hanya untuk "
                            "video/foto yang aktif sekarang.")

    def pakai_prompt_default(self):
        self.txt_prompt.delete("1.0", "end")
        self.txt_prompt.insert("1.0", ai.DEFAULT_PROMPT)
        self.var_status.set("Prompt kembali ke bawaan: gaya modern sinematik Hollywood.")

    def dialog_model(self):
        ok, got, total, d = ai.model_status()
        win = tk.Toplevel(self)
        win.title("Model AI (Stable Diffusion Turbo — offline)")
        win.geometry("640x420")
        win.configure(bg=BG)
        ttk.Label(win, text="Mesin AI lokal (Stable Diffusion Turbo)",
                  style="Gold.TLabel", font=("Segoe UI", 12, "bold")).pack(pady=(14, 4))
        ttk.Label(win, text="Model menggambar ulang frame video menjadi key art "
                            "poster sesuai prompt. Diunduh SEKALI saja, setelah "
                            "itu aplikasi 100% offline.", style="TLabel",
                  wraplength=580, justify="left").pack(padx=24)
        ttk.Label(win, text="Folder model:\n" + d, style="Dim.TLabel",
                  wraplength=580, justify="left").pack(padx=24, pady=(6, 10))
        bar = ttk.Progressbar(win, maximum=100, length=560)
        bar.pack(padx=24, fill="x")
        lbl = ttk.Label(win, text="", style="TLabel")
        lbl.pack(padx=24, pady=6)

        if ok:
            bar["value"] = 100
            lbl.config(text="✓ Model lengkap dan siap dipakai (100%).",
                       style="Green.TLabel")
        else:
            pct = got * 100 // max(1, total)
            bar["value"] = pct
            lbl.config(text="Terunduh %d%% — klik tombol untuk lanjut." % pct)

        q = queue.Queue()

        def poll():
            try:
                while True:
                    fase, done, tot = q.get_nowait()
                    bar["maximum"] = 100
                    bar["value"] = done * 100 // max(1, tot)
                    lbl.config(text="Mengunduh %s: %.0f%% dari total model…"
                               % (fase, done * 100 / max(1, tot)))
            except queue.Empty:
                pass
            if state["running"]:
                win.after(150, poll)

        def finish(ok_download):
            state["running"] = False
            self._refresh_model_status()
            if ok_download:
                lbl.config(text="✓ Model lengkap! Aplikasi kini 100% offline.",
                           style="Green.TLabel")
            elif not state["cancel"]:
                lbl.config(text="Gagal mengunduh. Cek koneksi & coba lagi "
                                "(unduhan bisa dilanjutkan, tidak mulai dari 0).")

        state = {"running": False, "cancel": False}

        def start_download():
            btn_dl.config(state="disabled", text="Mengunduh…")
            state["running"] = True

            def work():
                try:
                    done_ok = ai.download_model(
                        progress=lambda f, a, b: q.put((f, a, b)),
                        cancel=lambda: state["cancel"])
                except Exception as exc:                       # noqa: BLE001
                    win.after(0, lambda: lbl.config(text="Gagal: %s" % exc))
                    win.after(0, lambda: finish(False))
                    return
                win.after(0, lambda: finish(done_ok))

            threading.Thread(target=work, daemon=True).start()
            poll()

        rowd = ttk.Frame(win)
        rowd.pack(pady=10)
        btn_dl = ttk.Button(rowd, text="⬇  Unduh / Lanjutkan Model AI",
                            style="Gold.TButton", command=start_download)
        if ok:
            btn_dl.config(state="disabled")
        btn_dl.pack(side="left", padx=4)
        ttk.Button(rowd, text="Tutup", command=win.destroy).pack(side="left", padx=4)

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
                img, _, info = fp.extract_best_frame(path)
            except Exception as exc:                       # noqa: BLE001
                self.after(0, lambda: messagebox.showerror("Gagal", str(exc)))
                self.after(0, lambda: self.var_status.set("Gagal membaca video."))
                return
            self.after(0, lambda: self._source_ready(img, info, from_video=True))
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
        self._source_ready(img, {"jumlah_sampel": 1}, from_video=False)

    def _source_ready(self, img, info, from_video):
        self.source_img = img
        self.source_info = info
        if from_video:
            judul = fp.title_from_filename(self.source_path)
            self.var_judul.set(judul)
            det = info.get("waktu_detik", 0)
            self.var_status.set(
                f"Frame terbaik: detik {det} (skor {info.get('skor', '-')}). "
                f"Judul otomatis: “{judul}”. Klik BUAT POSTER DENGAN AI!")
        else:
            self.var_status.set("Foto dimuat. Ketik judul, lalu klik BUAT POSTER!")

    def _prompt_text(self):
        return self.txt_prompt.get("1.0", "end").strip()

    # ------------------------------------------------------------ render
    def buat_poster(self):
        if not self.source_img:
            messagebox.showinfo("Belum ada sumber", "Pilih VIDEO atau FOTO dulu ya, kawan!")
            return
        ok, got, total, _ = ai.model_status()
        if not ok:
            messagebox.showinfo(
                "Model AI belum ada",
                "Mesin AI perlu diunduh sekali saja (~2,5 GB).\n"
                "Klik tombol 🤖 Status Model AI untuk mengunduh.\n"
                "Setelah itu aplikasi tidak butuh internet lagi.")
            self.dialog_model()
            return
        self._render_async()

    def _render_async(self):
        if not self.source_img or self._busy:
            return
        self._busy = True
        self.var_status.set("AI sedang menggambar poster… (1-2 menit, tergantung PC)")
        img_src = self.source_img.copy()
        rasio_label = self.var_rasio.get()
        rasio_key = ai.rasio_label_to_key(rasio_label)
        video_ratio = img_src.size[0] / max(1, img_src.size[1])
        size = ai.ai_canvas(rasio_key, video_ratio)
        quality = self.var_kualitas.get()
        prompt = self._prompt_text() or ai.DEFAULT_PROMPT
        judul, tagline, pemain, sutradara = (self.var_judul.get(), self.var_tagline.get(),
                                             self.var_pemain.get(), self.var_sutradara.get())
        full = ai.poster_full_size(rasio_key, video_ratio)
        preview = eng.preview_size(full)

        def prog(fase, info):
            self.after(0, lambda: self.var_status.set(info))

        def work():
            try:
                art = self.poster_ai.generate(img_src, prompt, size,
                                              quality_key=quality, progress=prog)
                poster = eng.compose_poster(art, judul, size=full, tagline=tagline,
                                            pemain=pemain, sutradara=sutradara)
            except Exception as exc:                       # noqa: BLE001
                self.after(0, lambda: self._render_done())
                self.after(0, lambda: messagebox.showerror(
                    "Gagal membuat poster",
                    "%s: %s\n\nKalau ini terus terjadi, buka log_kesalahan.txt "
                    "di samping aplikasi (atau kirim isinya)." % (
                        exc.__class__.__name__, exc)))
                self.after(0, lambda: self.var_status.set(f"Gagal render: {exc}"))
                return
            self.after(0, lambda: self._show_preview(poster, preview))
        threading.Thread(target=work, daemon=True).start()

    def _render_done(self):
        self._busy = False

    def _show_preview(self, poster, preview_size):
        self._busy = False
        self._poster_preview = poster
        scaled = poster.resize(preview_size, eng.RESAMPLE)
        self._tk_preview = ImageTk.PhotoImage(scaled)
        self._place_preview()
        self.var_status.set(
            f"Poster AI siap! {self.var_rasio.get()} · "
            f"{poster.size[0]}×{poster.size[1]} px. Klik Simpan untuk file resolusi "
            "tinggi, atau 🎲 Variasi Baru untuk hasil AI lain.")

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
        img_src = self.source_img.copy()
        rasio_key = ai.rasio_label_to_key(self.var_rasio.get())
        video_ratio = img_src.size[0] / max(1, img_src.size[1])
        size = ai.ai_canvas(rasio_key, video_ratio)
        full = ai.poster_full_size(rasio_key, video_ratio)
        quality = self.var_kualitas.get()
        prompt = self._prompt_text() or ai.DEFAULT_PROMPT
        judul_v, tagline, pemain, sutradara = (self.var_judul.get(), self.var_tagline.get(),
                                               self.var_pemain.get(), self.var_sutradara.get())

        def work():
            try:
                art = self.poster_ai.generate(img_src, prompt, size,
                                              quality_key=quality)
                poster = eng.compose_poster(art, judul_v, size=full, tagline=tagline,
                                            pemain=pemain, sutradara=sutradara)
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
        ok, got, total, _ = ai.model_status()
        if not ok:
            messagebox.showinfo(
                "Model AI belum ada",
                "Mesin AI perlu diunduh sekali saja (~2,5 GB) sebelum batch bisa jalan.")
            self.dialog_model()
            return
        prompt = self._prompt_text() or ai.DEFAULT_PROMPT
        rasio_key = ai.rasio_label_to_key(self.var_batch_rasio.get())
        self._open_batch_dialog(folder, len(files), rasio_key, prompt)

    def _open_batch_dialog(self, folder, n, rasio_key, prompt):
        q = queue.Queue()
        win = tk.Toplevel(self)
        win.title(f"Mode Batch AI — {n} file")
        win.geometry("660x460")
        win.configure(bg=BG)

        head = ttk.Frame(win, padding=(12, 10))
        head.pack(fill="x")
        prompt_pendek = (prompt[:70] + "…") if len(prompt) > 70 else prompt
        ttk.Label(head, text=f"{n} file → poster AI ({rasio_key})", style="Gold.TLabel").pack(anchor="w")
        ttk.Label(head, text=f"Prompt untuk semua: {prompt_pendek}", style="Dim.TLabel",
                  wraplength=600, justify="left").pack(anchor="w")
        bar = ttk.Progressbar(win, maximum=n, length=580)
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
            lbl_file.config(text=f"Selesai: {res.get('ok', 0)} poster AI berhasil, "
                                 f"{res.get('gagal', 0)} gagal"
                                 + (" (dibatalkan)" if res.get("dibatalkan") else ""))
            btn_cancel.config(state="disabled", text="Tutup")
            out = res.get("out_dir", folder)
            if messagebox.askyesno("Batch selesai",
                                   f"Poster AI: {res.get('ok', 0)} berhasil, "
                                   f"{res.get('gagal', 0)} gagal.\nFolder hasil:\n{out}\n\n"
                                   "Buka folder hasil?"):
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
                res = bp.run_batch(folder, None, rasio_key, prompt,
                                   kualitas=self.var_kualitas.get(),
                                   log=log, progress=prog,
                                   should_continue=lambda: not cancel["v"])
            except Exception as exc:                # noqa: BLE001
                q.put(("log", f"GAGAL: {exc}"))
                res = {"ok": 0, "gagal": 1, "dibatalkan": False, "out_dir": folder}
            q.put(("done", res))

        threading.Thread(target=work, daemon=True).start()
        poll()


def main():
    # Semua jenis crash ditangkap dan dicatat ke log_kesalahan.txt di samping
    # aplikasi: error Python (sys.excepthook), error di thread
    # (threading.excepthook), error callback UI (report_callback_exception),
    # dan crash native level sistem (faulthandler — mis. DLL rusak atau CPU
    # tanpa instruksi AVX2).
    logp = _log_path()
    logf = open(logp, "a", encoding="utf-8", errors="replace")
    logf.write("\n=== PosterBioskopAI dimulai %s | python %s | EXE=%s | cpu=%d ===\n" % (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "%d.%d.%d" % sys.version_info[:3],
        bool(getattr(sys, "frozen", False)),
        os.cpu_count() or 0))
    logf.flush()
    faulthandler.enable(logf, all_threads=True)
    sys.excepthook = lambda t, v, tb: catat_kesalahan(logf, t, v, tb)
    threading.excepthook = lambda a: catat_kesalahan(
        logf, a.exc_type, a.exc_value, a.exc_traceback)

    app = PosterApp(log=logf)
    try:
        app.mainloop()
    finally:
        logf.close()


if __name__ == "__main__":
    main()
