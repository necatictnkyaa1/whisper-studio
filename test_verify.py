"""Doğrulama/düzeltme hattı testleri. Hesap testleri gerçek SymPy alt sürecini kullanır; model sahtedir."""
import json
import re
import unittest
from pathlib import Path
import sympy_worker
import verify

ROOT = Path(__file__).resolve().parent

class CalculationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checker = verify.SympyChecker()

    @classmethod
    def tearDownClass(cls):
        cls.checker.close()

    def c(self, left, right, context, approximate=False):
        return verify.check_calculation(left, right, context, self.checker, approximate)[0]

    def test_counterexample_disproves_identity(self):
        # İlk sürümde tüm sembollere aynı değer verildiği için x - y = 0 "özdeş" çıkabiliyordu.
        self.assertEqual(self.c('x - y', '0', 'x - y = 0 her zaman'), 'celisiyor')

    def test_equal_samples_are_not_a_proof(self):
        # Örnekleme yalnız karşı örnek arar; |x| ile x pozitif örneklerde eşittir ama özdeş değildir.
        self.assertEqual(self.c('Abs(x)', 'x', 'Abs(x) = x'), 'belirsiz')

    def test_symbolic_proof_is_consistent(self):
        self.assertEqual(self.c('x*(x-1)', 'x**2 - x', 'x(x-1) = x² - x'), 'tutarli')
        self.assertEqual(self.c('taylor(1/(1+x), x, 0, 2)', '1 - x + x**2', 'f(x) = 1/(1+x); P(x) = 1 - x + x²'), 'tutarli')
        self.assertEqual(self.c('diff(cos(x), x)', '-sin(x)', "cos(x) türevi -sin(x)"), 'tutarli')

    def test_approximate_claim_uses_written_precision(self):
        context = 'sqrt(2) yaklaşık 1.414, kabaca 1.41, yanlışça 1.42'
        self.assertEqual(self.c('sqrt(2)', '1.414', context, True), 'tutarli')
        self.assertEqual(self.c('sqrt(2)', '1.41', context, True), 'tutarli')
        self.assertEqual(self.c('sqrt(2)', '1.42', context, True), 'celisiyor')  # fark 0.0058 > ±0.005

    def test_exact_claim_is_not_accepted_by_tolerance(self):
        self.assertEqual(self.c('1/3', '1/4', '1/3 ile 1/4 aynıdır'), 'celisiyor')
        self.assertEqual(self.c('1/3', '0.33', '1/3 yaklaşık 0.33', True), 'tutarli')

    def test_decimal_is_exact_unless_explicitly_approximate(self):
        # Ondalık yazılmış olmak yaklaşıklık değildir: 0.1 + 0.2 = 0.4 kesin iddiası yanlıştır.
        self.assertEqual(self.c('0.1 + 0.2', '0.4', 'Toplam: 0.1 + 0.2 = 0.4'), 'celisiyor')
        self.assertEqual(self.c('0.1 + 0.2', '0.3', 'Toplam: 0.1 + 0.2 = 0.3'), 'tutarli')
        self.assertEqual(self.c('sqrt(2)', '1.414', 'sqrt(2) = 1.414'), 'celisiyor')  # kesin yazılmış
        # Model yaklaşık dese bile metinde yaklaşıklık işareti yoksa kesin karşılaştırılır.
        self.assertEqual(self.c('sqrt(2)', '1.414', 'sqrt(2) = 1.414', True), 'celisiyor')
        self.assertEqual(self.c('sqrt(2)', '1.414', 'sqrt(2) ≈ 1.414', True), 'tutarli')

    def test_residual_is_not_distance_to_root(self):
        # 16.10.2026 kullanıcı föyü: f(1.5) = 0.25 köke uzaklık değildir.
        context = 'x² = 2, x₀ = 1.5, f(1.5) = 0.25; sonuç tahminin gerçek değerden (sqrt(2)) ne kadar yüksek olduğunu gösterir.'
        self.assertEqual(self.c('1.5 - sqrt(2)', '0.25', context), 'celisiyor')
        self.assertEqual(self.c('1.5**2 - 2', '0.25', context), 'tutarli')

    def test_invented_check_cannot_validate_sentence(self):
        # Model asıl hesap yerine "2+2=4" yazarsa yanlış cümle temiz sayılmamalı.
        self.assertEqual(self.c('2+2', '4', 'Toplam 4 olur; hata 0.25'), 'belirsiz')
        self.assertEqual(self.c('7*3', '21', 'Sonuç 21'), 'belirsiz')  # 7 ve 3 metinde yok
        self.assertEqual(self.c('sqrt(2)', '1.414', 'Hata 0.25'), 'belirsiz')  # iddia metinde yok

    def test_unsafe_or_huge_input_is_rejected_without_eval(self):
        for expression in ('__import__("os").system("x")', 'x.__class__', '(lambda: 1)()', '[1 for _ in x]',
                           'open("a")', '10**10**10', 'factorial(100000)', 'x' + '+x' * 300):
            state, _ = sympy_worker.compare(expression, '1')
            self.assertEqual(state, 'belirsiz', expression)
        source = (ROOT / 'sympy_worker.py').read_text(encoding='utf-8')
        code = '\n'.join(line for line in source.splitlines() if not line.lstrip().startswith(('#', '"""', 'Güvenlik')))
        for forbidden in ('eval(', 'exec(', 'sympify(', 'parse_expr('):
            self.assertNotIn(forbidden, code)

    def test_blocking_calculation_is_killed_and_worker_restarts(self):
        checker = verify.SympyChecker(timeout=0.05)
        try:
            self.assertEqual(checker.check('1', '1')[0], 'tutarli')
            state, detail = checker.check('integrate(sin(x)**9*cos(x)**7*exp(x), x)', '0')
            self.assertEqual(state, 'belirsiz')
            self.assertIn('süre sınırını', detail)
            checker.timeout = 5
            self.assertEqual(checker.check('3+2', '5')[0], 'tutarli')
            self.assertEqual(checker.restarts, 1)
        finally:
            checker.close()

class FakeEvidence:
    def __init__(self, passages):
        self.passages_by_term, self.budget, self.errors = passages, None, []
        self.queries = []
    def passages(self, query, terms, k=3):
        self.queries.append((query, list(terms)))
        return [p for t in terms for p in self.passages_by_term.get(t, [])][:k]

