"""İnternet araştırması testleri. Ağ kullanılmaz; MediaWiki yanıtları sahte fonksiyonla verilir."""
import unittest
import research

LESSON = 'Gradyan inişi (gradient descent) kayıp fonksiyonunu minimize eden iteratif optimizasyon yöntemidir.'

def fake_wiki(pages, calls=None, fail=False):
    """pages: {(lang, başlık): metin}. Arama, başlıkta sorgu geçen sayfaları döndürür."""
    def get(url, params):
        lang = url.split('//')[1].split('.')[0]
        if calls is not None:
            calls.append((lang, dict(params)))
        if fail:
            raise research.ResearchError('bağlantı kurulamadı')
        if params.get('list') == 'search':
            query = params['srsearch'].casefold()
            hits = [t for (l, t) in pages if l == lang and (query in t.casefold() or t.casefold() in query)]
            return {'query': {'search': [{'title': t} for t in hits] or [{'title': 'Derin öğrenme'}]}}
        title = params['titles']
        if (lang, title) not in pages:
            return {'query': {'pages': [{'title': title, 'missing': True}]}}
        text = pages[(lang, title)]
        props = {'disambiguation': ''} if 'şu anlamlara gelebilir' in text else {}
        return {'query': {'pages': [{'title': title, 'fullurl': f'https://{lang}.wikipedia.org/wiki/{title.replace(" ", "_")}',
                                     'extract': text, 'pageprops': props}]}}
    return get

class ResearchTests(unittest.TestCase):
    def test_queries_come_only_from_terms_without_numbers(self):
        queries = research.term_queries(['Gradyan İnişi (Gradient Descent)', 'Delta (Δ)', 'Ahmet 2024 notu',
                                         'çok uzun bir terim adı burada yedi sözcük var'])
        self.assertEqual(queries, [[('tr', 'Gradyan İnişi'), ('en', 'Gradient Descent')], [('tr', 'Delta')]])

    def test_turkish_missing_falls_back_to_english_and_records_queries(self):
        calls = []
        get = fake_wiki({('en', 'Gradient descent'): 'Gradient descent is an iterative optimization method that '
                                                     'minimizes a loss function.\n\nReferences\nxyz'}, calls)
        pages, queries, problems = research.research(['Gradyan İnişi (Gradient Descent)'], LESSON, lambda: False,
                                                     lambda m: None, get=get, pause=0)
        self.assertEqual([(p.lang, p.title) for p in pages], [('en', 'Gradient descent')])
        self.assertNotIn('References', pages[0].text)
        self.assertEqual(pages[0].license, 'CC BY-SA 4.0')
        self.assertEqual(queries, ['Gradyan İnişi (tr.wikipedia.org)', 'Gradient Descent (en.wikipedia.org)'])
        sent = ' '.join(str(p) for _, p in calls)
        self.assertNotIn('kayıp fonksiyonunu', sent)  # ders metni internete gitmez
        self.assertEqual(problems, [])

    def test_title_inside_longer_term_matches(self):
        # 16.10.2026 uygulama denemesinde model "Taylor Series Approximation" yazdı; sayfa "Taylor series".
        self.assertTrue(research.title_matches('Taylor Series Approximation', 'Taylor series'))
        self.assertTrue(research.title_matches('Gradient Descent', 'Gradient descent'))
        self.assertTrue(research.title_matches('Backpropagation algorithm', 'Backpropagation'))
        self.assertFalse(research.title_matches('Derin öğrenme yöntemleri', 'Öğrenme'))  # tek genel sözcük
        self.assertFalse(research.title_matches('Gradyan inişi', 'Derin öğrenme'))
        self.assertFalse(research.title_matches('Analitik çözüm', 'Analiz'))

    def test_wiki_math_markup_is_collapsed(self):
        raw = ('Eğer seri sıfır merkezli ise (\n  \n    \n        a\n        =\n        0\n      \n    '
               '{\\displaystyle a=0}\n  \n), Taylor serisi Maclaurin serisi olur.')
        text = research.trim(raw)
        self.assertIn('a=0', text)
        self.assertNotIn('displaystyle', text)
        self.assertNotIn('\n=\n', text)
        self.assertIn('Taylor serisi Maclaurin serisi olur.', text)

    def test_unrelated_page_with_same_name_is_rejected(self):
        get = fake_wiki({('tr', 'Delta'): 'Delta, bir nehrin denize döküldüğü yerde oluşan alüvyal yeryüzü şeklidir. '
                                          'Nehir taşıdığı tortuları biriktirir.'})
        pages, _, problems = research.research(['Delta (Δ)'], LESSON, lambda: False, lambda m: None, get=get, pause=0)
        self.assertEqual(pages, [])
        self.assertIn('ilgisiz', problems[0])

    def test_disambiguation_page_is_not_a_source(self):
        # 16.10.2026 gerçek denemede tr "Delta" anlam ayrımı sayfası sözcük filtresinden geçebildi.
        get = fake_wiki({('tr', 'Delta'): 'Delta şu anlamlara gelebilir:\nDelta (harf), Yunan alfabesinin harfi. '
                                          'Gradyan, optimizasyon, fonksiyon, iteratif yöntemler…'})
        pages, _, _ = research.research(['Delta (Δ)'], LESSON, lambda: False, lambda m: None, get=get, pause=0)
        self.assertEqual(pages, [])

    def test_network_failure_returns_quickly_without_pages(self):
        calls = []
        pages, _, problems = research.research(['Gradyan İnişi (Gradient Descent)', 'Taylor Serisi', 'Türev'], LESSON,
                                               lambda: False, lambda m: None, get=fake_wiki({}, calls, fail=True), pause=0)
        self.assertEqual(pages, [])
        self.assertEqual(len(calls), 2)  # iki hatadan sonra durur
        self.assertTrue(all('erişilemedi' in p for p in problems))

    def test_cancel_stops_research(self):
        calls = []
        pages, _, _ = research.research(['Taylor Serisi', 'Türev'], LESSON, lambda: True, lambda m: None,
                                        get=fake_wiki({}, calls), pause=0)
        self.assertEqual((pages, calls), ([], []))

class HttpTests(unittest.TestCase):
    def test_429_waits_and_retries_once(self):
        import io
        import urllib.error
        attempts, waits = [], []
        class Response(io.BytesIO):
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
        def opener(request, timeout):
            attempts.append(request.full_url)
            if len(attempts) == 1:
                raise urllib.error.HTTPError(request.full_url, 429, 'Too Many Requests', {'Retry-After': '3'}, None)
            return Response(b'{"ok": true}')
        data = research.http_get('https://tr.wikipedia.org/w/api.php', {'action': 'query'}, opener=opener, sleep=waits.append)
        self.assertEqual((data, len(attempts), waits), ({'ok': True}, 2, [3.0]))

    def test_second_429_is_reported(self):
        import urllib.error
        def opener(request, timeout):
            raise urllib.error.HTTPError(request.full_url, 429, 'Too Many Requests', {}, None)
        with self.assertRaises(research.ResearchError) as error:
            research.http_get('https://tr.wikipedia.org/w/api.php', {}, opener=opener, sleep=lambda s: None)
        self.assertIn('429', str(error.exception))

if __name__ == '__main__':
    unittest.main()
