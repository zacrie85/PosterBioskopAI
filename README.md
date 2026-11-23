# 🎬 PosterBioskopAI

**Ubah video/foto biasa jadi poster film ala Hollywood — dengan AI generatif yang berjalan 100% offline di PC-mu.**

Aplikasi desktop (Windows) untuk pembuat konten, pelajar, dan pemilik usaha
cetak banner yang ingin poster bergaya poster bioskop tanpa perlu belajar
desain — tanpa internet, tanpa API key.

## Cara kerja

1. **Pilih video atau foto** — aplikasi mengekstraksi *frame terbaik* otomatis
   (skor ketajaman + exposure + kontras) dan menebak **judul poster** dari
   nama file: `VID_20240102_petualangan_gunung_bromo.mp4` → judul
   **"Petualangan Gunung Bromo"** ✨
2. **AI menggambar key art** — mesin **Stable Diffusion Turbo** (ONNX, CPU,
   offline) menggambar ulang frame itu menjadi key art sesuai prompt: prompt
   bawaan sinematik Hollywood terisi otomatis, atau ketik prompt sendiri
   (kata kunci Indonesia otomatis diterjemahkan). Satu prompt bisa diterapkan
   ke SEMUA video dalam mode batch.
3. **Tipografi & komposisi** — judul, tagline, garis emas, dan strip rilis
   dipasang dengan font Anton/Bebas Neue yang ikut dalam aplikasi, dengan
   **margin aman: teks dijamin tidak melewati batas kiri/kanan**. Rasio:
   **9:16 (Story/Reels/TikTok)** · **16:9 (Layar)** · atau ikuti rasio video.

## Instalasi (Windows)

1. Buka [Releases](https://github.com/zacrie85/PosterBioskopAI/releases) → unduh
   **4 file** ke SATU folder: `PosterBioskopAI.exe`,
   `PosterBioskopAI-Model-AI.zip.part00`, `...part01`, dan `GABUNG-MODEL.bat`.
2. Double-click **`GABUNG-MODEL.bat`** → model AI (±2,5 GB) terpasang otomatis.
3. Double-click **`PosterBioskopAI.exe`** → selesai; selanjutnya 100% offline.

Pakai Python (Windows/Linux/macOS): install [Python 3.9+](https://www.python.org/downloads/)
(centang *Add to PATH*), lalu `pip install -r requirements.txt` dan
`python poster_app.py` — model diunduh sekali lewat tombol 🤖 di aplikasi.
Ingin build EXE sendiri? Jalankan `build_windows.bat`.

## Mode batch — satu folder, banyak poster

- **Dari aplikasi:** klik **📦 Batch: Pilih Folder & Buat Semua…** — tiap video
  dianalisis sendiri (frame terbaik + judul dari nama file), digambar AI dengan
  prompt yang sama, hasil di folder `<nama-folder>_poster`. Ada progress bar,
  log, dan tombol Batal.
- **Dari terminal (tanpa GUI):**
  ```
  python batch_poster.py "D:\video-kegiatan" --rasio "9:16" --kualitas "Cepat (1 langkah)"
  python batch_poster.py folder --prompt "poster malam kabut neon biru"
  ```

## Struktur proyek

| File | Isi |
| --- | --- |
| `poster_app.py` | GUI aplikasi (Tkinter) + penangkap crash & log |
| `batch_poster.py` | Mode batch: folder → banyak poster AI (juga CLI) |
| `poster_ai.py` | Mesin AI generatif: SD-Turbo ONNX (pipeline, unduh model, penerjemah prompt) |
| `poster_engine.py` | Tipografi & komposisi poster (margin aman) |
| `frame_picker.py` | Ekstraksi frame terbaik + judul dari nama video |
| `build_windows.bat` | Build EXE (PyInstaller) |
| `.github/workflows/` | Build EXE otomatis di runner Windows GitHub |
| `contoh/` | Video uji |

## Pencarian masalah

* **Aplikasi menutup sendiri** — sejak v2.0.1 setiap kesalahan (termasuk crash
  level sistem seperti DLL yang hilang atau CPU lama tanpa AVX2) dicatat ke
  **`log_kesalahan.txt`** di samping aplikasi/EXE. Buka file itu untuk melihat
  penyebabnya; kirim isinya kalau butuh bantuan.
* **Poster gagal dibuat** — penyebabnya muncul sebagai jendela pesan; detail
  teknis tetap terekam di `log_kesalahan.txt`.
* **Model AI belum lengkap** — klik 🤖 **Status Model AI** → Unduh. Unduhan
  yang terputus bisa dilanjutkan, tidak mulai dari 0.
* **PC terasa lambat** — pilih kualitas **"Cepat (1 langkah)"**.

## Spek & catatan

* Windows 10/11 64-bit (atau Linux/macOS dengan Python), RAM 8 GB disarankan,
  ruang disk ±4 GB (EXE + model).
* Generasi AI di CPU: ±10-30 detik per langkah pada PC modern.
* Model AI memakai bobot Stable Diffusion Turbo (Stability AI, Non-Commercial
  Community License) — untuk keperluan pribadi/non-komersial. Kode aplikasi:
  MIT (lihat LICENSE).

## Lisensi

MIT — bebas dipakai dan dimodifikasi. Poster dibuat dari foto/video milikmu sendiri.