class FakeModel:
    """Biçimlendirme/yargı/düzeltme yanıtlarını betikten verir; bütün istemleri kaydeder."""
    def __init__(self, specs, verdicts, fixes):
        self.specs, self.verdicts, self.fixes, self.prompts, self.schemas = specs, verdicts, fixes, [], []
    def generate(self, messages, schema, temperature, max_tokens, **kw):
        prompt = messages[-1]['content']
        self.prompts.append(prompt)
        self.schemas.append(schema)
        if schema is verify.FORMAL_SCHEMA:
            ids = [line.split(']')[0].strip('[ ') for line in prompt.splitlines() if line.startswith('[')]
            return json.dumps({'birimler': [dict(self.specs[i], id=i) for i in ids if i in self.specs]}), {}
        if schema is verify.JUDGE_SCHEMA:
            for key, verdict in self.verdicts.items():
                if key in prompt:
                    if 'kanit_ids' in verdict:
                        return json.dumps(verdict), {}
                    # Eski senaryoların sabit alıntısını yeni kimlik sözleşmesine taşır.
                    # Kaynakta olmayan alıntı için kimlik UYDURMAZ.
                    lines = re.findall(r'^\[(K\d+C\d+)\] \(kaynak: [^\n]*?\) (.+)$', prompt, re.M)
                    quote = verify.strip_quote_prefix(verdict.get('kanit', ''),
                        [{'title': title} for title in re.findall(r'\(kaynak: ([^\n]*?)\)', prompt)])
                    pieces = [verify.squash(q) for q in quote.split('\n') if q.strip()]
                    selected = []
                    for piece in pieces:
                        matches = [identity for identity, text in lines if piece in verify.squash(text)]
                        if not matches:
                            selected = []
                            break
                        # Zamirle başlayan eski alıntılarda özne artık açık bir cümle seçimi olmalı.
                        if piece.startswith(('it ', 'this ', 'they ')):
                            for identity in matches:
                                previous = identity.split('C')[0] + 'C1'
                                if any(key == previous for key, _ in lines):
                                    selected.append(previous)
                        selected.extend(matches)
                    return json.dumps(dict(verdict, kanit_ids=list(dict.fromkeys(selected)))), {}
            return json.dumps({'kontrol': '', 'karar': 'yetersiz', 'kanit_ids': []}), {}
        for key, fixed in self.fixes.items():
            if key in prompt:
                return json.dumps({'duzeltilmis': fixed, 'degisiklik': 'kanıta göre düzeltildi'}), {}
        return json.dumps({'duzeltilmis': '', 'degisiklik': ''}), {}

GD = 'Gradient descent is a first-order iterative algorithm. It uses only the gradient, not the Hessian.'
NEWTON = "Newton's method uses the Hessian matrix of second derivatives."

class EvidenceSelectionTests(unittest.TestCase):
    def judge(self, response, text='Binary search requires sorted input. Binary search halves the search interval.'):
        unit = {'id': 'U1', 'metin': 'İkili arama sıralı girdi gerektirir.', 'baglam': ''}
        spec = {'ingilizce': 'Binary search requires sorted input', 'arama': ['Binary search']}
        evidence = FakeEvidence({'Binary search': [{'title': 'Binary search', 'url': 'https://example.org/binary',
                                                   'text': text}]})
        model = FakeModel({}, {unit['metin']: response}, {})
        verifier = verify.Verifier(model, evidence)
        return verifier.judge(unit, spec), model

    def test_quote_is_constructed_from_source_not_model_prose(self):
        result, model = self.judge({'karar': 'destekleniyor', 'kontrol': 'sıralı girdi',
                                   'kanit_ids': ['K1C1'], 'kanit': 'Completely invented quotation ...'})
        self.assertEqual(result['karar'], 'destekleniyor')
        self.assertEqual(result['kanit'], 'Binary search requires sorted input.')
        self.assertEqual(result['kanit_ids'], ['K1C1'])
        self.assertEqual(result['kanit_kaynaklari'], ['https://example.org/binary'])
        self.assertIn('[K1C1]', model.prompts[0])

    def test_unknown_mixed_or_malformed_ids_reject_entire_selection(self):
        for ids in (['K9C1'], ['K1C1', 'K9C1'], 'K1C1', [True], [], ['K1C1'] * 9):
            with self.subTest(ids=ids):
                result, _ = self.judge({'karar': 'destekleniyor', 'kontrol': '', 'kanit_ids': ids})
                self.assertEqual(result['karar'], 'yetersiz')
                self.assertEqual(result['kaynak'], '')

    def test_existing_but_irrelevant_sentence_is_not_accepted(self):
        result, _ = self.judge({'karar': 'destekleniyor', 'kontrol': '', 'kanit_ids': ['K1C2']})
        self.assertEqual(result['karar'], 'yetersiz')
        self.assertIn('ilgisiz', result['neden'])

    def test_relevant_page_does_not_launder_an_unrelated_page(self):
        passages = {'Binary search': [
            {'title': 'Binary search', 'url': 'https://example.org/binary',
             'text': 'Binary search requires sorted input.'},
            {'title': 'Unrelated', 'url': 'https://example.org/other',
             'text': 'This sorted input belongs to another unrelated method.'}]}
        unit = {'id': 'U', 'metin': 'İkili arama sıralı girdi gerektirir.'}
        model = FakeModel({}, {unit['metin']: {'karar': 'destekleniyor', 'kontrol': '',
                                              'kanit_ids': ['K1C1', 'K2C1']}}, {})
        result = verify.Verifier(model, FakeEvidence(passages)).judge(
            unit, {'ingilizce': 'Binary search requires sorted input', 'arama': ['Binary search']})
        self.assertEqual(result['karar'], 'yetersiz')
        self.assertEqual(result['kaynak'], '')

    def test_no_selection_cannot_be_rescued_by_free_quote(self):
        class OldContractModel:
            def generate(self, *args, **kwargs):
                return json.dumps({'karar': 'destekleniyor', 'kontrol': '',
                                   'kanit': 'Binary search requires sorted input.'}), {}
        evidence = FakeEvidence({'Binary search': [{'title': 'Binary search', 'url': 'https://example.org/binary',
                                                   'text': 'Binary search requires sorted input.'}]})
        verifier = verify.Verifier(OldContractModel(), evidence)
        result = verifier.judge({'id': 'U', 'metin': 'İkili arama sıralı girdi gerektirir.'},
                               {'ingilizce': 'Binary search requires sorted input', 'arama': ['Binary search']})
        self.assertEqual(result['karar'], 'yetersiz')

    def test_sentence_units_preserve_decimal_and_source_boundaries(self):
        units = verify.evidence_units([{'title': 'Ölçüm', 'url': 'https://example.org/a',
                                       'text': 'The measured value is 1.25. This is a second sentence.'},
                                      {'title': 'Diğer', 'url': 'https://example.org/b', 'text': 'Başka kaynak.'}])
        self.assertEqual(units['K1C1']['text'], 'The measured value is 1.25.')
        self.assertEqual(units['K2C1']['url'], 'https://example.org/b')
        selected = verify.selected_evidence(['K1C1', 'K1C1', 'K2C1'], units)
        self.assertEqual([key for key, _ in selected], ['K1C1', 'K2C1'])


