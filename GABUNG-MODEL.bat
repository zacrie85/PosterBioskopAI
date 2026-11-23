@echo off
rem ============================================================
rem  GABUNG-MODEL.bat — pasang model AI PosterBioskopAI v2.0
rem  Cara pakai:
rem   1. Download KEDUA file dari halaman Release:
rem        PosterBioskopAI-Model-AI.zip.part00
rem        PosterBioskopAI-Model-AI.zip.part01
rem   2. Taruh kedua file (dan file bat ini) DI FOLDER YANG SAMA
rem      dengan PosterBioskopAI.exe.
rem   3. Double-click file ini. Selesai -> aplikasi 100% offline.
rem ============================================================
cd /d "%~dp0"

if not exist "PosterBioskopAI-Model-AI.zip.part00" (
    echo [!] File "PosterBioskopAI-Model-AI.zip.part00" tidak ditemukan di folder ini.
    echo     Download dulu dari halaman Release, taruh di samping PosterBioskopAI.exe.
    pause
    exit /b 1
)
if not exist "PosterBioskopAI-Model-AI.zip.part01" (
    echo [!] File "PosterBioskopAI-Model-AI.zip.part01" tidak ditemukan di folder ini.
    pause
    exit /b 1
)

echo [1/3] Menggabungkan bagian model ^(butuh 1-2 menit^)...
copy /b /y "PosterBioskopAI-Model-AI.zip.part00"+"PosterBioskopAI-Model-AI.zip.part01" "PosterBioskopAI-Model-AI.zip" >nul
if errorlevel 1 (
    echo [!] Gagal menggabungkan.
    pause
    exit /b 1
)

echo [2/3] Mengekstrak model...
if exist models\sd-turbo-onnx rmdir /s /q models\sd-turbo-onnx
tar -xf "PosterBioskopAI-Model-AI.zip"
if errorlevel 1 (
    echo [!] Gagal mengekstrak. Coba jalankan ulang, atau ekstrak manual dengan 7-Zip.
    pause
    exit /b 1
)

echo [3/3] Membersihkan file sementara...
del /q "PosterBioskopAI-Model-AI.zip" >nul 2>nul

echo.
echo SELESAI! Model AI sudah terpasang di folder: models\sd-turbo-onnx
echo Buka PosterBioskopAI.exe — status Model AI harus "SIAP" dan tanpa internet.
echo.
pause
