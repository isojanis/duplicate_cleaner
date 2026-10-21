# Windows VM — Portable ZIP Testing Guide

## Prerequisites

| Requirement | Detail |
|---|---|
| OS | Windows 10 or 11, x64 |
| Python | **3.13 x64** — download from [python.org](https://www.python.org/downloads/windows/) |
| Source code | The `duplicate_cleaner` repo, copied into the VM (ZIP/USB/shared folder) |

> [!IMPORTANT]
> Python version matters. The build script enforces **exactly Python 3.13 x64**.
> During install, tick **"Add python.exe to PATH"** and choose the x64 installer.

---

## Part 1 — Build the portable ZIP

Open **PowerShell** (Win+X → Terminal, or search "PowerShell") from the repo root:

```powershell
# 1. Create the dedicated build environment
py -3.13 -m venv .venv-build

# 2. Activate it
.\.venv-build\Scripts\Activate.ps1

# 3. Install pinned build dependencies (PySide6, PyInstaller)
python -m pip install -r packaging\windows\requirements-build.txt

# 4. Run the build script
.\packaging\windows\build.ps1
```

> [!NOTE]
> If PowerShell blocks the activation script, run this first and then retry:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

### What the build does automatically

The script:
1. Verifies you're on Python 3.13 x64 (rejects anything else)
2. Runs PyInstaller with the pinned spec
3. Zips the output to `dist\DuplicateCleaner-0.1.0-windows-x64.zip`
4. Writes a `.sha256` checksum sidecar
5. Runs **`validate-portable.ps1`** automatically, which:
   - Verifies the SHA-256 checksum
   - Extracts to a temp path with **spaces and Unicode** in its name
   - Checks all required files are present (`DuplicateCleaner.exe`, `LICENSE`, `THIRD_PARTY_NOTICES`, `README.md`, QML assets)
   - Runs `--smoke-test` (starts the app, waits up to 60s, checks exit code)

If it ends with:

```
Portable build: ...\dist\DuplicateCleaner-0.1.0-windows-x64.zip
```

the automated part passed. ✅

---

## Part 2 — Manual acceptance testing

Extract the ZIP to a clean path — **not** inside the repo, and ideally with a space in the path to match real-user conditions:

```
C:\Users\YourName\Desktop\Duplicate Cleaner Test\DuplicateCleaner\
```

Launch `DuplicateCleaner.exe`. Work through each check below.

---

### Checklist

#### Startup
- [ ] App window appears, no crash, no Windows error dialog
- [ ] Window icon shown in taskbar and title bar

#### Scan
- [ ] Click the folder button (or Ctrl+O) — native Windows folder picker opens
- [ ] Pick a folder that contains some duplicate files
- [ ] Progress updates appear during scan
- [ ] Duplicate groups appear in results when scan completes
- [ ] File sizes and counts look correct

#### Cancel
- [ ] Start a scan on a large folder
- [ ] Click Cancel (or press Escape) mid-scan
- [ ] App stops promptly and shows partial results (not a freeze or crash)

#### Preview
- [ ] Click a duplicate **image** file (`.jpg`, `.png`, etc.) — image preview renders
- [ ] Click a duplicate **PDF** file — PDF page renders (if you have one)
- [ ] Click a duplicate **text** file (`.txt`, `.py`, etc.) — text content shown

#### Cleanup & Recycle Bin (most important Windows-specific check)
- [ ] Select one file from a duplicate group for removal
- [ ] Confirm deletion — file disappears from the list
- [ ] Open **Windows Recycle Bin** in Explorer
- [ ] The deleted file appears there
- [ ] Right-click → **Restore** — file returns to its original location ✅

> [!CAUTION]
> Only delete genuinely disposable test duplicates. The cleanup is real —
> files go to the Recycle Bin but are not permanently gone until you empty it.

#### Edge cases (optional but good)
- [ ] Scan a folder that contains **no** duplicates — app shows "0 groups" gracefully
- [ ] Try scanning a path with **spaces and Unicode** characters (e.g. `C:\Tëst Files\`)
- [ ] Scan a UNC path if you have one available (`\\server\share\...`)

---

## Part 3 — Validate an existing archive (optional)

If you copy a pre-built ZIP from Linux CI into the VM, validate it first:

```powershell
.\packaging\windows\validate-portable.ps1 -Archive .\dist\DuplicateCleaner-0.1.0-windows-x64.zip
```

Keep the `.sha256` file in the same folder as the `.zip` or this will fail.

---

## What to do if something goes wrong

| Symptom | Likely cause |
|---|---|
| Activation script blocked | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `Use x64 Python 3.13` error | Wrong Python selected — use `py -3.13` or pass `-Python` explicitly |
| Smoke test times out | Display driver / VM graphics issue — try a different VM graphics adapter |
| QML warnings in smoke test | Real bug — note the warning text and file an issue |
| App crashes on launch | Check Windows Event Viewer → Application log for the exception |
| Recycle Bin restore fails | Real bug — note the exact error shown by the app |
