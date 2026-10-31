import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


class PresetsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        with patch.object(Path, 'home', return_value=self.root):
            spec = importlib.util.spec_from_file_location('ktf_presets', Path(__file__).resolve().parents[1] / 'app.py')
            self.app = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.app)
        self.app.SETTINGS = self.root / 'configuration/settings.json'
        self.state = self.app.State()
        self.source = self.root / 'source'
        self.source.mkdir()
        self.destination = self.root / 'category'
        self.destination.mkdir()
        self.mapping = {'a': {'path': str(self.destination), 'label': 'First stage'}}
        self.layout = {'source': str(self.source), 'recursive': False, 'mappings': self.mapping}
        self.state.act('layout', self.layout)

    def tearDown(self):
        self.temp.cleanup()

    def save(self, name, layout=None, **options):
        return self.state.act('preset_save', {'name': name, **(layout or self.layout), **options})

    def test_two_stages_survive_restart_without_changing_active_context(self):
        context = copy.deepcopy(self.state.config)
        self.save('1차 분류')
        second = {'source': str(self.destination), 'recursive': True,
                  'mappings': {'/': {'path': str(self.root / 'currently-offline'), 'label': 'Second stage'}}}
        self.save('2차 분류', second)
        loaded = self.app.State()
        self.assertEqual(loaded.config['presets']['1차 분류'], self.layout)
        self.assertEqual(loaded.config['presets']['2차 분류'], second)
        for key in ['source', 'recursive', 'mappings', 'history', 'language']:
            self.assertEqual(loaded.config[key], context[key])

    def test_explicit_overwrite_delete_and_independent_applied_copy(self):
        self.save('Stage')
        changed = copy.deepcopy(self.layout)
        changed['mappings']['a']['label'] = 'Updated'
        with self.assertRaises(ValueError):
            self.save('Stage', changed)
        self.save('Stage', changed, overwrite=True)
        self.state.act('layout', self.state.config['presets']['Stage'])
        self.state.act('preset_delete', {'name': 'Stage'})
        self.assertEqual(self.state.config['mappings'], changed['mappings'])
        self.assertNotIn('Stage', self.app.State().config['presets'])

    def test_invalid_input_and_failed_writes_do_not_destroy_presets(self):
        self.save('Saved')
        previous = copy.deepcopy(self.state.config['presets'])
        for payload in [{'name': ''}, {'name': 'x'*81}, {'name': 'Wrong source', 'source': None},
                        {'name': 'Wrong', 'mappings': {'!': {'path': 'bad'}}}]:
            with self.assertRaises(ValueError):
                self.state.act('preset_save', {**self.layout, **payload})
        with patch.object(self.state, 'save', side_effect=OSError('Read only')):
            for action, payload in [('preset_save', {'name': 'New', **self.layout}),
                                    ('preset_delete', {'name': 'Saved'})]:
                with self.assertRaises(OSError):
                    self.state.act(action, payload)
                self.assertEqual(self.state.config['presets'], previous)

    def test_destination_can_be_the_previous_source(self):
        # A -> B, then B -> A must be validated against B, not the old source A.
        image = self.source / 'sample.png'
        image.write_bytes(b'unchanged illustration bytes')
        self.save('Parent')
        return_layout = {'source': str(self.destination), 'recursive': True,
                         'mappings': {'a': {'path': str(self.source), 'label': 'Return'}}}
        self.save('Child', return_layout)
        self.state.act('layout', self.state.config['presets']['Parent'])
        self.state.act('move', {'key': 'a', 'id': self.state.summary()['image']['id']})
        self.state.act('layout', self.state.config['presets']['Child'])
        self.assertEqual(self.state.config['source'], str(self.destination))
        self.assertTrue(self.state.config['recursive'])
        self.state.act('move', {'key': 'a', 'id': self.state.summary()['image']['id']})
        self.assertEqual(image.read_bytes(), b'unchanged illustration bytes')
        self.state.act('undo', {})
        self.assertEqual((self.destination/'sample.png').read_bytes(), b'unchanged illustration bytes')

    def test_failed_layout_does_not_partially_change_source_or_mapping(self):
        before = copy.deepcopy(self.state.config)
        invalid = {'source': str(self.destination), 'mappings': {'a': {'path': str(self.destination)}}}
        with self.assertRaises(ValueError):
            self.state.act('layout', invalid)
        self.assertEqual(self.state.config, before)
        valid = {'source': str(self.destination), 'recursive': True,
                 'mappings': {'a': {'path': str(self.source), 'label': 'Return'}}}
        with patch.object(self.state, 'save', side_effect=OSError('Read only')):
            with self.assertRaises(OSError):
                self.state.act('layout', valid)
        self.assertEqual(self.state.config, before)
        self.state.act('layout', {**self.layout, 'mappings': {}})
        self.assertEqual(self.state.config['mappings'], {})

    def test_blank_create_duplicate_rename_and_last_preset(self):
        self.state.config['language'] = 'ko-KR'
        before = copy.deepcopy(self.state.config)
        self.state.act('preset_create', {})
        name = self.state.summary()['selectedPreset']
        blank = {'source': '', 'recursive': False, 'mappings': {}}
        self.assertEqual(self.state.config['presets'][name], blank)
        self.assertEqual(self.state.config['source'], before['source'])
        self.state.act('preset_duplicate', {'name': 'Draft', **self.layout})
        duplicate = self.state.summary()['selectedPreset']
        self.assertEqual(self.state.config['presets'][duplicate], self.layout)
        self.state.act('layout', {'preset': duplicate, 'preset_name': 'Renamed', **self.layout})
        self.assertNotIn(duplicate, self.state.config['presets'])
        self.assertEqual(self.app.State().summary()['selectedPreset'], 'Renamed')
        before = copy.deepcopy(self.state.config)
        with self.assertRaises(ValueError):
            self.state.act('layout', {'preset': 'Renamed', 'preset_name': name, **self.layout})
        self.assertEqual(self.state.config, before)
        with patch.object(self.state, 'save', side_effect=OSError('Read only')):
            with self.assertRaises(OSError):
                self.state.act('layout', {'preset': 'Renamed', 'preset_name': 'Lost', **blank})
        self.assertEqual(self.state.config, before)
        for key in list(self.state.config['presets']):
            if key != name:
                self.state.act('preset_delete', {'name': key})
        with self.assertRaises(ValueError):
            self.state.act('preset_delete', {'name': name})
        self.state.act('layout', {'preset': name, 'preset_name': name, **blank})
        self.state.act('refresh', {})
        self.assertEqual(self.state.summary()['remaining'], 0)
        self.assertEqual(self.app.State().config['presets'][name], blank)

    def test_settings_without_presets_still_load(self):
        self.app.SETTINGS.write_text(json.dumps({'language': 'en-US', 'mappings': self.mapping}))
        state = self.app.State()
        self.assertEqual(state.config['presets']['Preset 1']['mappings'], self.mapping)
        self.assertEqual(state.config['mappings'], self.mapping)


if __name__ == '__main__':
    unittest.main(verbosity=2)