class PipelineTests(unittest.TestCase):
    def run_units(self, units, specs, verdicts, fixes, evidence, budget=None):
        model = FakeModel(specs, verdicts, fixes)
        verifier = verify.Verifier(model, FakeEvidence(evidence), budget=budget)
        return verifier.run(units), model, verifier

    def test_gold_fields_never_reach_model(self):
        fixture = json.loads((ROOT / 'ornekler' / 'dogrulama' / 'fixture-2026-10-16.json').read_text(encoding='utf-8'))
        units = fixture['birimler']
        specs = {u['id']: {'olgu_var': True, 'ingilizce': u['metin'], 'arama': ['x'], 'hesaplar': []} for u in units}
        _, model, _ = self.run_units(units, specs, {}, {}, {})
        sent = '\n'.join(model.prompts)
        for unit in units:
            if unit['not']:
                self.assertNotIn(unit['not'], sent)
            for source in unit['kaynaklar']:
                self.assertNotIn(source, sent)
        self.assertNotIn('"altin"', sent)
        self.assertNotIn('altin', sent.casefold().replace('altında', ''))

    def test_insufficient_evidence_keeps_sentence(self):
        # Vikipedi'de bulamamak yanlışlık kanıtı değildir: doğru pedagojik içerik silinmez.
        units = [{'id': 'U1', 'metin': 'Epsilon, iteratif süreçlerde durma ölçütü olarak kullanılan küçük bir sayıdır.',
                  'baglam': '', 'kaynaklar': ['Ders kaydı 01:00']}]
        specs = {'U1': {'olgu_var': True, 'ingilizce': 'epsilon stopping criterion', 'arama': ['Epsilon'], 'hesaplar': []}}
        results, _, _ = self.run_units(units, specs, {}, {}, {})
        self.assertEqual(results[0]['durum'], 'kanit_yetersiz')
        self.assertEqual(results[0]['son_metin'], units[0]['metin'])

    def test_contradicted_claim_is_fixed_and_cites_new_evidence_not_old_transcript(self):
        wrong = 'Gradient descent, gradient ve Hessian yöntemlerini kullanır.'
        fixed = 'Gradient descent yalnız gradyanı kullanır; Hessian Newton yönteminde kullanılır.'
        units = [{'id': 'U1', 'metin': wrong, 'baglam': '', 'kaynaklar': ['Ders kaydı 15:10–17:49']}]
        specs = {'U1': {'olgu_var': True, 'ingilizce': 'GD uses gradient and Hessian', 'arama': ['Gradient descent'],
                        'hesaplar': []}}
        verdicts = {wrong: {'kontrol': 'kanıt yalnız gradyan diyor', 'karar': 'celisiyor', 'kanit': 'It uses only the gradient, not the Hessian.'},
                    fixed: {'kontrol': 'uyumlu', 'karar': 'destekleniyor', 'kanit': 'It uses only the gradient, not the Hessian.'}}
        evidence = {'Gradient descent': [{'title': 'Gradient descent', 'url': 'https://en.wikipedia.org/wiki/Gradient_descent', 'text': GD}]}
        results, _, _ = self.run_units(units, specs, verdicts, {wrong: fixed}, evidence)
        record = results[0]
        self.assertEqual((record['durum'], record['son_metin'], record['orijinal']), ('duzeltildi', fixed, wrong))
        self.assertEqual(record['ders_kaynagi'], ['Ders kaydı 15:10–17:49'])  # özgün ifadenin kaynağı ayrı
        self.assertTrue(record['duzeltme_kaynagi'])
        self.assertTrue(all('wikipedia.org' in s for s in record['duzeltme_kaynagi']))

    def test_fix_that_fails_reverification_is_not_reported_as_success(self):
        wrong = 'Gradient descent Hessian kullanır.'
        bad_fix = 'Gradient descent her zaman Hessian ile çalışır.'
        units = [{'id': 'U1', 'metin': wrong, 'baglam': '', 'kaynaklar': []}]
        specs = {'U1': {'olgu_var': True, 'ingilizce': 'GD uses Hessian', 'arama': ['Gradient descent'], 'hesaplar': []}}
        contradiction = {'kontrol': '', 'karar': 'celisiyor', 'kanit': 'It uses only the gradient, not the Hessian.'}
        evidence = {'Gradient descent': [{'title': 'GD', 'url': 'https://en.wikipedia.org/wiki/Gradient_descent', 'text': GD}]}
        results, _, _ = self.run_units(units, specs, {wrong: contradiction, bad_fix: contradiction}, {wrong: bad_fix}, evidence)
        self.assertEqual(results[0]['durum'], 'cozulemedi')
        self.assertIsNone(results[0]['son_metin'])
        self.assertEqual(results[0]['duzeltme'], bad_fix)  # başarısız düzeltme saklanmaz, kayıtta görünür

    def test_judgement_without_verbatim_quote_is_insufficient(self):
        units = [{'id': 'U1', 'metin': 'Newton yöntemi Hessian kullanır.', 'baglam': '', 'kaynaklar': []}]
        specs = {'U1': {'olgu_var': True, 'ingilizce': 'Newton uses Hessian', 'arama': ['Newton'], 'hesaplar': []}}
        verdicts = {'Newton yöntemi': {'kontrol': '', 'karar': 'celisiyor', 'kanit': 'Newton never uses any matrix.'}}
        evidence = {'Newton': [{'title': 'Newton', 'url': 'https://en.wikipedia.org/wiki/Newton%27s_method', 'text': NEWTON}]}
        results, _, _ = self.run_units(units, specs, verdicts, {}, evidence)
        self.assertEqual(results[0]['durum'], 'kanit_yetersiz')  # uydurma alıntıyla çelişki ilan edilemez
        self.assertEqual(results[0]['son_metin'], units[0]['metin'])

    def test_calculation_error_is_fixed_with_sympy_as_source(self):
        context = 'x² = 2, x₀ = 1.5, f(1.5) = 0.25.'
        wrong = 'Bu sonuç, tahminimizin gerçek değerden (sqrt(2)) ne kadar yüksek olduğunu gösterir.'
        fixed = 'Bu sonuç bir artıktır; tahminin sqrt(2) değerinden farkı 1.5 - sqrt(2) ≈ 0.086 olur.'
        units = [{'id': 'U1', 'metin': wrong, 'baglam': context, 'kaynaklar': []}]
        specs = {'U1': {'olgu_var': False, 'ingilizce': '', 'arama': [],
                        'hesaplar': [{'sol': '1.5 - sqrt(2)', 'sag': '0.25', 'anlam': 'tahminin köke uzaklığı', 'yaklasik': False}]}}
        class Model(FakeModel):
            def generate(self, messages, schema, temperature, max_tokens, **kw):
                if schema is verify.FORMAL_SCHEMA and fixed in messages[-1]['content']:
                    # Düzeltilmiş cümlenin "artıktır" yorumu da denetlenmeli (yalnız uzaklık hesabı yetmez).
                    return json.dumps({'birimler': [{'id': 'U1', 'olgu_var': False, 'ingilizce': '', 'arama': [],
                                                     'hesaplar': [{'sol': '1.5 - sqrt(2)', 'sag': '0.086', 'anlam': 'uzaklık', 'yaklasik': True}],
                                                     'yorumlar': [{'tur': 'artik', 'deger': '0.25', 'tahmin': '1.5',
                                                                   'fonksiyon': 'x**2 - 2', 'degisken': 'x'}]}]}), {}
                return super().generate(messages, schema, temperature, max_tokens)
        verifier = verify.Verifier(Model(specs, {}, {wrong: fixed}), FakeEvidence({}))
        record = verifier.run(units)[0]
        self.assertEqual(record['durum'], 'duzeltildi')
        self.assertTrue(record['duzeltme_kaynagi'][0].startswith('SymPy hesabı'))

    def test_calculations_alone_never_mark_sentence_verified(self):
        # 16.10.2026 gerçek deneme: Y4'te bağlamdaki doğru hesaplar yanlış yorum cümlesini "doğrulandı" yaptırdı.
        units = [{'id': 'Y4', 'metin': 'Bu sonuç, tahminin gerçek değerden (sqrt(2) yaklaşık 1.414) ne kadar yüksek olduğunu gösterir.',
                  'baglam': 'x₀ = 1.5; f(1.5) = (1.5)² - 2 = 0.25.', 'kaynaklar': []}]
        specs = {'Y4': {'olgu_var': False, 'ingilizce': '', 'arama': [],
                        'hesaplar': [{'iddia': 'f(1.5)=0.25', 'sol': '(1.5)**2 - 2', 'sag': '0.25', 'anlam': '', 'yaklasik': False},
                                     {'iddia': 'kök 2', 'sol': 'sqrt(2)', 'sag': '1.414', 'anlam': '', 'yaklasik': True}]}}
        results, _, _ = self.run_units(units, specs, {}, {}, {})
        # Bağlam hesabının tekrarı ve parantezdeki sqrt(2) cümlenin yorumunu aklayamaz: ne "doğrulandı"
        # ne "hesap_tutarli"; cümle korunur ama onaylanmış sayılmaz.
        self.assertEqual(results[0]['durum'], 'yorum_denetlenemedi')
        self.assertEqual(results[0]['son_metin'], units[0]['metin'])

    def test_multi_line_quote_must_match_piece_by_piece(self):
        units = [{'id': 'U1', 'metin': 'Gradient descent Hessian kullanır.', 'baglam': '', 'kaynaklar': []}]
        specs = {'U1': {'olgu_var': True, 'ingilizce': 'GD uses Hessian', 'arama': ['Gradient descent'], 'hesaplar': []}}
        evidence = {'Gradient descent': [{'title': 'Gradient descent', 'url': 'https://en.wikipedia.org/wiki/Gradient_descent', 'text': GD}]}
        good = {'Gradient descent Hessian': {'kontrol': '', 'karar': 'celisiyor',
                'kanit': 'Gradient descent: Gradient descent is a first-order iterative algorithm.\nIt uses only the gradient, not the Hessian.'}}
        results, _, _ = self.run_units(units, specs, good, {}, evidence, verify.Budget(düzeltme=0))
        self.assertEqual(results[0]['durum'], 'cozulemedi')  # çelişki kabul edildi (düzeltme bütçesi yok)
        bad = {'Gradient descent Hessian': {'kontrol': '', 'karar': 'celisiyor',
               'kanit': 'Gradient descent is a first-order iterative algorithm.\nIt never uses derivatives at all.'}}
        results, _, _ = self.run_units(units, specs, bad, {}, evidence, verify.Budget(düzeltme=0))
        self.assertEqual(results[0]['durum'], 'kanit_yetersiz')  # uydurma parça → alıntı reddedildi

    def test_subs_function_is_allowed_but_method_call_is_not(self):
        import sympy_worker
        self.assertEqual(sympy_worker.compare('subs(diff(1/(1+x), x), x, 0)', '-1')[0], 'tutarli')
        self.assertEqual(sympy_worker.compare('diff(1/(1+x), x).subs(x, 0)', '-1')[0], 'belirsiz')

    def test_unit_limit_leaves_rest_unchecked_but_unchanged(self):
        units = [{'id': f'U{i}', 'metin': f'Cümle {i}.', 'baglam': '', 'kaynaklar': []} for i in range(5)]
        specs = {u['id']: {'olgu_var': False, 'ingilizce': '', 'arama': [], 'hesaplar': []} for u in units}
        results, _, _ = self.run_units(units, specs, {}, {}, {}, verify.Budget(max_units=3))
        self.assertEqual([r['durum'] for r in results], ['kontrol_disi'] * 3 + ['denetlenmedi'] * 2)
        self.assertTrue(all(r['son_metin'] == r['orijinal'] for r in results))

    def test_exhausted_judge_budget_still_runs_calculations_and_later_units(self):
        # İlk rapordaki kusur: web/çağrı bütçesi bitince hesaplar ve kalan maddeler atlanıyordu.
        context = 'x² = 2, x₀ = 1.5, f(1.5) = 0.25.'
        units = [{'id': 'F1', 'metin': 'Gradient descent Hessian kullanır.', 'baglam': '', 'kaynaklar': []},
                 {'id': 'F2', 'metin': 'Bu sonuç tahminin sqrt(2) değerinden ne kadar yüksek olduğunu gösterir.',
                  'baglam': context, 'kaynaklar': []},
                 {'id': 'F3', 'metin': 'f(1.5) = 0.25 bulunur.', 'baglam': context, 'kaynaklar': []}]
        specs = {'F1': {'olgu_var': True, 'ingilizce': 'GD uses Hessian', 'arama': ['Gradient descent'], 'hesaplar': []},
                 'F2': {'olgu_var': False, 'ingilizce': '', 'arama': [],
                        'hesaplar': [{'sol': '1.5 - sqrt(2)', 'sag': '0.25', 'anlam': 'uzaklık', 'yaklasik': False}]},
                 'F3': {'olgu_var': False, 'ingilizce': '', 'arama': [],
                        'hesaplar': [{'sol': '1.5**2 - 2', 'sag': '0.25', 'anlam': 'artık', 'yaklasik': False}]}}
        evidence = {'Gradient descent': [{'title': 'GD', 'url': 'https://en.wikipedia.org/wiki/Gradient_descent', 'text': GD}]}
        budget = verify.Budget(kanıt_yargısı=0, düzeltme=0)
        results, _, _ = self.run_units(units, specs, {}, {}, evidence, budget)
        by_id = {r['id']: r for r in results}
        self.assertEqual(by_id['F1']['durum'], 'kanit_yetersiz')
        self.assertIn('bütçesi', by_id['F1']['neden'])
        self.assertEqual(by_id['F1']['son_metin'], units[0]['metin'])  # kanıt yetersizliği içerik silmez
        # Hesap çelişkisi bütçeden bağımsız bulundu; düzeltme bütçesi yok → yanlış cümle sunulmaz, ekte kalır.
        self.assertEqual(by_id['F2']['durum'], 'cozulemedi')
        self.assertIsNone(by_id['F2']['son_metin'])
        self.assertEqual(by_id['F3']['durum'], 'hesap_tutarli')  # yalnız hesap: "doğrulandı" denmez

    def test_web_budget_exhaustion_makes_facts_insufficient_not_skipped(self):
        import tempfile
        calls = []
        def get(url, params):
            calls.append(params)
            if params.get('list') == 'search':
                return {'query': {'search': [{'title': 'Gradient descent'}]}}
            return {'query': {'pages': [{'title': 'Gradient descent', 'fullurl': 'https://en.wikipedia.org/wiki/Gradient_descent',
                                         'extract': GD, 'pageprops': {}}]}}
        with tempfile.TemporaryDirectory() as folder:
            budget = verify.Budget(web=1)
            store = verify.EvidenceStore(folder, get=get, pause=0, budget=budget)
            self.assertEqual(store.passages('gradient Hessian', ['Gradient descent']), [])  # arama yapıldı, sayfa için bütçe yok
            self.assertEqual(len(calls), 1)
            self.assertIn('web bütçesi doldu', store.errors)

    def test_unrelated_search_result_is_not_used_as_evidence(self):
        import tempfile
        def get(url, params):
            if params.get('list') == 'search':
                return {'query': {'search': [{'title': 'Minimum wage in the United States'}]}}
            raise AssertionError('ilgisiz sayfa indirilmemeli')
        with tempfile.TemporaryDirectory() as folder:
            store = verify.EvidenceStore(folder, get=get, pause=0)
            self.assertEqual(store.pages('Local minimum'), [])

    def test_bm25_prefers_claim_relevant_paragraph_over_intro(self):
        intro = 'Gradient descent is a method for unconstrained mathematical optimization in many fields of study today.'
        relevant = "Methods based on Newton's method and inversion of the Hessian can be better alternatives."
        other = 'The learning rate schedule changes the step size during training of neural networks.'
        # İddianın odağı Hessian/Newton ise ilgili paragraf girişin önüne geçer; konu dışı paragraf puan almaz.
        scores = verify.bm25("Newton's method uses the Hessian matrix", [intro, other, relevant])
        self.assertEqual(max(range(3), key=lambda i: scores[i]), 2)
        self.assertEqual(scores[1], 0)
        # İddia genel tanımsa giriş paragrafı da seçilebilir (yalnız girişe bakmak değil, iddiaya göre sıralama).
        scores = verify.bm25('gradient descent unconstrained optimization', [intro, other, relevant])
        self.assertEqual(max(range(3), key=lambda i: scores[i]), 0)

