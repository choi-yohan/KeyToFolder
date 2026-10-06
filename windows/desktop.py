"""Windows desktop entry point, also used by the bundled executable."""
import argparse
import ctypes
from ctypes import wintypes
import io
import os
from pathlib import Path
import sys
import tempfile
import threading
import traceback


def single_instance():
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
    kernel.CreateMutexW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.CreateMutexW(None, False, 'Local\\KeyToFolder.Desktop')
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    if ctypes.get_last_error() == 183:
        user = ctypes.WinDLL('user32')
        user.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
        user.FindWindowW.restype = wintypes.HWND
        user.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        user.SetForegroundWindow.argtypes = [wintypes.HWND]
        window = user.FindWindowW(None, 'KeyToFolder')
        if window:
            user.ShowWindow(window, 9)  # Restore a minimized window.
            user.SetForegroundWindow(window)
        kernel.CloseHandle(handle)
        return None, kernel
    return handle, kernel


def run(smoke_result=None):
    # Source runs use the repository; frozen runs use PyInstaller's resource folder.
    resource_root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))
    sys.path.insert(0, str(resource_root))
    import app
    import webview
    from http.server import ThreadingHTTPServer

    app.ROOT = resource_root
    if getattr(sys, 'frozen', False):
        # Migration from the source launcher's adjacent .settings.json.
        os.environ['KEYTOFOLDER_LEGACY_DIR'] = str(Path(sys.executable).resolve().parent)
        app.STATE = app.State()
    if smoke_result:
        from smoke_check import prepare
        prepare(app)
    server = ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
    server.daemon_threads = False
    thread = threading.Thread(target=server.serve_forever, name='KeyToFolder server', daemon=True)
    thread.start()
    url = f'http://127.0.0.1:{server.server_address[1]}/'
    window = None
    try:
        window = webview.create_window('KeyToFolder', url, width=1280, height=820,
                                      min_size=(720, 500), background_color='#101311')
        def pick_folder():
            chosen = window.create_file_dialog(webview.FileDialog.FOLDER)
            return str(chosen[0]) if chosen else ''
        # A frozen exe cannot run sys.executable -c for Tkinter: use its native picker.
        app.pick_folder = pick_folder
        if smoke_result:
            from smoke_check import check_window
            window.events.loaded += lambda: check_window(window, app, url, smoke_result)
            def timeout():
                if not smoke_result.exists():
                    smoke_result.write_text('{"ok": false, "error": "GUI startup timed out"}')
                    window.destroy()
            timer = threading.Timer(60, timeout)
            timer.daemon = True
            timer.start()
        webview.start(gui='edgechromium', private_mode=True)
    finally:
        if smoke_result and 'timer' in locals():
            timer.cancel()
        server.shutdown()
        thread.join()
        server.server_close()  # Wait for moves/settings writes to complete.
    if smoke_result:
        import json
        if not smoke_result.exists() or not json.loads(smoke_result.read_text())['ok']:
            raise RuntimeError('Packaged Windows smoke check failed.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--smoke-test', type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if sys.platform != 'win32':
        raise SystemExit('This desktop launcher is for Windows.')
    # Some GUI dependencies assume writable stdout/stderr even in --windowed builds.
    if sys.stdout is None:
        sys.stdout = io.StringIO()
    if sys.stderr is None:
        sys.stderr = io.StringIO()
    handle = kernel = None
    test_home = None
    try:
        if args.smoke_test:
            args.smoke_test = args.smoke_test.resolve()
            args.smoke_test.parent.mkdir(parents=True, exist_ok=True)
            test_home = tempfile.TemporaryDirectory(prefix='KeyToFolder-check-')
            os.environ['APPDATA'] = test_home.name
            os.environ.pop('KEYTOFOLDER_LEGACY_DIR', None)
        else:
            handle, kernel = single_instance()
            if handle is None:
                return
        run(args.smoke_test)
    except Exception:
        details = traceback.format_exc()
        if args.smoke_test:
            import json
            args.smoke_test.write_text(json.dumps({'ok': False, 'error': details}), encoding='utf-8')
        else:
            folder = Path(os.environ.get('APPDATA', str(Path.home()))) / 'KeyToFolder'
            try:
                folder.mkdir(parents=True, exist_ok=True)
                (folder / 'startup-error.log').write_text(details, encoding='utf-8')
            except OSError:
                pass
            ctypes.windll.user32.MessageBoxW(None,
                'KeyToFolder could not start. Ensure Microsoft Edge WebView2 Runtime is installed.\n'
                '시작하지 못했습니다. Microsoft Edge WebView2 Runtime 설치를 확인해 주세요.\n\n'
                + details[-1200:], 'KeyToFolder', 0x10)
        raise SystemExit(1)
    finally:
        if handle:
            kernel.CloseHandle(handle)
        if test_home:
            test_home.cleanup()


if __name__ == '__main__':
    main()
