=====================================================
 PosterBioskopAI — Pembuat Poster Film Ala Hollywood
        Aplikasi Desktop OFFLINE untuk Windows
=====================================================

APA INI?
--------
Aplikasi yang mengubah video atau foto jadi poster film ala
poster Hollywood (cover film): color grading sinematik, judul
besar auto-fit, tagline, nama pemain, billing block, dan strip
"SEGERA DI BIOSKOP".

Fitur kunci:
 1. Pilih VIDEO -> judul poster OTOMATIS diambil dari NAMA
    VIDEO (contoh: "VID_20240102_lomba_fisika.mp4" menjadi
    judul "Lomba Fisika"). Bisa diedit manual kapan saja.
 2. Frame terbaik dipilih OTOMATIS dari video (dinilai dari
    ketajaman gambar, pencahayaan, dan kontras).
 3. Gaya poster dipilih OTOMATIS dari 999 referensi gaya
    poster Hollywood yang dibundel di aplikasi (paduan genre,
    era, palet warna, tipografi, dan komposisi). Ada juga
    galeri manual + pencarian + filter genre/era.
 4. Rasio: Poster 2:3, Potret 3:4, Kotak 1:1, Wallpaper 16:9.
 5. Simpan PNG/JPG resolusi tinggi (mis. 1000x1500).
 6. MODE BATCH: pilih satu FOLDER berisi video/foto -> poster
    untuk SEMUA file sekaligus (tiap file di-analisis sendiri:
    frame terbaik, judul dari nama file, gaya auto-match).
    Hasil tersimpan di folder "<nama-folder>_poster" di sebelah
    folder sumber. Ada progress bar, log, dan tombol Batal.

CATATAN JUJUR SOAL "AI" & "999 REFERENSI"
-----------------------------------------
- Aplikasi ini 100% OFFLINE: tidak ada data yang dikirim ke
  internet, tidak perlu API key.
- "AI"-nya adalah mesin pencocok cerdas yang berjalan lokal:
  menganalisis kecerahan, kontras, saturasi, nuansa warna, dan
  area gelap foto/frame, lalu memilih gaya paling cocok dari
  999 referensi. Bukan AI generatif cloud, tapi hasilnya
  konsisten dan instan.
- 999 referensinya adalah GAYA yang di-generate (bukan gambar
  poster film asli, karena poster asli berhak cipta). Setiap
  referensi punya preview poster sendiri di galeri.

CARA PAKAI DI WINDOWS (pilih salah satu)
----------------------------------------
A. Jalankan langsung dengan Python (paling gampang):
   1. Install Python 3.9+ dari python.org (centang
      "Add Python to PATH" saat install).
   2. Double-click build_windows.bat TIDAK perlu kalau hanya
      mau jalan; cukup:
         pip install -r requirements.txt
         python poster_app.py

B. Jadikan EXE ter-install style (disarankan):
   1. Install Python 3.9+ (centang Add to PATH).
   2. Double-click  build_windows.bat
   3. Tunggu 2-5 menit. Hasilnya:
         dist\PosterBioskopAI.exe
   4. EXE ini bisa dicopy ke PC Windows lain TANPA install
      Python (satu file, standalone, offline).

C. TANPA install Python sama sekali:
   Unduh  PosterBioskopAI.exe  dari halaman Releases repo
   GitHub ini — EXE dibangun otomatis oleh GitHub Actions
   (runner Windows asli) setiap kali ada tag rilis baru.

MODE BATCH DARI TERMINAL (tanpa GUI)
------------------------------------
   python batch_poster.py "D:\video-kegiatan"
   python batch_poster.py folder --rasio "Wallpaper 16:9"
   python batch_poster.py folder --gaya REF-289 --out hasil

   Tanpa --gaya  : tiap file di-auto-match gayanya sendiri.
   Dengan --gaya : SATU referensi dipakai untuk semua file.
   Tanpa --out   : hasil ke folder "<folder>_poster" di sebelahnya.

FORMAT VIDEO YANG DIDUKUNG
--------------------------
MP4, MOV, MKV, AVI, WEBM, M4V, MPG, TS, WMV, 3GP
(diproses oleh OpenCV yang dibundel saat build EXE).

TIPS HASIL POSTER BAGUS
-----------------------
- Pakai video resolusi 720p ke atas; frame terbaik otomatis
  diambil dari bagian video yang paling tajam.
- Foto orang: rasio Poster 2:3 paling mirip poster bioskop.
- Judul pendek (1-3 kata) terlihat paling "Hollywood".
- Kalau hasil auto-match kurang sreg, buka Galeri dan pilih
  manual — ada 999 pilihan, dari Grindhouse 70-an sampai
  Teaser Modern.

STRUKTUR FILE
-------------
  poster_app.py      GUI aplikasi (Tkinter)
  batch_poster.py    mode batch: folder -> banyak poster (juga CLI)
  poster_engine.py   mesin render poster (grading, teks, efek)
  style_library.py   999 referensi gaya + auto-match
  frame_picker.py    pilih frame terbaik + judul dari nama video
  make_icon.py       membuat icon.ico
  requirements.txt   daftar dependensi
  build_windows.bat  skrip build EXE Windows
  rilis_github.bat   skrip upload proyek ke GitHub (aman)
  .github/workflows/ build EXE otomatis di runner Windows GitHub
  LICENSE            lisensi MIT
  .gitignore         file yang diabaikan git
  icon.ico           ikon aplikasi (dibuat oleh make_icon.py)

LISENSI & HAK CIPTA
-------------------
Kode boleh kamu pakai/modifikasi bebas untuk keperluan pribadi (MIT,
lihat LICENSE). Aplikasi memakai font bawaan Windows (Impact, Arial
Black, Georgia) atau fallback font bebas (DejaVu/Liberation) di sistem
lain. Poster yang dihasilkan memakai foto/video milikmu sendiri.

CARA RILIS KE GITHUB (2 menit)
------------------------------
1. Buat repo KOSONG di github.com (New repository, tanpa README).
2. Install Git dari git-scm.com (sekali saja).
3. Double-click  rilis_github.bat
4. Tempel URL repo, contoh: https://github.com/USERNAME/PosterBioskopAI.git
5. Saat git push meminta login:
      Username = username GitHub kamu
      Password = token GitHub baru (ghp_...) — input tersembunyi,
                 TIDAK disimpan di file mana pun.
6. Selesai — kode naik ke repo kamu.

KEAMANAN TOKEN
--------------
Jangan pernah menulis token di dalam kode, README, atau mengirimnya
lewat chat (sekali terkirim, anggap bocor: segera REVOKE di
github.com -> Settings -> Developer settings -> Personal access
tokens). Skrip rilis ini sengaja meminta token lewat prompt tersembunyi
git, bukan menyimpannya.