NEWTON_CONTEXT = 'x² = 2 için başlangıç tahmini x₀ = 1.5; f(x) = x² - 2; f(1.5) = (1.5)² - 2 = 2.25 - 2 = 0.25.'
DISTANCE = {'tur': 'fark', 'deger': '0.25', 'tahmin': '1.5', 'gercek': 'sqrt(2)'}
RESIDUAL = {'tur': 'artik', 'deger': '0.25', 'tahmin': '1.5', 'fonksiyon': 'x**2 - 2', 'degisken': 'x'}

def spec(yorumlar=(), hesaplar=(), olgu=False, ingilizce='', arama=()):
    return {'olgu_var': olgu, 'ingilizce': ingilizce, 'arama': list(arama), 'hesaplar': list(hesaplar),
            'yorumlar': list(yorumlar)}

class InterpretationTests(unittest.TestCase):
    """Sayıya yüklenen anlamı kod bulur. Karşı örnekler fixture cümlesinin farklı ifadeleri ve başka sayılardır."""
    def test_meaning_kind_is_found_from_wording_not_from_model(self):
        cases = {
            'Bu sonuç, tahminimizin gerçek değerden (sqrt(2) yaklaşık 1.414) ne kadar yüksek olduğunu gösterir.': {'fark'},
            'Elde edilen 0.25, x₀ tahmininin gerçek kökten uzaklığıdır.': {'fark'},
            'Bu değer, tahminin doğru değerden ne kadar saptığını anlatır.': {'fark'},
            'This result shows how far the estimate is from the true value.': {'fark'},
            'Bu değer, tahminin gerçek değere göre yüzde hatasını verir.': {'goreli_hata'},
            'Bu sonuç bir artıktır (residual); köke uzaklık değildir.': {'artik'},
            'Bu sonuç (0.25) artıktır, tahminin köke uzaklığı ise yaklaşık 0.086 olur.': {'artik', 'fark'},
        }
        for sentence, expected in cases.items():
            self.assertEqual(verify.interpretations(sentence), expected, sentence)

    def test_sentences_without_meaning_claim_need_no_interpretation(self):
        for sentence in ('P(x) = 1 + (-1)x + 2/2x² = 1 - x + x² olur.',
                         "3x = 9 → x = 3 bulunur; 3 + y = 5 → y = 2. Çözüm noktası (3, 2)'dir.",
                         'Backward difference, Taylor serisi genişlemesi kullanılarak elde edilen bir türev yaklaşım yöntemidir.',
                         'Artık x = 3 bulunur.', "2'nin karekökü yaklaşık 1.414'tür.",
                         'İleri fark formülü h = 0.1 adımıyla uygulanır.'):
            self.assertEqual(verify.interpretations(sentence), set(), sentence)

