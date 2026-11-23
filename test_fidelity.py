"""Kaynak sadakati denetimi. Örnekler 16.10.2026 gerçek denemelerinde görülen durumlardan alındı."""
import tempfile
import unittest
from pathlib import Path
from fidelity import check_example, expressions, numbers
from sources import SourceLibrary

# 13.10.2026 dersinin transkriptinden kısa, anonim bir alıntı (öğrenci adları yok).
LECTURE = ('Bir değer seçelim, bu belki de akıllı bir tahmindir. 1,5 olduğunu söyleyelim. Bu işlevi x kez x '
           'tanımında işleve koyun. Sonra biraz azaltmalıyız. Örneğin, buraya 1.4 koyduğumuzda hata 0.04. '
           'Dört retangül kullanmak yerine, 100 retangül tanımlamak istiyorsam hata daha az olur.')

class FidelityTests(unittest.TestCase):
    def library(self, text, kind='transkript'):
        folder = tempfile.mkdtemp()
        path = Path(folder) / 'ders.txt'
        path.write_text(text, encoding='utf-8')
        library = SourceLibrary()
        library.add_text(path, kind=kind)
        return library

    def test_changed_setup_from_real_lecture_is_adapted_not_sourced(self):
        library = self.library(LECTURE)
        example = {'soru': 'x² - 4 = 0 denkleminin köklerini sayısal yöntemle bulunuz.',
                   'cozum': 'x₀ = 1.5 ile başlayalım.', 'dayanak': 'kaynakta', 'kaynaklar': ['P1']}
        label, note, auto = check_example(example, library.passages, library.passages)
        self.assertEqual(label, 'uyarlanmis')
        self.assertIn('x² - 4 = 0', note)
        self.assertIsNone(auto)

    def test_integral_example_with_invented_function_is_adapted(self):
        library = self.library(LECTURE)
        example = {'soru': 'f(x) = x² fonksiyonunun [0, 1] aralığındaki integralini n=4 ile hesaplayınız.',
                   'cozum': '...', 'dayanak': 'kaynakta', 'kaynaklar': ['P1']}
        label, note, _ = check_example(example, library.passages, library.passages)
        self.assertEqual(label, 'uyarlanmis')
        self.assertIn('f(x) = x²', note)

    def test_number_words_in_speech_count_as_source_numbers(self):
        self.assertIn(4.0, numbers('Dört retangül'))
        self.assertIn(0.04, numbers('hata 0.04'))
        self.assertIn(1.5, numbers('1,5 olduğunu'))

    def test_verbatim_pdf_example_gets_automatic_citation(self):
        library = self.library('f(w) = (w − 3)² fonksiyonu. Türevi f′(w) = 2(w − 3). w₀ = 0 ve η = 0,1 olsun.', 'not')
        example = {'soru': "f(w) = (w - 3)² için f'(w) = 2(w - 3), η = 0,1 ile ilk adım?", 'cozum': 'w₁ = 0,6',
                   'dayanak': 'uretilmis', 'kaynaklar': []}
        label, note, auto = check_example(example, [], library.passages)
        self.assertEqual((label, note, auto), ('kaynakta', '', 'P1'))

    def test_conceptual_example_keeps_cited_label_and_uncited_is_generated(self):
        library = self.library('Gradyan inişi yalnızca birinci dereceden bilgiyi kullanır.', 'not')
        example = {'soru': 'Gradyan inişi ile Newton yöntemi farkı nedir?', 'cozum': 'Eğim ve eğrilik.',
                   'dayanak': 'kaynakta', 'kaynaklar': ['P1']}
        self.assertEqual(check_example(example, library.passages, library.passages)[0], 'kaynakta')
        self.assertEqual(check_example(dict(example, kaynaklar=[]), [], library.passages)[0], 'uretilmis')

    def test_expressions_do_not_cross_lines_or_end_with_operator(self):
        text = "f'(w) = 2(w - 3)\n- Başlangıç değeri\nη = 0,1\n2. Adım\nw(t+1) = w(t) −\nnabla"
        self.assertEqual(expressions(text), ["f'(w) = 2(w - 3)", 'η = 0,1', 'w(t+1) = w(t)'])
        # 16.10.2026 uygulama denemesi: "x = 2'deki" Türkçe ekiyle yakalanıyordu.
        self.assertEqual(expressions("f(x) = x² fonksiyonunun x = 2'deki türevi"), ['f(x) = x²'])  # "x = 2" çok kısa
        self.assertEqual(expressions("Noktası x = 2,5'tir ve y = 3x + 1'dir."), ['x = 2,5', 'y = 3x + 1'])

if __name__ == '__main__':
    unittest.main()
