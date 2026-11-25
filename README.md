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
2. **AI merawat / menggambar key art** — mesin **Stable Diffusion Turbo** (ONNX, CPU,
   offline). Bawaannya **foto asli tetap nyata**: preset "Foto asli + sentuhan AI"
   hanya mepoles frame (wajah, tekstur, dan warna asli tetap terbaca), bukan
   mengubahnya jadi kartun. Mau gaya bebas? Pilih preset Cepat–Maksimal. Kata kunci
   Indonesia otomatis diterjemahkan; satu prompt bisa diterapkan ke SEMUA video 
   dalam mode batch.
3. **Tipografi & komposisi** — judul, tagline, garis emas, dan strip rilis
   dipasang dengan font Anton/Bebas Neue yang ikut dalam aplikasi, dengan
   **margin aman: teks dijamin tidak melewati batas kiri/kanan**. Rasio:
   **9:16 (Story/Reels/TikTok)** · **16:9 (Layar)** · atau ikuti rasio video.

## Memilih template — 131 desain bawaan

Di panel **Template** ada empat cara; semua instan dan tanpa perlu paham desain:

1. **🎨 Galeri visual (paling mudah)** — klik tombol 🎨 di samping dropdown:
   seluruh 131 template tampil sebagai pratinjau poster kecil, **klik satu
   gambar** dan langsung terpasang di aplikasi.
2. **Dropdown** — pilih langsung; pola nama berkas = `keluarga-palet-nomor`
   (mis. `festival-senja-039` = keluarga *Festival*, palet *Senja*).
3. **Pratinjau di aplikasi (v2.3.0)** — dropdown Template kini menampilkan KOTAK PRATINJAU kecil di bawahnya; pilih nama → pratinjau langsung berubah, jadi kelihatan bentuknya sebelum dipakai.
4. **Katalog gambar** — buka `templates\_katalog-template.jpg` untuk melihat
   semua desain sekaligus, bahkan tanpa menjalankan aplikasi.
