# Duplicate Cleaner

A starter KDE-friendly desktop app for finding and deleting duplicate files.

## Stack

- Python
- PySide6
- Qt Quick / QML
- Kirigami

## Run in VS Code or terminal

1. Create a virtual environment:

```bash
python3 -m venv .venv
```

2. Activate it:

```bash
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -e .
```

4. Launch the app:

```bash
python -m duplicate_cleaner
```

## Notes

- This is a UI scaffold. The duplicate scanning and delete workflow are placeholders for now.
- On some Linux systems, Kirigami QML modules may need a distro package such as `kirigami2` or `kdeclarative`.
