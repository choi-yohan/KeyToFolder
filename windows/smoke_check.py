"""Checks the actual packaged UI with disposable fixtures on the Windows runner."""
import json
from pathlib import Path
import time
import traceback
from urllib.request import Request, urlopen


def prepare(app):
    from PIL import Image
    fixture = app.SETTINGS.parent / 'fixture'
    source, destination = fixture / 'source', fixture / 'destination'
    source.mkdir(parents=True)
    destination.mkdir()
    Image.new('RGB', (320, 240), '#b9e18f').save(source / 'sample.png')
    app.STATE.config.update(language='en-US', source=str(source), history=[],
                            mappings={'a': {'label': 'Fixture', 'path': str(destination)}})
    app.STATE.scan()
    app.STATE.save()


def check_window(window, app, url, result):
    def api(action, data=None):
        headers = {'X-Sorter-Token': app.TOKEN}
        payload = None if data is None else json.dumps(data).encode()
        if payload is not None:
            headers['Content-Type'] = 'application/json'
        with urlopen(Request(url + 'api/' + action, data=payload, headers=headers), timeout=10) as response:
            return json.load(response)
    try:
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            loaded = window.evaluate_js("document.getElementById('filename').textContent === 'sample.png' && document.getElementById('image').naturalWidth > 0")
            if loaded:
                break
            time.sleep(.1)
        else:
            raise AssertionError('The packaged HTML, JavaScript, API or image did not load.')
        before = api('state')
        assert before['remaining'] == 1
        moved = api('move', {'key': 'a', 'id': before['image']['id']})
        assert moved['remaining'] == 0 and moved['lastMove']['available']
        with urlopen(url + 'undo-thumbnail?id=' + moved['lastMove']['id'] + '&token=' + app.TOKEN) as response:
            assert response.headers['Content-Type'] == 'image/png' and len(response.read()) > 0
        restored = api('undo', {})
        assert restored['remaining'] == 1 and restored['lastMove'] is None
        assert app.State().config['mappings'] == restored['mappings']
        assert app.SETTINGS.parent.name == 'KeyToFolder'
        result.write_text(json.dumps({'ok': True, 'checks': ['native-window', 'packaged-html-js',
            'image-preview', 'move', 'undo-preview', 'undo', 'persistent-settings']}), encoding='utf-8')
    except Exception:
        result.write_text(json.dumps({'ok': False, 'error': traceback.format_exc()}), encoding='utf-8')
    finally:
        window.destroy()