class InterpretationPipelineTests(unittest.TestCase):
    def run_one(self, sentence, unit_spec, context=NEWTON_CONTEXT, fixes=None, budget=None):
        units = [{'id': 'U1', 'metin': sentence, 'baglam': context, 'kaynaklar': []}]
        model = FakeModel({'U1': unit_spec}, {}, fixes or {})
        return verify.Verifier(model, FakeEvidence({}), budget=budget).run(units)[0]

    def test_real_qwen_formalization_of_y4_is_not_accepted(self):
        # 16.10.2026 12:01 gerçek Qwen biçimlendirmesi (ham-kayit.json): yalnız bağlam hesapları, yorum yok.
        sentence = 'Bu sonuç, tahminimizin gerçek değerden (sqrt(2) yaklaşık 1.414) ne kadar yüksek olduğunu gösterir.'
        real = spec(hesaplar=[{'iddia': 'f(1.5) = 0.25', 'sol': '(1.5)**2 - 2', 'sag': '0.25', 'anlam': '', 'yaklasik': False},
                              {'iddia': 'sqrt(2) yaklaşık 1.414', 'sol': 'sqrt(2)', 'sag': '1.414', 'anlam': '', 'yaklasik': True}])
        record = self.run_one(sentence, real)
        self.assertEqual(record['durum'], 'yorum_denetlenemedi')
        self.assertEqual(record['son_metin'], sentence)
        self.assertEqual(record['ilk_kontrol']['hesaplar'][0]['kapsam'], 'baglam')

    def test_wrong_distance_paraphrases_are_contradicted(self):
        # Düzeltme bütçesi sıfır: yorum düzeltmesi modele gitmediği için yine kodla kurulur.
        for sentence in ('Bu sonuç, tahminimizin gerçek değerden (sqrt(2) yaklaşık 1.414) ne kadar yüksek olduğunu gösterir.',
                         'Bu değer, x₀ tahmininin gerçek kökten (sqrt(2)) ne kadar uzak olduğunu gösterir.',
                         'Elde edilen 0.25, tahminin sqrt(2) gerçek değerinden farkıdır.'):
            record = self.run_one(sentence, spec([DISTANCE]), budget=verify.Budget(düzeltme=0))
            self.assertEqual(record['ilk_kontrol']['durum'], 'celisiyor', sentence)
            self.assertEqual(record['durum'], 'duzeltildi', sentence)
            self.assertIn('artıktır', record['son_metin'])
            self.assertNotIn(sentence, record['son_metin'])

    def test_referenced_value_comes_from_context_not_model(self):
        # Model "deger" yuvasına parantezdeki 1.414'ü yazsa da "Bu sonuç" bağlamdaki son sonuç 0.25'tir.
        sentence = 'Bu sonuç, tahminin gerçek değerden (sqrt(2) yaklaşık 1.414) ne kadar uzak olduğunu gösterir.'
        record = self.run_one(sentence, spec([dict(DISTANCE, deger='1.414')]), budget=verify.Budget(düzeltme=0))
        meaning = [c for c in record['ilk_kontrol']['hesaplar'] if c['kapsam'] == 'yorum'][0]
        self.assertEqual(meaning['sag'], '0.25')
        self.assertEqual(meaning['sonuc'][0], 'celisiyor')

    def test_model_cannot_swap_in_an_easier_meaning(self):
        # Cümle uzaklık diyor; model "artık" yuvası doldurursa (bağlamla tutarlı olur) yine onaylanmaz.
        sentence = 'Bu sonuç, tahminin gerçek değerden ne kadar uzak olduğunu gösterir.'
        record = self.run_one(sentence, spec([RESIDUAL]))
        self.assertEqual(record['durum'], 'yorum_denetlenemedi')

    def test_correct_interpretations_are_kept(self):
        self.assertEqual(self.run_one('Bu sonuç, f fonksiyonunun tahmin noktasındaki artığıdır.', spec([RESIDUAL]))['durum'],
                         'hesap_tutarli')
        context = 'x₀ = 1.5 ve gerçek değer sqrt(2) ≈ 1.4142; e = 1.5 - 1.4142 = 0.0858.'
        sentence = 'Bu sonuç, tahminin gerçek değerden ne kadar yüksek olduğunu gösterir.'
        slot = {'tur': 'fark', 'deger': '0.0858', 'tahmin': '1.5', 'gercek': 'sqrt(2)'}
        record = self.run_one(sentence, spec([slot]), context=context)
        self.assertEqual((record['durum'], record['son_metin']), ('hesap_tutarli', sentence))

    def test_other_numbers_same_wrong_reading(self):
        # Fixture dışı: x³ = 5, x₀ = 2, f(2) = 3; 3 köke uzaklık değildir (|2 − 5^(1/3)| ≈ 0.29).
        context = 'x³ = 5 için tahmin x₀ = 2; f(x) = x³ - 5; f(2) = 8 - 5 = 3.'
        sentence = 'Bu değer, tahminin gerçek kökten ne kadar uzak olduğunu gösterir.'
        slot = {'tur': 'fark', 'deger': '3', 'tahmin': '2', 'gercek': '5**(1/3)'}
        record = self.run_one(sentence, spec([slot]), context=context, budget=verify.Budget(düzeltme=0))
        self.assertEqual(record['ilk_kontrol']['durum'], 'celisiyor')
        residual = {'tur': 'artik', 'deger': '3', 'tahmin': '2', 'fonksiyon': 'x**3 - 5', 'degisken': 'x'}
        self.assertEqual(self.run_one('Bu değer, tahmindeki artıktır.', spec([residual]), context=context)['durum'],
                         'hesap_tutarli')

    def test_restated_context_calculation_cannot_validate_unrelated_claim(self):
        record = self.run_one('Bu yöntem her zaman tek adımda köke ulaşır.',
                              spec(hesaplar=[{'iddia': '', 'sol': '(1.5)**2 - 2', 'sag': '0.25', 'anlam': '', 'yaklasik': False}]))
        self.assertEqual(record['durum'], 'kontrol_disi')  # eskiden hesap_tutarli olurdu

    def test_model_fix_is_never_used_for_meaning_contradiction(self):
        # 13:05 gerçek denemede modelin düzeltmesi aynı yanlış anlamı tekrarladı ("ne kadar uzak"). Yorum çelişkisinde
        # model düzeltme yazmaz ve düzeltilmiş cümle modele yeniden biçimlendirilmez; kod şablonu ve aynı yuvalar kullanılır.
        wrong = 'Bu sonuç, tahminin gerçek değerden (sqrt(2)) ne kadar yüksek olduğunu gösterir.'
        repeat = 'Bu sonuç, tahminin gerçek kökten ne kadar uzak olduğunu gösterir.'
        units = [{'id': 'U1', 'metin': wrong, 'baglam': NEWTON_CONTEXT, 'kaynaklar': []}]
        model = FakeModel({'U1': spec([DISTANCE])}, {}, {wrong: repeat})
        record = verify.Verifier(model, FakeEvidence({})).run(units)[0]
        self.assertEqual(record['durum'], 'duzeltildi')
        self.assertNotEqual(record['son_metin'], repeat)
        self.assertEqual(model.schemas, [verify.FORMAL_SCHEMA])  # tek çağrı: ilk biçimlendirme
        self.assertTrue(all(s.startswith('SymPy hesabı') for s in record['duzeltme_kaynagi']))

