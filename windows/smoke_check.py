"""Checks the actual packaged UI with disposable fixtures on the Windows runner."""
import json
from pathlib import Path
import time
import traceback
from urllib.request import Request, urlopen


def prepare(app):
    from PIL import Image
    fixture = (app.SETTINGS.parent / 'fixture').resolve()
    source, destination = fixture / 'source', fixture / 'destination'
    source.mkdir(parents=True)
    destination.mkdir()
    Image.new('RGB', (320, 240), '#b9e18f').save(source / 'sample.png')
    for index in range(1, 100):
        Image.new('RGB', (320, 240), (index * 2, 120, 160)).save(source / f'zsample-{index:03d}.png')
    app.STATE.config.update(language='en-US', source=str(source), history=[],
                            mappings={'a': {'label': 'Fixture', 'path': str(destination)}})
    app.STATE.config['presets'] = {}
    app.STATE.ensure_presets()
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
            loaded = window.evaluate_js("document.getElementById('filename').textContent === 'sample.png' && document.getElementById('image').naturalWidth > 0 && document.querySelector('.thumbnail-card img')?.naturalWidth > 0")
            if loaded:
                break
            time.sleep(.1)
        else:
            raise AssertionError('The packaged HTML, JavaScript, API or image did not load.')
        # Keep the same decoded element when scrolling nearby and returning.
        window.evaluate_js("window.__retainedThumbnail = document.querySelector('.thumbnail-card img'); true")
        window.evaluate_js("document.getElementById('thumbnailViewport').scrollTop = 2300; true")
        time.sleep(.3)
        window.evaluate_js("document.getElementById('thumbnailViewport').scrollTop = 0; true")
        time.sleep(.3)
        assert window.evaluate_js("document.querySelector('.thumbnail-card img') === window.__retainedThumbnail"), 'Nearby scrolling recreated an image element.'
        # Scan distant ranges: retained elements must be bounded, not all 100 images.
        for index in range(0, 100, 10):
            window.evaluate_js(f"document.getElementById('thumbnailViewport').scrollTop = {index} * thumbnailRowHeight(); true")
            time.sleep(.15)
        assert window.evaluate_js("thumbNodes.size <= 64"), 'Thumbnail cache exceeded its bound.'
        window.evaluate_js("delete window.__retainedThumbnail; true")
        before = api('state')
        assert before['remaining'] == 100
        # Check source-aware presets and their warning in the frozen Windows GUI.
        original = {'source': before['source'], 'recursive': before['recursive'], 'mappings': before['mappings']}
        saved = api('preset_save', {'name': 'Stage 1', **original})
        assert saved['presets']['Stage 1'] == original
        window.evaluate_js('render(' + json.dumps(saved) + '); mappingDialog(); loadPresetLayout("Stage 1"); true')
        assert window.evaluate_js("document.getElementById('mappingSource').value") == original['source']
        destination = before['mappings']['a']['path']
        edit_script = ("selectMappingKey('a'); document.getElementById('mappingLabel').value='Unsaved'; "
                       "document.getElementById('mappingLabel').dispatchEvent(new Event('input', {bubbles:true})); "
                       "document.getElementById('mappingSource').value=" + json.dumps(destination) + "; "
                       "document.getElementById('mappingSource').dispatchEvent(new Event('blur')); true")
        window.evaluate_js(edit_script)
        assert window.evaluate_js("document.getElementById('sourceChangeDialog').open"), 'Missing unsaved-preset warning.'
        window.evaluate_js("document.getElementById('cancelSourceChange').click(); true")
        assert window.evaluate_js("document.getElementById('mappingSource').value") == original['source']
        window.evaluate_js(edit_script)
        window.evaluate_js("document.getElementById('confirmSourceChange').click(); true")
        assert window.evaluate_js("document.getElementById('mappingSource').value") == destination
        window.evaluate_js("document.getElementById('mappingDialog').close(); true")
        second = {'source': destination, 'recursive': True,
                  'mappings': {'a': {'path': original['source'], 'label': 'Return'}}}
        api('preset_save', {'name': 'Stage 2', **second})
        applied = api('layout', second)
        assert applied['source'] == destination and applied['mappings']['a']['path'] == original['source']
        before = api('layout', original)
        assert app.State().config['presets']['Stage 1'] == original
        assert app.State().config['presets']['Stage 2'] == second
        moved = api('move', {'key': 'a', 'id': before['image']['id']})
        assert moved['remaining'] == 99 and moved['lastMove']['available']
        with urlopen(url + 'undo-thumbnail?id=' + moved['lastMove']['id'] + '&token=' + app.TOKEN) as response:
            assert response.headers['Content-Type'] == 'image/png' and len(response.read()) > 0
        restored = api('undo', {})
        assert restored['remaining'] == 100 and restored['lastMove'] is None
        assert app.State().config['mappings'] == restored['mappings']
        assert app.SETTINGS.parent.name == 'KeyToFolder'
        result.write_text(json.dumps({'ok': True, 'checks': ['native-window', 'packaged-html-js',
            'image-preview', 'move', 'undo-preview', 'undo', 'persistent-settings', 'thumbnail-element-reuse', 'thumbnail-cache-bound', 'source-aware-presets', 'unsaved-source-warning-cancel-confirm']}), encoding='utf-8')
    except Exception:
        result.write_text(json.dumps({'ok': False, 'error': traceback.format_exc()}), encoding='utf-8')
    finally:
        window.destroy()
