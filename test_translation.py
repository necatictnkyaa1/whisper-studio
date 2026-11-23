import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from core import transcribe, render, refine_segment
from translation import ensure_model
from translation import download_package, Cancelled
import io
import hashlib
import urllib.error
import zipfile

class TranslationTests(unittest.TestCase):
    def test_technical_terms_are_protected_only_when_present_in_source(self):
        from unittest.mock import Mock
        from translation import LocalTranslator
        translator = object.__new__(LocalTranslator)
        translator.source, translator.target = 'en', 'tr'
        translator._translate = Mock(return_value='ZXQTERM0ZXQ ve ZXQTERM1ZXQ')
        output = translator.translate('Gradient descent and mean squared error')
        self.assertEqual(output, 'gradyan inişi ve ortalama karesel hata')
        self.assertNotIn('ZXQ', output)

    def test_lost_technical_marker_falls_back_without_leaking_marker(self):
        from unittest.mock import Mock
        from translation import LocalTranslator
        translator = object.__new__(LocalTranslator)
        translator.source, translator.target = 'en', 'tr'
        translator._translate = Mock(side_effect=['lost marker', 'Özgün çeviri'])
        self.assertEqual(translator.translate('Gradient descent'), 'Özgün çeviri')
    def test_partly_corrupted_marker_never_leaks(self):
        from unittest.mock import Mock
        from translation import LocalTranslator
        translator=object.__new__(LocalTranslator)
        translator.source,translator.target='en','tr'
        translator._translate=Mock(side_effect=['ZXQTERM0ZXQ ZXQNTM0ZXQ', 'Gradyan inişi algoritması'])
        self.assertEqual(translator.translate('Gradient descent algorithm'),'Gradyan inişi algoritması')

    def test_english_sentence_is_not_skipped_by_turkish_audio_window(self):
        import numpy as np
        text = 'What was the last topic in the previous session we were told?'
        rows = []
        with patch('faster_whisper.WhisperModel') as whisper, patch('translation.LocalTranslator') as translator, \
             patch('faster_whisper.audio.decode_audio', return_value=np.zeros(90 * 16000, dtype='float32')), \
             patch('recognition.speech_windows', return_value=iter([SimpleNamespace(start=67,end=81,text=text)])):
            engine = whisper.return_value
            engine.transcribe.return_value = (iter([SimpleNamespace(start=67, end=81, text=text)]), SimpleNamespace(language='tr', duration=90))
            engine.detect_language.side_effect = [('tr', .98, []), ('en', .99, [])]
            translator.return_value.translate.return_value = 'Önceki dersin son konusu neydi?'
            transcribe('unused.mp3', 'turbo', None, 'cpu', True, lambda s,p: rows.append(s), lambda _: None, lambda: False, 'tr')
        self.assertTrue(rows[0].translated)
        self.assertEqual(rows[0].source_language, 'en')
    def test_weak_recognition_uses_better_second_pass(self):
        import numpy as np
        from unittest.mock import Mock
        segment = SimpleNamespace(start=0, end=2, text='Gradient Isen', avg_logprob=-2, compression_ratio=1)
        candidate = SimpleNamespace(text='Gradient descent', avg_logprob=-.3, compression_ratio=1)
        engine = Mock()
        engine.transcribe.return_value = (iter([candidate]), None)
        text, weak = refine_segment(engine, np.zeros(32000), segment, 'en', lambda _: None, lambda: False)
        self.assertEqual(text, 'Gradient descent')
        self.assertFalse(weak)
        self.assertEqual(engine.transcribe.call_args.kwargs['beam_size'], 8)

    def test_worse_second_pass_does_not_replace_original(self):
        import numpy as np
        from unittest.mock import Mock
        segment = SimpleNamespace(start=0, end=2, text='Original', avg_logprob=-1.2, compression_ratio=1)
        engine = Mock()
        engine.transcribe.return_value = (iter([SimpleNamespace(text='Worse', avg_logprob=-2, compression_ratio=1)]), None)
        text, _ = refine_segment(engine, np.zeros(32000), segment, 'en', lambda _: None, lambda: False)
        self.assertEqual(text, 'Original')

    def test_unchanged_translation_gets_second_attempt(self):
        from unittest.mock import Mock
        from translation import LocalTranslator
        translator = object.__new__(LocalTranslator)
        translator.tokenizer = Mock()
        translator.tokenizer.encode.return_value = ['a', 'b']
        translator.tokenizer.decode.side_effect = ['This is an English sentence.', 'Bu İngilizce bir cümledir.']
        translator.engine = Mock()
        translator.engine.translate_batch.return_value = [SimpleNamespace(hypotheses=[['a']])]
        translator.cancelled = lambda: False
        translator.prefix = ''
        self.assertEqual(translator.translate('This is an English sentence.'), 'Bu İngilizce bir cümledir.')
        self.assertEqual([call.kwargs['beam_size'] for call in translator.engine.translate_batch.call_args_list], [4, 8])
    def test_http_403_switches_to_next_source(self):
        payload = io.BytesIO()
        with zipfile.ZipFile(payload, 'w') as z:
            z.writestr('model/metadata.json', '{}')
        data = payload.getvalue()
        response = io.BytesIO(data)
        response.headers = {'Content-Length': str(len(data))}
        denied = urllib.error.HTTPError('https://first.invalid', 403, 'Forbidden', {}, None)
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as root:
            archive = Path(root) / 'model.zip'
            with patch('translation.urllib.request.urlopen', side_effect=[denied, response]) as network:
                download_package(['https://first.invalid', 'https://second.invalid'], archive,
                                 lambda _: None, lambda: False, hashlib.sha256(data).hexdigest())
            self.assertEqual(network.call_count, 2)
            self.assertTrue(zipfile.is_zipfile(archive))

    def test_corrupt_download_is_not_accepted(self):
        response = io.BytesIO(b'not a model')
        response.headers = {}
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as root:
            with patch('translation.urllib.request.urlopen', return_value=response):
                with self.assertRaisesRegex(RuntimeError, 'bütünlük'):
                    download_package(['https://example.invalid'], Path(root) / 'model.zip',
                                     lambda _: None, lambda: False, '0' * 64)

    def test_cancelled_download_does_not_try_other_sources(self):
        with patch('translation.urllib.request.urlopen') as network:
            with self.assertRaises(Cancelled):
                download_package(['https://example.invalid'], Path('unused.zip'),
                                 lambda _: None, lambda: True)
            network.assert_not_called()

    def test_offline_missing_model_never_downloads(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as root:
            with patch('translation.urllib.request.urlopen') as network:
                with self.assertRaisesRegex(RuntimeError, 'henüz indirilmemiş'):
                    ensure_model('en', 'tr', True, lambda _: None, lambda: False, root)
                network.assert_not_called()

    def test_unsupported_pair(self):
        with self.assertRaisesRegex(ValueError, 'İngilizce'):
            ensure_model('de', 'tr', False, lambda _: None, lambda: False)

    def test_translation_keeps_original_and_timestamps(self):
        segment = SimpleNamespace(start=2.5, end=7, text=' This is a lecture. ')
        info = SimpleNamespace(language='en', duration=10)
        collected = []
        with patch('faster_whisper.WhisperModel') as whisper, patch('translation.LocalTranslator') as translator:
            whisper.return_value.transcribe.return_value = (iter([segment]), info)
            translator.return_value.translate.return_value = 'Bu bir ders.'
            transcribe('unused.wav', 'tiny', 'en', 'cpu', True,
                       lambda s, p: collected.append(s), lambda _: None, lambda: False, 'tr')
        self.assertEqual(collected[0].original, 'This is a lecture.')
        self.assertEqual(collected[0].text, 'Bu bir ders.')
        self.assertIn('00:00:02,500 --> 00:00:07,000\nBu bir ders.', render(collected, True))

    def test_same_language_needs_no_translation_model(self):
        with patch('faster_whisper.WhisperModel') as whisper, patch('translation.LocalTranslator') as translator:
            whisper.return_value.transcribe.return_value = (iter([]), SimpleNamespace(language='tr', duration=1))
            transcribe('unused.wav', 'tiny', 'tr', 'cpu', True, lambda s, p: None, lambda _: None, lambda: False, 'tr')
            translator.assert_not_called()

    def test_turkish_opening_does_not_disable_english_translation(self):
        import numpy as np
        segments = [SimpleNamespace(start=1, end=5, text='Merhaba arkadaşlar.'),
                    SimpleNamespace(start=22, end=28, text='We will study gradient descent today.')]
        collected = []
        with patch('faster_whisper.WhisperModel') as whisper, patch('translation.LocalTranslator') as translator, \
             patch('faster_whisper.audio.decode_audio', return_value=np.zeros(40 * 16000, dtype='float32')), \
             patch('recognition.speech_windows', return_value=iter(segments)):
            engine = whisper.return_value
            engine.transcribe.return_value = (iter(segments), SimpleNamespace(language='tr', duration=40))
            engine.detect_language.side_effect = [('tr', .98, []), ('en', .99, [])]
            translator.return_value.translate.return_value = 'Bugün gradyan inişini çalışacağız.'
            transcribe('unused.mp3', 'turbo', None, 'cpu', True,
                       lambda s, p: collected.append(s), lambda _: None, lambda: False, 'tr')
            # Pencere çözümlemesi recognition testlerinde ayrıca sınanır.
        self.assertFalse(collected[0].translated)
        self.assertTrue(collected[1].translated)
        self.assertEqual(collected[1].source_language, 'en')
        self.assertIn('gradyan', collected[1].text)

    def test_unchanged_sentence_is_preserved_without_stopping(self):
        collected = []
        with patch('faster_whisper.WhisperModel') as whisper, patch('translation.LocalTranslator') as translator:
            whisper.return_value.transcribe.return_value = (iter([SimpleNamespace(start=0, end=5, text='This is a full English sentence.')]),
                SimpleNamespace(language='en', duration=5))
            translator.return_value.translate.return_value = 'This is a full English sentence.'
            transcribe('unused.mp3', 'turbo', 'en', 'cpu', True, lambda s, p: collected.append(s), lambda _: None, lambda: False, 'tr')
        self.assertEqual(collected[0].text, 'This is a full English sentence.')
        self.assertEqual(collected[0].original, collected[0].text)
        self.assertFalse(collected[0].translated)
        self.assertTrue(collected[0].review)
