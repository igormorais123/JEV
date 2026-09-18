"""Persistence and evidence integrity checks, isolated from project execution data."""
import copy
import importlib.util
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / 'server.py'
spec = importlib.util.spec_from_file_location('jev_server', MODULE)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


def fresh():
    return dict(schema_version=1, revision=0, updated_at='2026-09-18T20:00:00Z', system_progress={}, stage_progress={}, runs=[], events=[])


def run_record():
    return dict(id='isolated-test-run', system_id='S01', phase='simple', evidence='offline', status='running', started_at='2026-09-18T20:00:00Z',
                attempts=[dict(id='isolated-attempt', status='pending', latency_ms=None, input_tokens=None, output_tokens=None, cost_usd=None, reserved_usd=.001, cache_hit=False)], decisions=[])


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.previous = app.STATE_PATH
        app.STATE_PATH = Path(cls.temp.name) / 'execution.json'
        cls.http = app.ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.http.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        app.STATE_PATH = cls.previous
        cls.temp.cleanup()

    def setUp(self):
        app.STATE_PATH.write_text(json.dumps(fresh()), encoding='utf-8')

    def request(self, path, data=None, headers=None):
        headers = headers or {}
        if data is not None:
            headers = {'Content-Type': 'application/json', 'X-Jev-Lab': '1', **headers}
        request = urllib.request.Request(self.base+path, data=json.dumps(data).encode() if data is not None else None, headers=headers, method='PUT' if data is not None else 'GET')
        try:
            response = urllib.request.urlopen(request)
        except urllib.error.HTTPError as error:
            response = error
        return response.status, response.read()

    def test_save_revision_and_reject_stale(self):
        state = fresh()
        state['system_progress']['S01'] = {'simple': 'running', 'notes': 'teste isolado'}
        status, body = self.request('/api/state', state)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['revision'], 1)
        self.assertEqual(self.request('/api/state', state)[0], 409)
        self.assertEqual(json.loads(app.STATE_PATH.read_text())['revision'], 1)

    def test_reconcile_unknown_cost_without_duplicate(self):
        state = fresh()
        state['runs'] = [run_record()]
        status, body = self.request('/api/state', state)
        self.assertEqual(status, 200)
        state = json.loads(body)
        state['runs'][0]['status'] = 'completed'
        attempt = state['runs'][0]['attempts'][0]
        attempt.update(status='success', cost_usd=.00001, reserved_usd=0, input_tokens=200, output_tokens=5, latency_ms=220)
        status, body = self.request('/api/state', state)
        self.assertEqual(status, 200)
        state = json.loads(body)
        state['runs'][0]['attempts'][0]['cost_usd'] = 0
        self.assertEqual(self.request('/api/state', state)[0], 400)

    def test_corrupt_state_is_not_reset(self):
        app.STATE_PATH.write_text('{broken', encoding='utf-8')
        self.assertEqual(self.request('/api/state')[0], 422)
        self.assertEqual(app.STATE_PATH.read_text(), '{broken')

    def test_private_paths_not_served(self):
        for path in ['/.env', '/lab/data/execution.json', '/../.env', '/artifacts/.env']:
            self.assertEqual(self.request(path)[0], 404)

    def test_cross_origin_and_wrong_host(self):
        self.assertEqual(self.request('/api/state', fresh(), {'Origin': 'https://example.com'})[0], 403)
        self.assertEqual(self.request('/api/state', headers={'Host': 'example.com'})[0], 403)

    def test_invalid_cost_and_duplicate_attempts(self):
        state = fresh()
        state['runs'] = [run_record()]
        state['runs'][0]['attempts'][0]['cost_usd'] = -1
        self.assertEqual(self.request('/api/state', state)[0], 400)
        state['runs'][0]['attempts'][0]['cost_usd'] = None
        duplicate = copy.deepcopy(state['runs'][0])
        duplicate['id'] = 'another-run'
        state['runs'].append(duplicate)
        self.assertEqual(self.request('/api/state', state)[0], 400)

    def test_secret_fields_rejected(self):
        state = fresh()
        state['api_key'] = 'not-a-real-key'
        self.assertEqual(self.request('/api/state', state)[0], 400)

    def test_evidence_cannot_be_deleted(self):
        state = fresh()
        state['runs'] = [run_record()]
        _, body = self.request('/api/state', state)
        state = json.loads(body)
        state['runs'] = []
        self.assertEqual(self.request('/api/state', state)[0], 400)


if __name__ == '__main__':
    unittest.main()
