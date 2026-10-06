# KeyToFolder

[한국어 안내](README.ko-KR.md)

A local image sorter: preview an image, press a mapped key, and move the original file into a destination folder. Python handles files; your browser provides the interface.

## Features

- Assign **45 destination keys**: A–Z, 0–9, and `- = [ ] ; ' , . /`.
- Browse a scrollable thumbnail sidebar. Click a thumbnail to jump directly to that image.
- Move an image and immediately show the next one. The sidebar follows selection and updates after moves and undo.
- Undo moves, keep mappings across launches, and never overwrite an existing file.
- Choose **한국어 (ko-KR)** or **English (en-US)**. The initial language is `None`, so the first launch asks you to choose. Your choice persists and can be changed using the Language button.
- View JPG/JPEG, PNG, WebP, GIF, AVIF, BMP, ICO and SVG. TIFF previews use optional Pillow. HEIC, RAW and PSD are not currently supported.

## Windows executable

The Windows x64 desktop build includes Python and Pillow, opens its own window, and stops the local server when the window closes. Extract `KeyToFolder-Windows-x64.zip` and double-click `KeyToFolder.exe`. Settings remain in `%APPDATA%\KeyToFolder\settings.json`, so replacing the executable preserves preferences and undo history.

Microsoft Edge WebView2 Runtime is required: [download from Microsoft](https://developer.microsoft.com/en-us/microsoft-edge/webview2/). The executable is not code-signed. The original `launch.bat` remains available for source/browser mode, which requires installed Python.

The **Build Windows app** GitHub Actions workflow builds and checks the actual packaged window, image preview, move, undo, and settings persistence on Windows. Download its `KeyToFolder-Windows-x64` artifact and extract the Windows ZIP inside. For a local build, install Python 3.12 and run `windows/build.bat`; output is `dist/KeyToFolder.exe`.

## Requirements

- **Python 3.10 or newer**: [download Python](https://www.python.org/downloads/). Required for source/browser mode and the macOS launcher; bundled with the Windows executable.
- A modern Chrome, Edge, Firefox or Safari browser. Preview support for some formats, such as AVIF, depends on your browser.
- Core sorting uses only Python's standard library. No additional packages are required.

macOS operation has been checked. The Windows desktop build is checked by GitHub Actions. Linux and the original Windows batch launcher have not been tested on those operating systems.

## Quick start

1. Download and extract the project. Keep `app.py` and `ui.html` together.
2. On macOS, double-click `KeyToFolder.app` (included in the release ZIP), and you can drag the app to the Dock for quick access. `launch.command` remains available. On Windows, run `launch.bat`. On Linux, run `bash launch.command`.
3. Choose a language on the first launch.
4. Select a **Source folder**.
5. Open **Key mapping**, click a key on the keyboard layout, and choose or enter its destination folder in the editor above. Assigned keys are highlighted; hover to see the folder name. Save to apply your changes.
6. Press a mapped key to move the current image. The next image appears automatically.

If macOS reports that the launcher is not executable, run these commands in the project folder:

```bash
chmod +x launch.command
./launch.command
```

You can also start the app directly from the project folder:

```bash
# macOS / Linux
python3 app.py

# Windows
py -3 app.py
```

Windows/Linux folder selection uses Tkinter. If it is unavailable, enter the folder path manually.

## Keyboard controls

| Key | Action |
|---|---|
| Mapped letter, number or punctuation key | Move to its destination folder |
| Left / Right arrow | Previous / next image |
| Space | Skip sorting and go to the next image |
| Command+Z / Ctrl+Z | Undo the last move |

Space and Right arrow intentionally perform the same navigation action. Punctuation mappings use physical keyboard positions; holding Shift does not change the assigned destination. Commands are ignored while typing in a field, selecting a language, or holding down a key.

## Optional optimized previews

For TIFF previews and smaller, cached sidebar thumbnails, install Pillow in a project virtual environment. Without Pillow, the sidebar uses browser-supported original images. Only the visible section and nearby items are rendered, so large folders do not create thousands of thumbnail elements. The launchers prefer this environment automatically.

macOS / Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Windows:

```bat
py -3 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python app.py
```

## Settings and files

Files are moved without changing their names or image contents. If a destination already contains the filename, the move is blocked. Recursive scanning excludes assigned destination folders.

The app retains the last 1,000 moves for undo. If a moved file has changed or disappeared, undo is blocked.

The bottom of the right sidebar shows the last moved image, its current folder, and the folder it returns to when you undo. Use the Undo move button there to restore it.

Settings, language and undo history are stored outside the app: macOS `~/Library/Application Support/KeyToFolder/settings.json`; Windows `%APPDATA%/KeyToFolder/settings.json`; Linux `$XDG_CONFIG_HOME/KeyToFolder/settings.json` (or `~/.config/KeyToFolder/settings.json`).

Settings contain local folder paths. Do not publish them. `.gitignore` excludes `.settings.json`, virtual environments and caches. An older configuration without a language triggers the language chooser once.

## Local operation

The server binds only to `127.0.0.1`. Images and settings are not uploaded to an external service. Do not expose the server to the internet. In macOS app mode, close the app window or press Command+Q to stop the app and server. In browser mode, press Ctrl+C in the terminal.

## License

MIT. See [LICENSE](LICENSE).

Developed with assistance from OpenAI Codex, GPT-6.1 Sol.

## macOS app launcher

The release includes a universal launcher for Apple Silicon and Intel Macs (macOS 11+). It opens the interface in its own window; no separate browser or terminal is needed. Python 3.10+ is still required. Apple Silicon execution has been checked; the Intel build has not been tested on an Intel Mac. The application has a local ad-hoc signature, not an Apple Developer signature or notarization, so macOS may require approval on first launch.
