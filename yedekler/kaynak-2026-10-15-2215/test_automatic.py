import unittest
from unittest.mock import patch
from automatic import Hardware, Profile, profiles, run_automatic

class AutomaticTests(unittest.TestCase):
    def setUp(self):
        report_writer = patch('automatic.Path.write_text')
        report_writer.start()
        self.addCleanup(report_writer.stop)

    def test_quality_uses_available_not_total_memory(self):
        self.assertEqual(profiles(Hardware(16000, 8000, 12000, True))[0], Profile('large-v3', 'cuda'))
        self.assertEqual(profiles(Hardware(16000, 5000, 6000, True))[0], Profile('turbo', 'cuda'))
        self.assertEqual(profiles(Hardware(16000, 1800, 0, False))[0], Profile('base', 'cpu'))

    def test_resource_failure_tries_next_profile(self):
        calls = []
        def runner(path, model, language, device, *args, **kwargs):
            calls.append((model, device))
            if len(calls) == 1:
                raise RuntimeError('CUDA out of memory')
        with patch('automatic.inspect_hardware', return_value=Hardware(16000, 8000, 12000, True)):
            run_automatic('x', False, lambda s,p: None, lambda s: None, lambda: False, None, runner)
        self.assertEqual(calls, [('large-v3', 'cuda'), ('turbo', 'cuda')])

    def test_partial_result_is_never_restarted(self):
        calls = []
        def runner(path, model, language, device, offline, emit, *args, **kwargs):
            calls.append(model)
            emit(object(), 10)
            raise RuntimeError('CUDA out of memory')
        with patch('automatic.inspect_hardware', return_value=Hardware(16000, 8000, 12000, True)):
            with self.assertRaises(RuntimeError):
                run_automatic('x', False, lambda s,p: None, lambda s: None, lambda: False, None, runner)
        self.assertEqual(len(calls), 1)

    def test_network_failure_does_not_download_multiple_models(self):
        calls = []
        def runner(*args, **kwargs):
            calls.append(1)
            raise RuntimeError('Download unavailable')
        with patch('automatic.inspect_hardware', return_value=Hardware(16000, 8000, 12000, True)):
            with self.assertRaises(RuntimeError):
                run_automatic('x', False, lambda s,p: None, lambda s: None, lambda: False, None, runner)
        self.assertEqual(len(calls), 1)

    def test_offline_uses_best_available_cached_profile(self):
        calls = []
        with patch('automatic.inspect_hardware', return_value=Hardware(16000, 8000, 12000, True)), \
             patch('automatic.cached', side_effect=lambda model: model == 'turbo'):
            run_automatic('x', True, lambda s,p: None, lambda s: None, lambda: False, None,
                          lambda path, model, *args, **kwargs: calls.append(model))
        self.assertEqual(calls, ['turbo'])
