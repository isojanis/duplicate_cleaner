# Duplicate Cleaner

A starter KDE-friendly desktop app for finding and deleting duplicate files.

## Stack

- Python
- PySide6
- Qt Quick / QML
- Kirigami

## Stable host setup

This project should use the host system Qt/Kirigami stack together with a local virtual environment for Python-only tooling. Avoid installing `PySide6` from pip here, because the wheel can conflict with the host Kirigami plugin ABI.

1. Create the virtual environment with system site packages:

```bash
python3 -m venv --system-site-packages .venv
```

2. Activate it:

```bash
source .venv/bin/activate
```

3. Ensure pip is available and install the local tooling:

```bash
python -m ensurepip --upgrade
pip install debugpy
pip install -e . --no-deps
```

4. Launch the app:

```bash
PYTHONPATH=src python -m duplicate_cleaner
```

## VS Code

- Interpreter: `${workspaceFolder}/.venv/bin/python`
- Use the `Bootstrap Duplicate Cleaner (Host)` task once after recreating `.venv`.
- `Run Duplicate Cleaner (Host)` and `Debug Duplicate Cleaner (Host)` now auto-install `debugpy` if it is missing.

## Notes

- This is a UI scaffold. The duplicate scanning and delete workflow are placeholders for now.
- On some Linux systems, Kirigami QML modules may need a distro package such as `kirigami2` or `kdeclarative`.
