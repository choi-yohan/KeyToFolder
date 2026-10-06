# KeyToFolder

[English guide](README.md)

일러스트를 보면서 키 하나로 실제 폴더에 분류하는 로컬 앱입니다. Python이 파일을 처리하고 브라우저가 화면을 보여줍니다. 파일 이동에는 인터넷 연결이 필요하지 않습니다.

## Features

- 영문자 A–Z, 숫자 0–9 및 `- = [ ] ; ' , . /`까지 **45개 키**에 목적지 폴더를 지정할 수 있습니다.
- 왼쪽의 썸네일 목록 사이드바를 스크롤하고 썸네일을 클릭하면 해당 이미지로 바로 이동합니다.
- 사진을 이동하면 다음 사진을 보여줍니다. 분류한 이미지는 목록에서 빠지고 이동을 취소하면 다시 나타납니다.
- 이동을 취소할 수 있고, 폴더 매핑은 다음 실행에도 유지됩니다. 목적지에 같은 이름의 파일이 있으면 덮어쓰지 않습니다.
- 최초 실행에서는 언어가 `None`이며 한국어(`ko-KR`) 또는 영어(`en-US`) 선택 창이 먼저 표시됩니다. 선택을 저장하면 이후 실행에도 유지됩니다. 상단 **언어** 버튼으로 다시 변경할 수 있습니다.
- JPG, JPEG, PNG, WebP, GIF, AVIF, BMP, ICO, SVG를 표시합니다. TIFF 미리보기에는 선택 사항인 Pillow가 필요합니다. HEIC, RAW, PSD는 현재 지원하지 않습니다.

## Requirements

