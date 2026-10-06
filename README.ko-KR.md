# KeyToFolder

[English guide](README.md)

이미지를 미리 보고 지정한 키를 눌러 원본 파일을 목적지 폴더로 옮기는 로컬 이미지 분류 앱입니다. Python이 파일을 처리하고 브라우저가 화면을 보여줍니다.

## 주요 기능

- **45개의 목적지 키**를 지정할 수 있습니다: A–Z, 0–9 및 `- = [ ] ; ' , . /`.
- 스크롤 가능한 한 열 썸네일 사이드바를 둘러볼 수 있습니다. 썸네일을 클릭하면 해당 이미지로 바로 이동합니다.
- 이미지를 옮기면 다음 이미지가 즉시 표시됩니다. 사이드바는 현재 선택을 따라가며, 이동하거나 되돌리면 목록도 갱신됩니다.
- 이동을 되돌릴 수 있고, 키 매핑은 다음 실행에도 유지되며, 기존 파일은 덮어쓰지 않습니다.
- **한국어(ko-KR)** 또는 **영어(en-US)**를 선택할 수 있습니다. 초기 언어는 `None`이므로 처음 실행할 때 언어를 선택합니다. 선택은 저장되며 **언어** 버튼으로 변경할 수 있습니다.
- JPG/JPEG, PNG, WebP, GIF, AVIF, BMP, ICO, SVG를 표시합니다. TIFF 미리보기에는 선택 사항인 Pillow를 사용합니다. HEIC, RAW, PSD는 현재 지원하지 않습니다.

## Windows 실행 파일

Windows x64 데스크톱 버전에는 Python과 Pillow가 포함됩니다. 독립된 앱 창으로 실행되며, 창을 닫으면 로컬 서버도 종료됩니다. `KeyToFolder-Windows-x64.zip`을 압축 해제하고 `KeyToFolder.exe`를 더블클릭하세요. 설정은 `%APPDATA%\KeyToFolder\settings.json`에 저장되므로 실행 파일을 교체해도 설정과 이동 취소 기록이 유지됩니다.