CUBE_CONTEXT = 'x³ = 5 için tahmin x₀ = 2; f(x) = x³ - 5; f(2) = 8 - 5 = 3.'
CUBE_DISTANCE = {'tur': 'fark', 'deger': '3', 'tahmin': '2', 'gercek': '5**(1/3)'}  # fonksiyon yuvası boş

class MeaningCorrectionTests(unittest.TestCase):
    """Yorum çelişkisinde düzeltmeyi kod kurar. Sayılar ve cümleler fixture dışıdır; model yalnız yuva doldurur."""
    def run_one(self, sentence, slots, context, units_extra=None):
        unit = dict({'id': 'U1', 'metin': sentence, 'baglam': context, 'kaynaklar': []}, **(units_extra or {}))
        model = FakeModel({'U1': spec(slots)}, {}, {sentence: sentence})  # model düzeltmesi sorulsaydı aynı cümleyi verirdi
        verifier = verify.Verifier(model, FakeEvidence({}))
        return verifier.run([unit])[0], model, verifier

    def test_distance_misreading_is_rewritten_as_residual_from_template(self):
        record, model, _ = self.run_one('Bu değer, tahminin gerçek kökten ne kadar uzak olduğunu gösterir.',
                                        [CUBE_DISTANCE], CUBE_CONTEXT)
        self.assertEqual(record['durum'], 'duzeltildi')
        self.assertEqual(record['son_metin'], 'Bu sonuç (3), f(2) değeridir, yani artıktır; tahminin gerçek değerden '
                                              'farkı ise |2 − 5^(1/3)| ≈ 0.290 olur.')
        self.assertEqual(record['anlam_secimi']['secilen'], 'artik')
        self.assertEqual(model.schemas, [verify.FORMAL_SCHEMA])  # düzeltme ve yeniden biçimlendirme modele gitmedi
        self.assertEqual(record['ikinci_kontrol']['durum'], 'hesap_tutarli')

    def test_paraphrases_with_other_numbers_get_the_same_correct_meaning(self):
        context = 'x² = 3 için x₀ = 1.8; f(x) = x² - 3; f(1.8) = 3.24 - 3 = 0.24.'
        slot = {'tur': 'fark', 'deger': '0.24', 'tahmin': '1.8', 'gercek': 'sqrt(3)'}
        for sentence in ('Bu sonuç, x₀ tahmininin gerçek değerden ne kadar saptığını gösterir.',
                         'Elde edilen 0.24, tahminin sqrt(3) kökünden uzaklığıdır.',
                         'This value is the distance of the estimate from the exact root.',
                         'Bulunan değer, tahminimizin doğru değerden ne kadar büyük olduğunu anlatır.'):
            record, model, _ = self.run_one(sentence, [slot], context)
            self.assertEqual(record['durum'], 'duzeltildi', sentence)
            self.assertIn('f(1.8) değeridir, yani artıktır', record['son_metin'])
            self.assertIn('|1.8 − √3| ≈ 0.0679', record['son_metin'])
            self.assertEqual(model.schemas, [verify.FORMAL_SCHEMA])

    def test_negative_residual_from_english_sentence(self):
        record, _, _ = self.run_one('This result shows how far the estimate is from the true value (sqrt(7)).',
                                    [{'tur': 'fark', 'deger': '-0.75', 'tahmin': '2.5', 'gercek': 'sqrt(7)'}],
                                    'x² = 7, x₀ = 2.5; f(x) = x² - 7; f(2.5) = 6.25 - 7 = -0.75.')
        self.assertEqual(record['durum'], 'duzeltildi')
        self.assertTrue(record['son_metin'].startswith('Bu sonuç (-0.75), f(2.5) değeridir, yani artıktır;'))

    def test_relative_error_misreading_is_rewritten_as_difference(self):
        record, _, _ = self.run_one('Bu sonuç, tahminin gerçek değere göre göreli hatasıdır.',
                                    [{'tur': 'goreli_hata', 'deger': '0.2', 'tahmin': '4.2', 'gercek': '4'}],
                                    'Gerçek değer 4, ölçülen tahmin 4.2; e = 4.2 - 4 = 0.2.')
        self.assertEqual(record['durum'], 'duzeltildi')
        self.assertEqual(record['son_metin'], 'Bu sonuç (0.2), tahminin gerçek değerden farkıdır (|4.2 − 4|); tahminin '
                                              'gerçek değere göre göreli hatası ise |4.2 − 4| / |4| ≈ 0.0500 olur.')
        self.assertEqual(verify.interpretations(record['son_metin']), {'fark', 'goreli_hata'})

    def test_no_consistent_meaning_is_honestly_unresolved(self):
        context = 'x² = 3 için x₀ = 1.8; f(x) = x² - 3; bir öğrenci 0.5 buldu.'
        sentence = 'Öğrencinin bulduğu 0.5, tahminin sqrt(3) gerçek değerinden farkıdır.'
        record, model, _ = self.run_one(sentence, [{'tur': 'fark', 'deger': '0.5', 'tahmin': '1.8', 'gercek': 'sqrt(3)'}],
                                        context)
        self.assertEqual((record['durum'], record['son_metin']), ('cozulemedi', None))
        self.assertIn('hiçbiriyle tutarlı değil', record['neden'])
        self.assertNotIn('duzeltme', record)
        self.assertEqual(model.schemas, [verify.FORMAL_SCHEMA])

    def test_two_consistent_meanings_are_not_guessed(self):
        # Gerçek değer 1 iken fark ve göreli hata aynı sayıdır: hangisi kastedildiği bilinemez.
        record, _, _ = self.run_one('Bu sonuç (0.3), tahmindeki artıktır.',
                                    [{'tur': 'artik', 'deger': '0.3', 'tahmin': '1.3', 'gercek': '1',
                                      'fonksiyon': 'x**2 - 1', 'degisken': 'x'}],
                                    'Gerçek değer 1, tahmin x₀ = 1.3; f(x) = x² - 1; e = 1.3 - 1 = 0.3.')
        self.assertEqual((record['durum'], record['son_metin']), ('cozulemedi', None))
        self.assertIn('birden çok', record['neden'])

    def test_template_must_pass_reverification_with_same_slots(self):
        # Şablon anlamı kod tarafından yeniden tanınmazsa (yeniden doğrulama gerçekten yapılıyor) başarı sayılmaz.
        from unittest import mock
        with mock.patch.object(verify, '_phrases', lambda kind, slot, context: ('bir sayıdır', 'öteki sayı')):
            record, _, _ = self.run_one('Bu değer, tahminin gerçek kökten ne kadar uzak olduğunu gösterir.',
                                        [CUBE_DISTANCE], CUBE_CONTEXT)
        self.assertEqual((record['durum'], record['son_metin']), ('cozulemedi', None))
        self.assertIn('yeniden doğrulanamadı', record['neden'])

    def test_model_function_slot_with_definition_prefix_is_normalized(self):
        # 13:05 gerçek Qwen yanıtı fonksiyon yuvasına "f(x) = …" yazdı; ad ve ifade ayrılmalı.
        slot = dict(CUBE_DISTANCE, fonksiyon='g(x) = x**3 - 5', degisken='x')
        record, _, _ = self.run_one('Bu değer, tahminin gerçek kökten ne kadar uzak olduğunu gösterir.', [slot],
                                    'x³ = 5 için tahmin x₀ = 2; g(2) = 8 - 5 = 3.')
        self.assertEqual(record['durum'], 'duzeltildi')
        self.assertIn('g(2) değeridir', record['son_metin'])

    def test_gold_and_note_fields_do_not_reach_model(self):
        _, model, _ = self.run_one('Bu değer, tahminin gerçek kökten ne kadar uzak olduğunu gösterir.', [CUBE_DISTANCE],
                                   CUBE_CONTEXT, {'altin': 'yanlis', 'not': 'GIZLI-ETIKET-NOTU artık değil uzaklık',
                                                  'kaynaklar': ['Ders kaydı 03:14']})
        sent = '\n'.join(model.prompts)
        for secret in ('GIZLI-ETIKET-NOTU', 'yanlis', 'Ders kaydı 03:14'):
            self.assertNotIn(secret, sent)

    def test_raw_model_responses_are_recorded_for_every_stage(self):
        wrong = 'Gradient descent Hessian kullanır.'
        fixed = 'Gradient descent yalnız gradyanı kullanır.'
        units = [{'id': 'U1', 'metin': wrong, 'baglam': '', 'kaynaklar': []}]
        specs = {'U1': spec(olgu=True, ingilizce='GD uses Hessian', arama=['Gradient descent'])}
        quote = 'It uses only the gradient, not the Hessian.'
        verdicts = {wrong: {'kontrol': '', 'karar': 'celisiyor', 'kanit': quote},
                    fixed: {'kontrol': '', 'karar': 'destekleniyor', 'kanit': quote}}
        evidence = {'Gradient descent': [{'title': 'Gradient descent', 'url': 'https://en.wikipedia.org/wiki/GD', 'text': GD}]}
        verifier = verify.Verifier(FakeModel(specs, verdicts, {wrong: fixed}), FakeEvidence(evidence))
        self.assertEqual(verifier.run(units)[0]['durum'], 'duzeltildi')
        self.assertEqual([r['asama'] for r in verifier.raw],
                         ['biçimlendirme', 'kanıt yargısı', 'düzeltme', 'biçimlendirme', 'kanıt yargısı'])
        self.assertTrue(all(r['birimler'] == ['U1'] and r['yanit'] for r in verifier.raw))
        self.assertEqual(json.loads(verifier.raw[2]['yanit'])['duzeltilmis'], fixed)

    def test_unparseable_response_is_still_recorded(self):
        class Broken(FakeModel):
            def generate(self, messages, schema, temperature, max_tokens, **kw):
                return 'birimler: anlaşılmaz yanıt', {}
        verifier = verify.Verifier(Broken({}, {}, {}), FakeEvidence({}))
        record = verifier.run([{'id': 'U1', 'metin': 'Cümle.', 'baglam': '', 'kaynaklar': []}])[0]
        self.assertEqual(record['durum'], 'denetlenmedi')
        self.assertEqual(verifier.raw[0]['yanit'], 'birimler: anlaşılmaz yanıt')

    def test_rules_do_not_hardcode_fixture_values(self):
        # Kural kodunda fixture'ın sayıları/ifadeleri sabit olarak geçmemeli (yorum ve belge dizgileri hariç).
        import io
        import tokenize
        source = (ROOT / 'verify.py').read_text(encoding='utf-8')
        found = []
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            # 1.5 sayı olarak BM25 k1 ve web bekleme süresidir (pause=1.5 sn); dizgilerde yine aranır.
            if token.type == tokenize.NUMBER and token.string in ('0.25', '1.414', '0.0858', '2.25'):
                found.append(token.string)
            if token.type == tokenize.STRING and not token.string.startswith(('"""', "'''")):
                found += [v for v in ('0.25', '1.5', '1.414', 'sqrt(2)', 'x**2 - 2', 'Hessian') if v in token.string]
        self.assertEqual(found, [])

