# README — PosterBioskopAI

Aplikasi desktop Windows pembuat poster film ala Hollywood dari video/foto
kamu — kini dengan **mesin AI generatif sungguhan yang berjalan 100% offline**.

## Yang baru di v2.0.4 (perbaikan InvalidArgument saat AI menggambar)

* Setiap feed model AI kini dikonversi otomatis ke tipe yang diDEKLARASIKAN
  sesi ONNX (float/fp16/int64/int32) — menutup selisih deklarasi model.
* Bila kernel onnxruntime di CPU tertentu tetap menuntut tipe lain (kasus
  nyata: timestep int64 ditolak, minta float), pesan galat diparse otomatis
  dan percobaan kedua dijalankan dengan tipe yang diminta.
* Sesi yang tetap gagal melaporkan nama sesi + tipe semua feed ke log.
* CI kini mencatat deklarasi input tiap sesi ONNX sebagai referensi.

## Yang baru di v2.0.3 (perbaikan tampilan pesan galat)

* Memperbaiki NameError saat menampilkan jendela pesan galat (bug closure:
  variabel target `except ... as exc` dihapus Python saat blok berakhir).
* Galat ASLI penyebab render gagal kini selalu terekam utuh di
  `log_kesalahan.txt` sejak thread kerja — bukan hanya tampil di jendela.

## Yang baru di v2.0.2 (perbaikan akar masalah crash)

* Aplikasi dibangun mode **ONEDIR** (folder aplikasi berisi EXE + _internal)
  menggantikan onefile — menghilangkan konflik pemuatan DLL penyebab
  "access violation" saat memuat mesin AI di sebagian PC Windows.
* Runtime C++ terbaru (msvcp140/vcruntime140/vcruntime140_1) **dijamin ikut**
  di folder aplikasi; DLL mesin AI dimuat eksplisit sebelum dipakai.
* Mesin AI diperiksa di thread utama saat aplikasi dibuka — masalah terlihat
  dengan pesan jelas, bukan mati diam-diam saat klik.
* Build kini otomatis menguji pemuatan mesin AI di Windows asli (OrtProbe)
  sebelum dirilis; paket VC++ Redistributable tersedia di halaman Release.

## Yang baru di v2.0.1 (perbaikan stabilitas)

Aplikasi tidak lagi mati diam-diam: SEMUA kesalahan — Python maupun crash level
sistem (DLL/CPU) — kini dicatat ke `log_kesalahan.txt` di samping aplikasi dan
ditampilkan sebagai jendela pesan. Bundel EXE juga dipastikan membawa mesin AI
(onnxruntime) secara lengkap, dan versi pustaka dipin ke kombinasi yang teruji.

## Yang baru di v2.0 (rombak total)

Perpustakaan 999 referensi gaya lama **dihapus seluruhnya**. Digantikan mesin
AI generatif **Stable Diffusion Turbo** (format ONNX, CPU): frame terbaik dari
video di-"gambar ulang" AI menjadi key art poster sinematik sesuai prompt.

* **Prompt bawaan otomatis terisi**:
  "Rubahlah gambar ini menjadi poster untuk sebuah film Hollywood dengan
  menggunakan judul video sebagai judul di poster, buat poster dengan gaya
  modern sinematik"
* **Prompt manual**: kotak prompt boleh diedit bebas (kata kunci Indonesia
  otomatis diterjemahkan ke kata kunci gaya yang dipahami AI).
* **Tombol "Terapkan ke Semua Video"**: satu prompt dipakai untuk semua file
  yang diproses mode batch.
* **Rasio poster**: Ikuti rasio video, 9:16 (Story/Reels), 16:9 (Layar).
* **Tulisannya rapi**: judul auto-fit 1-3 baris dan dijamin tidak melewati
  batas kiri/kanan gambar (margin aman ~5%), lengkap dengan scrim gelap,
  tagline, garis emas, dan strip rilis gaya poster bioskop modern.
