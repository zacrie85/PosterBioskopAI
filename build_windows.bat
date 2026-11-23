@echo off
rem ============================================================
rem  PosterBioskopAI - build aplikasi EXE Windows (offline)
rem  Jalankan file ini dengan double-click di PC Windows kamu.
rem  Hasil akhirnya: dist\PosterBioskopAI.exe
rem ============================================================
cd /d "%~dp0"

echo [1/4] Membuat icon aplikasi...
python make_icon.py
if errorlevel 1 (
    py make_icon.py
)

echo [2/4] Meng-install dependensi (pillow, opencv, pyinstaller)...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    py -m pip install -r requirements.txt
)

echo [3/4] Membangun EXE dengan PyInstaller (butuh 2-5 menit)...
pyinstaller --noconfirm --onefile --windowed --name PosterBioskopAI ^
    --icon=icon.ico poster_app.py
if errorlevel 1 (
    pyinstaller --noconfirm --onefile --windowed --name PosterBioskopAI ^
        --icon=icon.ico poster_app.py
)

echo [4/4] Selesai!
echo   Aplikasi ada di:  dist\PosterBioskopAI.exe
echo   Kalau antivirus memblokir, pilih "Keep anyway" / "Izinkan".
pause