Microsoft Edge WebView2 Runtime이 필요합니다: [Microsoft에서 다운로드](https://developer.microsoft.com/en-us/microsoft-edge/webview2/). 실행 파일에는 코드 서명이 없습니다. 기존 `launch.bat`도 소스/브라우저 방식으로 사용할 수 있으며, 이 방식에는 Python 설치가 필요합니다.

**Build Windows app** GitHub Actions 워크플로는 Windows에서 앱을 빌드하고, 패키징된 실제 앱 창, 이미지 미리보기, 이동, 되돌리기, 설정 저장을 확인합니다. `KeyToFolder-Windows-x64` 아티팩트를 다운로드하고 그 안의 Windows ZIP을 압축 해제하세요. 로컬에서 빌드하려면 Python 3.12를 설치하고 `windows/build.bat`를 실행하세요. 결과는 `dist/KeyToFolder.exe`에 생성됩니다.

## 실행 요구 사항

- **Python 3.10 이상**: [Python 다운로드](https://www.python.org/downloads/). 소스/브라우저 방식과 macOS 실행 프로그램에 필요하며, Windows 실행 파일에는 포함되어 있습니다.
- 최신 Chrome, Edge, Firefox 또는 Safari 브라우저. AVIF 등 일부 형식의 미리보기 지원은 브라우저에 따라 달라집니다.
- 기본 분류 기능은 Python 표준 라이브러리만 사용합니다. 추가 패키지는 필요하지 않습니다.

macOS에서 작동을 확인했습니다. Windows 데스크톱 버전은 GitHub Actions에서 확인합니다. Linux와 기존 Windows 배치 실행 프로그램은 해당 운영체제에서 테스트하지 않았습니다.

## 빠른 시작

1. 프로젝트를 다운로드하고 압축을 해제하세요. `app.py`와 `ui.html`은 같은 폴더에 두세요.
2. macOS에서는 Release ZIP에 포함된 `KeyToFolder.app`을 더블클릭하세요. 앱을 Dock으로 끌어놓으면 빠르게 실행할 수 있습니다. `launch.command`도 계속 사용할 수 있습니다. Windows에서는 `launch.bat`를, Linux에서는 `bash launch.command`를 실행하세요.
3. 처음 실행할 때 언어를 선택하세요.
4. **원본 폴더**를 선택하세요.
5. **키 설정**을 열고 키보드 배치에서 키를 클릭한 뒤, 위쪽 편집 영역에서 목적지 폴더를 선택하거나 입력하세요. 지정된 키는 강조되며, 마우스를 올리면 폴더 이름이 표시됩니다. 저장하면 변경 사항이 적용됩니다.
6. 지정한 키를 누르면 현재 이미지가 이동하고 다음 이미지가 자동으로 표시됩니다.

macOS에서 실행 프로그램에 실행 권한이 없다고 나오면 프로젝트 폴더에서 다음 명령을 실행하세요.

```bash
chmod +x launch.command
./launch.command
```

프로젝트 폴더에서 앱을 직접 실행할 수도 있습니다.

```bash
# macOS / Linux
python3 app.py

# Windows
py -3 app.py
```

Windows/Linux의 폴더 선택에는 Tkinter를 사용합니다. 사용할 수 없는 경우 폴더 경로를 직접 입력하세요.

## 키보드 조작

| 키 | 동작 |
|---|---|
| 지정한 영문자·숫자·특수문자 키 | 해당 목적지 폴더로 이동 |
| 왼쪽 / 오른쪽 화살표 | 이전 / 다음 이미지 |
| Space | 분류를 건너뛰고 다음 이미지로 이동 |
| Command+Z / Ctrl+Z | 마지막 이동 되돌리기 |

Space와 오른쪽 화살표는 의도적으로 같은 탐색 동작을 수행합니다. 특수문자 매핑은 실제 키보드 위치를 사용하므로 Shift를 눌러도 지정된 목적지는 바뀌지 않습니다. 입력란에 입력하거나 언어를 선택하는 동안, 또는 키를 길게 누르고 있는 동안에는 명령이 실행되지 않습니다.

## 선택 사항: 최적화된 미리보기

TIFF 미리보기와 크기가 작고 캐시되는 사이드바 썸네일을 사용하려면 프로젝트 가상 환경에 Pillow를 설치하세요. Pillow가 없으면 사이드바는 브라우저가 지원하는 원본 이미지를 사용합니다. 화면에 보이는 구간과 주변 항목만 표시하므로 큰 폴더에서도 수천 개의 썸네일 요소를 만들지 않습니다. 실행 프로그램은 이 가상 환경을 자동으로 우선 사용합니다.

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

## 설정과 파일 처리

파일을 옮길 때 이름이나 이미지 내용을 바꾸지 않습니다. 목적지에 같은 이름의 파일이 있으면 이동이 차단됩니다. 하위 폴더를 검색할 때는 지정된 목적지 폴더를 제외합니다.

앱은 최근 1,000건의 이동을 되돌릴 수 있도록 기록합니다. 이동한 파일이 변경되거나 사라지면 되돌리기가 차단됩니다.

오른쪽 사이드바 하단에는 마지막으로 옮긴 이미지, 현재 폴더, 되돌릴 때 돌아갈 폴더가 표시됩니다. 해당 영역의 **이동 취소** 버튼으로 복원할 수 있습니다.

설정, 언어, 이동 취소 기록은 앱 바깥에 저장됩니다: macOS는 `~/Library/Application Support/KeyToFolder/settings.json`, Windows는 `%APPDATA%/KeyToFolder/settings.json`, Linux는 `$XDG_CONFIG_HOME/KeyToFolder/settings.json` 또는 `~/.config/KeyToFolder/settings.json`을 사용합니다.

설정에는 로컬 폴더 경로가 포함되므로 공개하지 마세요. `.gitignore`는 `.settings.json`, 가상 환경, 캐시를 제외합니다. 언어가 없는 이전 설정을 사용하면 언어 선택 창이 한 번 표시됩니다.

## 로컬 실행

서버는 `127.0.0.1`에만 연결합니다. 이미지와 설정은 외부 서비스로 업로드되지 않습니다. 서버를 인터넷에 공개하지 마세요. macOS 앱 방식에서는 앱 창을 닫거나 Command+Q를 눌러 앱과 서버를 종료하세요. 브라우저 방식에서는 터미널에서 Ctrl+C를 누르세요.

## 라이선스

MIT. [LICENSE](LICENSE)를 참고하세요.

OpenAI Codex, GPT-6.1 Sol의 도움을 받아 개발했습니다.

## macOS 앱 실행 프로그램

Release에는 Apple Silicon과 Intel Mac용 통합 실행 프로그램(macOS 11 이상)이 포함됩니다. 독립된 창으로 화면을 표시하므로 별도 브라우저나 터미널이 필요하지 않습니다. Python 3.10 이상은 여전히 필요합니다. Apple Silicon에서 실행을 확인했으며, Intel 버전은 Intel Mac에서 테스트하지 않았습니다. 앱에는 로컬 ad-hoc 서명이 적용되어 있지만 Apple 개발자 서명이나 공증은 없으므로, macOS에서 처음 실행할 때 승인이 필요할 수 있습니다.
