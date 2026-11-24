# -*- coding: utf-8 -*-
"""Uji kecil untuk GitHub Actions (Windows asli): pastikan pyd onnxruntime
termuat mulus DI DALAM bundel PyInstaller sebelum aplikasi dirilis.

Ini persis titik crash yang dilaporkan pengguna (access violation saat
Windows memuat onnxruntime_pybind11_state.pyd) — kalau uji ini gagal, build
langsung ditandai gagal dan versi bermasalah tidak pernah sampai ke pengguna.
"""
import sys

import onnxruntime as ort

print("ORT OK:", ort.__version__)
print("providers:", ort.get_available_providers())
sys.stdout.flush()
sys.exit(0)