GD_PAGE = [{'title': 'Gradient descent', 'url': 'https://en.wikipedia.org/wiki/Gradient_descent',
            'text': 'Gradient descent should not be confused with local search algorithms, although both are iterative '
                    'methods for optimization.'},
           {'title': 'Gradient descent', 'url': 'https://en.wikipedia.org/wiki/Gradient_descent',
            'text': 'If the function is convex, all local minima are also global minima, so in this case gradient descent '
                    'can converge to the global solution.'},
           {'title': 'Hessian matrix', 'url': 'https://en.wikipedia.org/wiki/Hessian_matrix',
            'text': 'The Hessian matrix is the square matrix of second-order partial derivatives; it is used in the '
                    'second-derivative test for local maxima and minima.'}]
Y2_CLAIM = ('Gradient descent uses both gradient (first derivative) and Hessian (second derivative) methods to find '
            'local minima or maxima.')

class QuoteRelevanceTests(unittest.TestCase):
    def judged(self, claim, verdict, quote, passages=GD_PAGE, subject='Gradient descent'):
        units = [{'id': 'U1', 'metin': 'Föy cümlesi.', 'baglam': '', 'kaynaklar': []}]
        verdicts = {'Föy cümlesi': {'kontrol': '', 'karar': verdict, 'kanit': quote}}
        model = FakeModel({'U1': spec(olgu=True, ingilizce=claim, arama=[subject])}, verdicts, {})
        return verify.Verifier(model, FakeEvidence({subject: passages}), budget=verify.Budget(düzeltme=0)).run(units)[0]

    def test_irrelevant_verbatim_quote_is_not_contradiction_evidence(self):
        # 16.10.2026 12:01: Y2 "çelişiyor" kararı bu türden birebir ama ilgisiz parçalara dayanmıştı. Hessian sayfası
        # parçası Hessian'ı anlatır ama GD hakkında bir şey söylemez (özne aynı parçada yok).
        quote = '\n'.join([GD_PAGE[0]['text'], GD_PAGE[1]['text'].replace('If the function ', ''), GD_PAGE[2]['text']])
        record = self.judged(Y2_CLAIM, 'celisiyor', quote)
        self.assertEqual(record['durum'], 'kanit_yetersiz')
        self.assertIn('ilgisiz', record['neden'])
        self.assertEqual(record['son_metin'], 'Föy cümlesi.')

    def test_topic_words_alone_do_not_make_a_quote_relevant(self):
        passages = [{'title': 'Gradient descent', 'url': 'u', 'text': 'Gradient descent is an iterative algorithm. '
                     'It uses only the gradient, not the Hessian.'}]
        self.assertEqual(self.judged('Gradient descent uses the Hessian', 'celisiyor',
                                     'Gradient descent is an iterative algorithm.', passages)['durum'], 'kanit_yetersiz')
        self.assertEqual(self.judged('Gradient descent uses the Hessian', 'celisiyor',
                                     'It uses only the gradient, not the Hessian.', passages)['durum'], 'cozulemedi')

    def test_irrelevant_quote_cannot_verify_a_clean_claim_either(self):
        passages = [{'title': 'Finite difference', 'url': 'u', 'text': 'Finite differences are widely used in numerical '
                     'analysis for solving differential equations. The backward difference uses the values at x and '
                     'x - h, and its error follows from the Taylor series expansion.'}]
        claim = 'Backward difference is a derivative approximation obtained using Taylor series expansion.'
        self.assertEqual(self.judged(claim, 'destekleniyor', 'Finite differences are widely used in numerical analysis '
                                     'for solving differential equations.', passages, 'Backward difference')['durum'],
                         'kanit_yetersiz')
        self.assertEqual(self.judged(claim, 'destekleniyor', 'The backward difference uses the values at x and x - h, and '
                                     'its error follows from the Taylor series expansion.', passages,
                                     'Backward difference')['durum'], 'dogrulandi')

    def test_formalization_prompt_contains_no_fixture_sentence(self):
        fixture = json.loads((ROOT / 'ornekler' / 'dogrulama' / 'fixture-2026-10-16.json').read_text(encoding='utf-8'))
        model = FakeModel({}, {}, {})
        verify.Verifier(model, FakeEvidence({})).formalize([{'id': 'Z', 'metin': 'Boş.', 'baglam': ''}])
        prompt = model.prompts[0].casefold()
        for unit in fixture['birimler']:
            for text in (unit['metin'], unit['not']):
                for piece in re.findall(r'[^,.;()]{25,}', text.casefold()):
                    self.assertNotIn(piece.strip(), prompt)

if __name__ == '__main__':
    unittest.main()
