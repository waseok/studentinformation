# -*- mode: python ; coding: utf-8 -*-
# 빌드: pyinstaller --clean build.spec
# 결과물은 dist/ 폴더에 생성됩니다. Tesseract는 Windows에 별도 설치합니다.

block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=[
        ("config", "config"),
        ("templates", "templates"),
    ],
    hiddenimports=[
        "PyQt5",
        "PyQt5.QtCore",
        "PyQt5.QtGui",
        "PyQt5.QtWidgets",
        "cv2",
        "pytesseract",
        "fitz",
        "PIL",
        "PIL.Image",
        "openpyxl",
        "reportlab",
        "qrcode",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="StudentInfoOneScanOCR",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
)