5. **PNG/JPG milikmu** — taruh di folder `templates\` (tombol 📁 membukanya
   lalu klik 📁 sekali lagi untuk menyegarkan); PNG transparan disusun di atas
   key art, JPEG dipakai sebagai latar. **Tanpa template** = komposisi bawaan
   mesin tipografi.

Keluarga layout: Klasik · Judul Atas · Letterbox · Panel Samping · Festival ·
Komedi · Minimalis · Gradien Penuh · Duotone · Bingkai · Badge · Kolom Tiga ·
Vignette · Sisi Gelap · Skrim Puncak. Palet: Emas · Crimson · Orka · Ungu ·
Biru · Senja · Rimba · Mono · Pop · Perak. Tips cepat: drama/kisah nyata →
*Festival* atau *Klasik*; aksi/horor → *Sisi Gelap*, *Duotone*, *Skrim
Puncak*; komedi/seru → *Komedi* + palet *Pop*; dokumenter bersih →
*Minimalis* atau *Letterbox*.

## Foto asli (bukan kartun) & judul selalu utuh — v2.2.0

**Kenapa dulu terasa kartun?** Semua preset lama menjalankan AI pada strength
1.0 = gambar ulang penuh, sehingga foto asli "hilang" jadi gaya CGI. Sekarang
dropdown **Kualitas** punya dua preset baru:

* **Foto asli + sentuhan AI (paling setia)** — bawaan. AI hanya bekerja dari
  noise kecil (2 langkah dari sigma 0,93): komposisi, wajah, dan tekstur foto
  asli tetap ada; hasilnya terasa seperti foto yang dipercantik, bukan kartun.
* **Fotorealistik sinematik (seimbang)** — sentuhan AI lebih kuat (4 langkah
  dari sigma 2,28) tetap fotorealistik.
* Preset lama (Cepat/Normal/Tinggi/Maksimal) tetap tersedia untuk gaya bebas
  ala poster Hollywood (boleh terasa CGI/ilustratif).

Selain itu semua gaya kini **melarang AI menggambar huruf palsu** (tulisan
ngawur seperti "ERANEAY" di key art) — judul selalu ditulis mesin tipografi.

**Judul tidak pernah dipotong lagi.** Judul dari nama video/foto ditampilkan
UTUH sepanjang apa pun: bila panjang, font otomatis mengecil dan baris
bertambah (4 baris normal; judul ekstrem → font lebih kecil lagi), sehingga
semua kata tampil lengkap tanpa tanda "…".

## Strip bisa diganti/dihapus + gaya judul bervariasi — v2.3.0

**Teks "SEGERA DI BIOSKOP"** kini ada kolomnya di aplikasi (bagian 3, "Teks di
bawah judul"): isi teks apa pun (mis. "TAYANG 25 DESEMBER") atau **kosongkan
untuk menghapus** strip itu. Mode batch: `--rilis ""`.

**Gaya judul** — dropdown baru di aplikasi (dan `--gaya-judul` di batch):

* **Otomatis (menyesuaikan judul)** — bawaan: judul pendek jadi blok besar,
  sedang mendapat kata akhir miring berwarna aksen, panjang memakai kontras
  besar-kecil (kata penting besar, kata sambung "di/yang/dan" kecil).
* **Klasik (seragam besar)** — gaya lama, satu ukuran.
* **Menonjol (kata penting besar)** / **Miring (kata akhir aksen)** — pilih
  manual sesuai selera.

Semua gaya menyejajarkan garis dasar huruf besar-kecil dan tetap **tidak
pernah memotong teks**: judul sepanjang apa pun tampil utuh.

## Instalasi (Windows)

1. Buka [Releases](https://github.com/zacrie85/PosterBioskopAI/releases) → dari
   rilis terbaru unduh: **PosterBioskopAI-Windows.zip**,
   `PosterBioskopAI-Model-AI.zip.part00` + `...part01`, dan `GABUNG-MODEL.bat`.
2. **Ekstrak ZIP** → muncul folder `PosterBioskopAI`. Taruh kedua bagian model
   dan `GABUNG-MODEL.bat` **di dalam folder itu** (di samping
   `PosterBioskopAI.exe`).
3. Double-click **`GABUNG-MODEL.bat`** → model AI (±2,5 GB) terpasang otomatis.
4. Double-click **`PosterBioskopAI.exe`** → selesai; selanjutnya 100% offline.

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
  python batch_poster.py folder --template festival-senja-039
  ```

## Struktur proyek

| File | Isi |
| --- | --- |
| `poster_app.py` | GUI aplikasi (Tkinter) + penangkap crash & log |
| `batch_poster.py` | Mode batch: folder → banyak poster AI (juga CLI) |
| `poster_ai.py` | Mesin AI generatif: SD-Turbo ONNX (pipeline, unduh model, penerjemah prompt) |
| `poster_engine.py` | Tipografi & komposisi poster (margin aman) |
| `frame_picker.py` | Ekstraksi frame terbaik + judul dari nama video |
| `template_engine.py` | Pasang template layout/palet di atas key art |
| `template_gallery.py` | Galeri 🎨 pemilih template + pembuat katalog |
| `templates/` | 131 template bawaan (PNG+JSON) + katalog & cache pratinjau |
| `build_windows.bat` | Build EXE (PyInstaller) |
| `.github/workflows/` | Build EXE otomatis di runner Windows GitHub |
| `contoh/` | Video uji |

## Pencarian masalah

* **Aplikasi menutup sendiri** — sejak v2.0.1 setiap kesalahan (termasuk crash
  level sistem seperti DLL yang hilang atau CPU lama tanpa AVX2) dicatat ke
  **`log_kesalahan.txt`** di samping aplikasi/EXE. Buka file itu untuk melihat
  penyebabnya; kirim isinya kalau butuh bantuan.
* **Pesan tentang mesin AI / runtime C++** — jalankan **`vc_redist.x64.exe`**
  dari halaman Release (pembaruan runtime resmi Microsoft), lalu buka aplikasi
  lagi. Sejak v2.0.2 runtime C++ terbaru juga sudah ikut di folder aplikasi.
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