- **Python 3.10 이상**: [python.org에서 설치](https://www.python.org/downloads/)하세요. 소스/브라우저 방식과 macOS 앱에 필요합니다. Windows 실행 파일에는 포함됩니다.
- 최신 Chrome, Edge, Firefox 또는 Safari. AVIF 등 일부 형식의 미리보기는 브라우저 지원에 따라 달라집니다.
- 기본 분류 기능은 Python 표준 라이브러리만 사용합니다. 별도의 패키지가 필요하지 않습니다.

macOS에서 작동을 확인했습니다. Windows 앱은 GitHub Actions에서 자동으로 확인했습니다. Linux와 기존 `launch.bat`는 해당 운영체제에서 테스트하지 않았습니다.

## Quick start

1. 저장소를 내려받거나 ZIP을 풀고 `app.py`와 `ui.html`을 같은 폴더에 둡니다.
2. macOS에서는 Release ZIP의 `KeyToFolder.app`을 더블클릭하세요. Dock에 끌어놓으면 다음부터 Dock에서 실행할 수 있습니다. 기존 `launch.command`도 사용할 수 있습니다. Windows에서는 `launch.bat`, Linux에서는 `bash launch.command`를 실행합니다.
3. 처음 실행할 때 언어를 선택하세요.
4. **원본 폴더**에서 분류할 폴더를 선택합니다.
5. **키 설정**의 키보드 모양에서 키를 클릭하고, 위쪽 폴더 입력란에서 경로를 지정한 뒤 저장하세요. 지정된 키는 강조색으로 표시되며 마우스를 올리면 폴더 이름이 보입니다.
6. 지정한 키를 누르면 사진을 이동하고 다음 사진을 보여줍니다.

macOS에서 실행 권한이 없다고 나오면 앱 폴더의 터미널에서 다음을 실행하세요.

```bash
chmod +x launch.command
./launch.command
```

직접 실행하는 방법:

```bash
# macOS / Linux
python3 app.py

# Windows
py -3 app.py
```

Windows/Linux의 폴더 선택 창은 Tkinter를 사용합니다. Tkinter가 없는 환경에서도 폴더 경로를 직접 입력해 분류할 수 있습니다.

## Shortcuts

| 키 | 동작 |
|---|---|
| 지정한 영문자·숫자·특수문자 | 해당 폴더로 이동 |
| ← / → | 이전 / 다음 사진 |
| Space | 분류하지 않고 다음 사진 |
| ⌘Z 또는 Ctrl+Z | 마지막 이동 취소 |

Space와 오른쪽 화살표는 모두 다음 이미지로 이동합니다. Space는 분류를 건너뛰는 용도로 사용할 수 있습니다. 특수문자는 실제 키 위치를 기준으로 처리하므로 Shift로 다른 문자를 입력하더라도 같은 매핑을 사용합니다. 설정 입력 중이나 언어 선택 중에는 분류 단축키가 작동하지 않습니다. 길게 누르고 있어도 연속 이동하지 않습니다.

## Optional optimized previews

TIFF 미리보기와 작은 크기의 썸네일을 사용하려면 앱 폴더에서 가상 환경을 만들고 Pillow를 설치하세요. Pillow를 설치하면 작은 썸네일을 생성해 캐시하고, 설치하지 않았으면 브라우저가 원본 이미지로 썸네일을 표시합니다. 화면에 보이는 구간과 그 주변만 표시하므로 사진이 많아도 수천 개의 썸네일을 한꺼번에 만들지 않습니다. 실행 스크립트는 프로젝트의 가상 환경을 우선 사용합니다.

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

- 파일을 이동할 때 이미지 내용이나 이름을 바꾸지 않습니다. 목적지에 같은 이름의 파일이 있으면 덮어쓰지 않습니다.
- 하위 폴더를 검색할 때는 지정한 목적지 폴더를 제외합니다.
- 최근 1,000개 이동의 취소 기록을 저장합니다. 이동 후 파일이 수정되거나 사라지면 자동으로 되돌리지 않습니다.

오른쪽 사이드바 하단에서 직전에 옮긴 사진의 썸네일, 현재 폴더, 되돌릴 폴더를 확인할 수 있습니다. 해당 영역의 **이동 취소** 버튼을 누르면 복원됩니다.

설정과 언어, 이동 기록은 macOS에서 `~/Library/Application Support/KeyToFolder/settings.json`, Windows에서 `%APPDATA%/KeyToFolder/settings.json`, Linux에서 `$XDG_CONFIG_HOME/KeyToFolder/settings.json` 또는 `~/.config/KeyToFolder/settings.json`에 저장됩니다.

설정에는 개인 폴더 경로가 있으므로 공개하지 마세요. `.gitignore`는 `.settings.json`, 가상 환경, 캐시를 제외합니다. 언어 설정이 없는 이전 설정을 사용하면 언어 선택 창이 한 번 표시됩니다.

## Local operation

서버는 이 컴퓨터의 `127.0.0.1`에만 연결합니다. 이미지나 설정을 외부 서버로 보내지 않습니다. 인터넷에 공개하는 서버로 실행하지 마세요. macOS 앱으로 실행했다면 창을 닫거나 ⌘Q를 누르면 앱과 서버가 종료됩니다. 브라우저 방식으로 실행했다면 터미널에서 Ctrl+C를 누르세요.

## macOS app launcher

Release에는 macOS 11 이상용 Apple Silicon 및 Intel 통합 실행 파일이 포함됩니다. 독립된 앱 창으로 실행되므로 별도의 브라우저나 터미널이 필요하지 않습니다. Python 3.10 이상은 여전히 필요합니다. Apple Silicon에서 실행을 확인했습니다. Intel Mac에서 실제 실행은 확인하지 않았습니다. 앱에는 로컬 ad-hoc 서명만 적용되어 있으며, Apple 개발자 서명 및 공증을 받지 않은 앱이므로 첫 실행 시 macOS의 실행 확인이 필요할 수 있습니다.

## Windows executable

Windows x64 앱에는 Python과 Pillow가 포함됩니다. `KeyToFolder-Windows-x64.zip`을 압축 해제하고 `KeyToFolder.exe`를 더블클릭하면 터미널 없이 앱 창으로 실행됩니다. 창을 닫으면 서버도 종료됩니다. 설정과 이동 기록은 `%APPDATA%\KeyToFolder\settings.json`에 저장되어 실행 파일을 교체해도 유지됩니다.

[Microsoft Edge WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/)이 필요합니다. 실행 파일에는 개발자 코드 서명이 없습니다. 기존 `launch.bat` 방식도 사용할 수 있으며, 그 경우 Python을 따로 설치해야 합니다.

GitHub의 **Actions → Build Windows app**에서 빌드가 완료된 실행을 열고 `KeyToFolder-Windows-x64` 아티팩트를 내려받으세요. 압축을 풀면 배포용 Windows ZIP이 들어 있습니다. 빌드 과정에서 실제 Windows 앱 창, 사진 표시, 이동·되돌리기, 설정 저장을 자동으로 확인합니다.

직접 빌드하려면 Python 3.12를 설치한 Windows에서 `windows/build.bat`를 실행하세요. 결과는 `dist/KeyToFolder.exe`입니다.

## License

MIT. See [LICENSE](LICENSE).

Developed with assistance from OpenAI Codex, GPT-6.1 Sol.
