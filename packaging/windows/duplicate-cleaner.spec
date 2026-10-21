# Build on Windows; the same recipe can be smoke-tested on Linux.
from pathlib import Path
import sys

from PyInstaller.utils.hooks import copy_metadata

root = Path(SPECPATH).parents[1]
data = [
    (str(root / "qml"), "duplicate_cleaner/resources/qml"),
    (str(root / "packaging/assets"), "duplicate_cleaner/resources/assets"),
    (str(root / "README.md"), "."),
    (str(root / "LICENSE"), "."),
    (str(root / "THIRD_PARTY_NOTICES"), "."),
]
for package in ("PySide6", "PySide6_Addons", "PySide6_Essentials", "shiboken6"):
    data += copy_metadata(package)

# QtQml/QtQuick hooks collect Qt's QML modules and their plugin dependencies.
# Explicit imports cover modules reached only from QML.
a = Analysis(
    [str(root / "packaging/windows/launcher.py")],
    pathex=[str(root / "src")],
    datas=data,
    hiddenimports=["PySide6.QtQuick", "PySide6.QtQuickControls2", "PySide6.QtPdf", "PySide6.QtSvg"],
    excludes=["PyQt5", "PyQt6", "PySide2"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DuplicateCleaner",
    console=False,
    icon=str(root / "packaging/assets/duplicate-cleaner.ico") if sys.platform == "win32" else None,
)
coll = COLLECT(exe, a.binaries, a.datas, name="DuplicateCleaner")
