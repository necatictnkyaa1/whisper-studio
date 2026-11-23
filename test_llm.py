"""Model adaptörü testleri: gerçek model yok, yerel sahte HTTP sunucusu (127.0.0.1)."""
import json
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from automatic import Hardware
import llm

class FakeOllama(BaseHTTPRequestHandler):
    requests = []
    slow = False
    stall_once = False
    def log_message(self, *args):
        pass
    def reply(self, rows):
        self.send_response(200)
        self.send_header('Content-Type', 'application/x-ndjson')
        self.end_headers()
        try:
            for row in rows:
                self.wfile.write((json.dumps(row) + '\n').encode())
                self.wfile.flush()
                if FakeOllama.slow:
                    time.sleep(0.3)
        except ConnectionError:
            pass  # iptal testinde istemci bağlantıyı bilerek kapatır
    def do_GET(self):
        if self.path == '/api/version':
            self.reply([{'version': 'test'}])
        elif self.path == '/api/tags':
            self.reply([{'models': [{'name': n} for n in FakeOllama.installed]}])
        elif self.path == '/api/ps':
            self.reply([{'models': FakeOllama.loaded}])
    installed = ['qwen3.5:4b']
    loaded = []
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        FakeOllama.requests.append((self.path, body))
        if self.path == '/api/chat' and body.get('model') == 'bozuk-model':
            data = json.dumps({'error': 'llama runner process has terminated: CUDA error'}).encode()
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if self.path == '/api/chat':
            rows =[{'message': {'content': part}, 'done': False} for part in ['{"a"', ': 1}']]
            if FakeOllama.slow:
                rows = [{'message': {'content': 'x'}, 'done': False}] * 40
            if body.get('think'):
                rows = [{'message': {'thinking': 'düşünüyorum '}, 'done': False}] * 3 + rows
            self.reply(rows + [{'message': {'content': ''}, 'done': True, 'eval_count': 2, 'done_reason': 'stop'}])
        elif self.path == '/api/pull':
            if FakeOllama.stall_once:
                FakeOllama.stall_once = False
                self.reply([{'status': 'downloading', 'digest': 'a', 'total': 100, 'completed': 10}] * 1)
                time.sleep(2)  # ilerleme yok; istemci bağlantıyı yenilemeli
                return
            self.reply([{'status': 'pulling manifest'}, {'status': 'downloading', 'total': 2 * 1073741824,
                                                         'completed': 1073741824}, {'status': 'success'}])

class AdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), FakeOllama)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.client = llm.OllamaClient(host=f'127.0.0.1:{cls.server.server_port}')
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
    def setUp(self):
        FakeOllama.requests.clear()
        FakeOllama.slow = False
        FakeOllama.stall_once = False

    def test_model_choice_is_automatic_and_conservative(self):
        self.assertEqual(llm.choose_model(Hardware(16000, 4000, 11900, True)).name, 'qwen3.5:9b')
        self.assertTrue(llm.choose_model(Hardware(16000, 4000, 11900, True)).gpu)
        self.assertEqual(llm.choose_model(Hardware(16000, 4000, 6000, True)).name, 'qwen3.5:4b')
        cpu = llm.choose_model(Hardware(16000, 3000, 0, False))
        self.assertEqual((cpu.name, cpu.gpu), ('qwen3.5:4b', False))

    def test_offline_falls_back_to_installed_model(self):
        plan = llm.choose_model(Hardware(16000, 4000, 11900, True), {'qwen3.5:4b'})
        self.assertEqual(plan.name, 'qwen3.5:4b')

    def test_chat_streams_json_without_thinking(self):
        plan = llm.ModelPlan('qwen3.5:9b', 16384, True, '')
        text, stats = self.client.chat(plan, [{'role': 'user', 'content': 'x'}], lambda: False, schema={'type': 'object'})
        self.assertEqual(json.loads(text), {'a': 1})
        self.assertEqual(stats['eval_count'], 2)
        path, body = FakeOllama.requests[-1]
        self.assertEqual(path, '/api/chat')
        self.assertIs(body['think'], False)
        self.assertEqual(body['format'], {'type': 'object'})
        self.assertEqual(body['options']['num_ctx'], 16384)
        self.assertNotIn('num_gpu', body['options'])

    def test_thinking_reports_progress_but_is_not_in_answer(self):
        plan = llm.ModelPlan('qwen3.5:9b', 24576, True, '')
        progress = []
        text, _ = self.client.chat(plan, [{'role': 'user', 'content': 'x'}], lambda: False, None, progress.append,
                                   think=True)
        self.assertEqual(text, '{"a": 1}')
        self.assertIs(FakeOllama.requests[-1][1]['think'], True)
        self.assertNotIn('format', FakeOllama.requests[-1][1])
        self.assertEqual(progress[:3], [12, 24, 36])  # içerik gelmeden önce de ilerleme var

    def test_server_error_becomes_clear_model_error(self):
        plan = llm.ModelPlan('bozuk-model', 16384, True, '')
        with self.assertRaises(llm.ModelError) as error:
            self.client.chat(plan, [{'role': 'user', 'content': 'x'}], lambda: False)
        self.assertIn('HTTP 500', str(error.exception))
        self.assertIn('CUDA error', str(error.exception))

    def test_cpu_plan_disables_gpu_layers(self):
        plan = llm.ModelPlan('qwen3.5:4b', 8192, False, '')
        self.client.chat(plan, [{'role': 'user', 'content': 'x'}], lambda: False)
        self.assertEqual(FakeOllama.requests[-1][1]['options']['num_gpu'], 0)

    def test_cancel_stops_stream_quickly(self):
        FakeOllama.slow = True
        plan = llm.ModelPlan('qwen3.5:9b', 16384, True, '')
        started = time.monotonic()
        deadline = started + 0.8
        with self.assertRaises(llm.Cancelled):
            self.client.chat(plan, [{'role': 'user', 'content': 'x'}], lambda: time.monotonic() > deadline)
        self.assertLess(time.monotonic() - started, 3)

    def test_prepare_downloads_missing_model_with_progress(self):
        messages = []
        plan = llm.prepare(self.client, Hardware(16000, 4000, 11900, True), False, messages.append, lambda: False)
        self.assertEqual(plan.name, 'qwen3.5:9b')
        self.assertEqual(FakeOllama.requests[-1], ('/api/pull', {'model': 'qwen3.5:9b', 'stream': True}))
        self.assertTrue(any('1.0 / 2.0 GB' in m for m in messages))

    def test_stalled_download_is_restarted(self):
        FakeOllama.stall_once = True
        messages = []
        self.client.pull('qwen3.5:9b', messages.append, lambda: False, stall_seconds=0.5)
        pulls = [r for r in FakeOllama.requests if r[0] == '/api/pull']
        self.assertEqual(len(pulls), 2)
        self.assertTrue(any('bağlantı yenileniyor' in m for m in messages))

    def test_vram_held_by_our_previous_job_counts_as_free(self):
        # Gerçek olay: önceki işten 9B bellekte kaldı (≈5,9 GB) → boş VRAM ~5 GB → 4,45 token/sn CPU planı.
        FakeOllama.installed = ['qwen3.5:9b']
        FakeOllama.loaded = [{'name': 'qwen3.5:9b', 'size_vram': 5862 * 1048576}]
        try:
            plan = llm.prepare(self.client, Hardware(16000, 1500, 5100, True), True, lambda m: None, lambda: False)
        finally:
            FakeOllama.installed, FakeOllama.loaded = ['qwen3.5:4b'], []
        self.assertEqual((plan.name, plan.gpu, plan.num_ctx), ('qwen3.5:9b', True, 24576))

    def test_offline_never_downloads(self):
        plan = llm.prepare(self.client, Hardware(16000, 4000, 11900, True), True, lambda m: None, lambda: False)
        self.assertEqual(plan.name, 'qwen3.5:4b')
        self.assertFalse(any(path == '/api/pull' for path, _ in FakeOllama.requests))

    def test_missing_engine_gives_clear_message(self):
        client = llm.OllamaClient(host='127.0.0.1:9', executable='yok/ollama.exe')
        with self.assertRaises(llm.ModelError) as error:
            client.ensure_running(lambda m: None, lambda: False)
        self.assertIn('kurulu değil', str(error.exception))

class EngineInstallTests(unittest.TestCase):
    def package(self, folder, members):
        import hashlib
        import zipfile
        from pathlib import Path
        archive = Path(folder) / 'kaynak' / 'ollama-windows-amd64.zip'
        archive.parent.mkdir()
        with zipfile.ZipFile(archive, 'w') as z:
            for name, data in members.items():
                z.writestr(name, data)
        return archive.as_uri(), hashlib.sha256(archive.read_bytes()).hexdigest()

    def test_verified_package_is_extracted_into_project_runtime(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder:
            url, digest = self.package(folder, {'ollama.exe': b'exe', 'lib/x.dll': b'dll'})
            target = Path(folder) / '.runtime' / 'ollama'
            llm.install_engine(target, lambda m: None, lambda: False, url, digest)
            self.assertEqual((target / 'ollama.exe').read_bytes(), b'exe')
            self.assertFalse((target.parent / 'indirme' / 'ollama-windows-amd64.zip').exists())

    def test_wrong_checksum_is_rejected_and_deleted(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder:
            url, _ = self.package(folder, {'ollama.exe': b'exe'})
            target = Path(folder) / '.runtime' / 'ollama'
            with self.assertRaises(llm.ModelError):
                llm.install_engine(target, lambda m: None, lambda: False, url, '0' * 64)
            self.assertFalse(target.exists())
            self.assertFalse((target.parent / 'indirme' / 'ollama-windows-amd64.zip').exists())

    def test_path_traversal_in_package_is_blocked(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder:
            url, digest = self.package(folder, {'ollama.exe': b'exe', '../../kacak.txt': b'x'})
            target = Path(folder) / '.runtime' / 'ollama'
            with self.assertRaises(llm.ModelError):
                llm.install_engine(target, lambda m: None, lambda: False, url, digest)
            self.assertFalse((Path(folder) / 'kacak.txt').exists())

if __name__ == '__main__':
    unittest.main()
