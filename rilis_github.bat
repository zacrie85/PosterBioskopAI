@echo off
rem ============================================================
rem  RILIS PosterBioskopAI ke GitHub (aman: token TIDAK disimpan)
rem  Cara pakai:
rem    1. Buat repo kosong di github.com (New repository),
rem       JANGAN centang README/License (biar kosong).
rem    2. Double-click file ini.
rem    3. Tempel URL repo saat diminta, contoh:
rem          https://github.com/USERNAME/PosterBioskopAI.git
rem    4. Saat git push menanyakan Username & Password:
rem          Username = username GitHub kamu
rem          Password = PASTE token GitHub (ghp_...)  <- input tersembunyi
rem       Token tidak ditulis ke file mana pun.
rem ============================================================
cd /d "%~dp0"

where git >nul 2>nul
if errorlevel 1 (
    echo [!] Git belum ter-install. Download gratis di: https://git-scm.com/download/win
    pause
    exit /b 1
)

set /p REPO=Tempel URL repo GitHub kamu: 
if "%REPO%"=="" (
    echo [!] URL kosong, dibatalkan.
    pause
    exit /b 1
)

echo.
echo [1/5] Menyiapkan repository lokal...
if not exist .git git init
git add .
git commit -m "PosterBioskopAI: aplikasi pembuat poster film ala Hollywood (offline, 999 referensi gaya)" 2>nul
git branch -M main

echo [2/5] Menghubungkan ke repo kamu...
git remote remove origin 2>nul
git remote add origin "%REPO%"

echo [3/5] Mendorong kode ke GitHub...
echo ------------------------------------------------------------
echo Kalau diminta login: Username = username GitHub kamu,
echo                      Password = token GitHub (ghp_...)
echo Input password tersembunyi ^& tidak disimpan di file.
echo ------------------------------------------------------------
git push -u origin main

echo [4/5] Selesai! Cek halaman repo kamu di browser.
echo [5/5] Pesan keamanan: setelah rilis, hapus/revoke token yang
echo        pernah kamu buat, lalu buat token baru kalau perlu.
pause