* **4 tingkat kualitas AI**: Cepat (1 langkah) → Maksimal (4 langkah).
* **Variasi**: tombol 🎲 mengacak seed — frame sama, hasil AI berbeda.

## Struktur folder

| File | Fungsi |
| --- | --- |
| `poster_app.py` | GUI utama (Tkinter) |
| `poster_ai.py` | Mesin AI: SD-Turbo img2img + unduh model + penerjemah prompt |
| `poster_engine.py` | Tipografi & finishing poster (margin aman) |
| `frame_picker.py` | Pemilih frame terbaik dari video + judul dari nama file |
| `batch_poster.py` | Mode batch (GUI & CLI) |
| `assets/fonts/` | Font Anton & Bebas Neue (lisensi OFL) |
| `models/sd-turbo-onnx/` | Model AI (~2,7 GB) — diunduh/pasang sekali |

## Pasang model AI (sekali saja, ~2,7 GB)

**Cara 1 — dari dalam aplikasi (paling mudah):** buka aplikasi → tombol
"🤖 Status Model AI…" → "⬇ Unduh / Lanjutkan Model AI". Unduhan bisa
dilanjutkan kalau terputus.

**Cara 2 — manual dari halaman Release:** ekstrak dulu
`PosterBioskopAI-Windows.zip` jadi folder aplikasi; download
`PosterBioskopAI-Model-AI.zip.part00` dan `.part01`, taruh DI DALAM folder
aplikasi itu (di samping `PosterBioskopAI.exe`), lalu double-click
`GABUNG-MODEL.bat`.

Setelah terpasang, aplikasi tidak butuh internet lagi.

## Cara pakai

1. **Pilih VIDEO** — judul poster otomatis dari nama file, frame terbaik
   dipilih otomatis (ketajaman × exposure × kontras). Atau pilih FOTO.
2. Atur **prompt** (default sudah terisi) dan **rasio** (9:16 / 16:9 / ikuti
   video), pilih kualitas AI.
3. **BUAT POSTER DENGAN AI!** — 10-90 detik tergantung CPU. Preview muncul;
   coba 🎲 Variasi Baru kalau mau hasil lain.
4. **Simpan** resolusi tinggi (PNG/JPG), atau pakai **Mode Batch** untuk satu
   folder video sekaligus (prompt yang sama untuk semua).

CLI batch:
```
python batch_poster.py <folder> --rasio "9:16" --kualitas "Normal (2 langkah)"
python batch_poster.py <folder> --prompt "poster malam kabut neon biru"
```

## Spek & catatan

* Windows 10/11 (atau Linux/macOS dengan Python), RAM 8 GB disarankan,
  ruang disk ~4 GB (EXE + model).
* Generasi AI di CPU: ±10-30 detik per langkah pada PC modern.
* Model AI memakai bobot Stable Diffusion Turbo (Stability AI,
  Non-Commercial Community License) — dipakai untuk keperluan pribadi/non-
  komersial. Kode aplikasi: MIT (lihat LICENSE).
* Build EXE sendiri: double-click `build_windows.bat`, atau biarkan GitHub
  Actions yang membangun (workflow `Build EXE + Model AI` berjalan otomatis
  saat push tag `v*`, hasil EXE + model langsung ditempel ke Release).

## Kalau ada masalah

* **Aplikasi menutup sendiri / poster gagal dibuat** — buka `log_kesalahan.txt`
  di samping aplikasi: setiap penyebab kesalahan terekam di situ (sejak
  v2.0.1). Kirim isinya kalau butuh bantuan.
* **Pesan tentang mesin AI / runtime C++** — jalankan `vc_redist.x64.exe`
  dari halaman Release (pembaruan runtime resmi Microsoft), lalu buka aplikasi
  lagi. Sejak v2.0.2 runtime C++ terbaru juga sudah ikut di folder aplikasi.
* **Model AI belum lengkap** — tombol "🤖 Status Model AI" untuk mengunduh
  atau melanjutkan unduhan yang terputus.
* **PC terasa lambat** — pilih kualitas "Cepat (1 langkah)" di menu Kualitas.
