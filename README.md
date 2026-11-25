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

## Template kini 2: posisi judul saja (v2.6.0)

Template 131 desain lama dihapus — ternyata kebanyakan orang hanya butuh
**menentukan posisi judul**. Kini cukup 2 pilihan di dropdown Template:

- **judul-atas** — judul di sepertiga atas (bagus saat wajah/karakter ada
  di bagian bawah frame).
- **judul-bawah** — judul di bawah (gaya poster bioskop klasik).

Keduanya otomatis menggelapkan area judul (scrim) supaya tulisan selalu
terbaca. **PNG/JPG buatanmu tetap didukung**: taruh di folder `templates\`
lalu klik 📁 — PNG transparan disusun di atas key art, JPEG dipakai sebagai
latar. **Tanpa template** = penata memilih posisi & gaya sendiri.

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

## Panel kiri bisa digulir — v2.3.1

Pada layar pendek, seluruh panel kontrol kiri kini punya **scrollbar sendiri +
roda mouse**: kontrol apa pun yang terpotong (termasuk tombol **BUAT POSTER
DENGAN AI!** dan MODE BATCH) cukup digulir ke bawah. Pratinjau template juga
dipindah berdampingan dengan keterangan agar hemat ruang.

## Penata AI + Bingkai & Hiasan — v2.4.0

Panel baru **"5. BINGKAI & PENATA AI"** di aplikasi:

* **Penata AI** — membaca key art (palet dominan via k-means, kecerahan,
  saturasi, kehangatan, keramaian tepi, kecerahan zona judul), lalu memutuskan:
  warna aksen diambil DARI gambar sendiri, gaya judul sesuai mood
  (gelap->miring aksen, aksi->menonjol, ceria->klasik), dan **penjaga
  kontras**: latar judul terang/ramai -> scrim otomatis diperkuat supaya teks
  tidak tenggelam. Pilihan "Klasik (putih-emas)" mengembalikan perilaku lama.
* **Bingkai & hiasan (10 gaya)** — Garis klasik, Emas mewah (pita emas
  bergradasi + intan sudut), Film strip (lubang seluloid), Kertas sobek,
  Halftone, Neon glow, Art deco (kipi sudut), Vignet lembut, Splat aksen
  (percikan warna di sudut), Gradien warna (cuci warna diagonal).
  Otomatis memilih gaya dari mood gambar; semua bingkai memakai warna dari
  palet key art dan **margin teks menyesuaikan** agar judul tetap di dalam
  bingkai.
* **Tekstur AI pada bingkai** (opsional, lebih lambat) — 1 langkah img2img
  SD-Turbo di tepi poster agar bingkai menyatu dengan key art; bagian tengah
  (art + teks) dijaga tetap asli.

Mode batch: `--bingkai "Emas mewah"`, `--penata "Klasik (putih-emas)"`,
`--tekstur-bingkai`. Semua proses 100% offline, tanpa unduhan baru.

## Fitur Baru — v2.6.0

1. **🧹 Hapus subtitle otomatis** — frame video dengan subtitle yang menempel
   (hardsub) dibersihkan DULU sebelum AI menggambar, jadi tidak ada teks
   liar di belakang judul. Deteksi pola baris teks di pita bawah; kalau
   tidak yakin, frame dibiarkan utuh (anti-rusak). Nonaktif: hilangkan
   centang "Hapus subtitle otomatis" / CLI `--jaga-subtitel`.
2. **🧠 Objek pintar dari judul & prompt** — kata "kapal selam" di judul →
   objek kapal selam; "ular/naga" → ular; "kerajaan/raja" → mahkota; dst.
   Ini pilihan bawaan dropdown Objek AI; mood tetap jadi cadangan lewat
   pilihan "Otomatis (dari mood)". Objek baru: **Kapal, Kapal Selam, Ular**.
3. **🔍 Upscale 2× (4K)** — centang "Upscale 2× (4K)": poster 1080×1920
   menjadi 2160×3840 tajam (LANCZOS + unsharp). CLI: `--upscale-x2`.
4. **🎯 Varian A/B di pratinjau** — setelah AI selesai, 3 thumbnail varian
   muncul di bawah pratinjau; klik satu → pratinjau berganti dan **💾 Simpan
   mengikuti gaya varian yang dipilih**.

## 4 Fitur Baru — v2.5.0

1. **Mood neural (CLIP)** — deteksi mood oleh jaringan syaraf sungguhan
   (CLIP ViT-B/32 ONNX, ± 90 MB, opsional). Tower vision dijalankan di PC-mu;
   embedding teks 5 mood sudah dihitung & ikut aplikasi (± 4 KB) — jadi
   unduhannya kecil. Kalau model belum diunduh / hasilnya kurang yakin,
   analisis statistik penata yang dipakai. Unduh: tombol **🧠 Unduh model
   mood** di aplikasi, atau `batch_poster.py --unduh-mood`.
2. **🎲 Buat 3 Varian** — satu key art AI, tiga poster gaya berbeda langsung
   tersimpan di folder `hasil/` (Otomatis, Klasik-emas, Film strip). Mode
   batch: centang "3 varian per video" / `--varian 3`.
3. **Objek AI** — hiasan yang berhubungan dengan cerita (Pisau / Pedang /
   Mahkota / Cincin / Otomatis-dari-mood) di pojok kanan-atas. Siluet
   digambar prosedural, lalu **dilukis AI** (img2img SD-Turbo kualitas paling
   setia) agar bertekstur sinematik; tanpa model: siluet tetap rapi.
4. **🖼 Ekspor Bingkai PNG** — bingkai aktif jadi PNG **transparan** untuk
   dipakai ulang di Canva/Photoshop/dll.

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
  python batch_poster.py folder --template judul-bawah
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
| `template_gallery.py` | Galeri 🎨 pratinjau template |
| `templates/` | 2 template posisi judul (judul-atas/bawah) + folder PNG/JPG milikmu |
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
