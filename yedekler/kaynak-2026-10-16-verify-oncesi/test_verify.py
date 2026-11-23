"""Doğrulama/düzeltme hattı testleri. Hesap testleri gerçek SymPy alt sürecini kullanır; model sahtedir."""
import json
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
        self.specs, self.verdicts, self.fixes, self.prompts = specs, verdicts, fixes, []
    def generate(self, messages, schema, temperature, max_tokens, **kw):
        prompt = messages[-1]['content']
        self.prompts.append(prompt)
        if schema is verify.FORMAL_SCHEMA:
            ids = [line.split(']')[0].strip('[ ') for line in prompt.splitlines() if line.startswith('[')]
            return json.dumps({'birimler': [dict(self.specs[i], id=i) for i in ids if i in self.specs]}), {}
        if schema is verify.JUDGE_SCHEMA:
            for key, verdict in self.verdicts.items():
                if key in prompt:
                    return json.dumps(verdict), {}
            return json.dumps({'kontrol': '', 'karar': 'yetersiz', 'kanit': ''}), {}
        for key, fixed in self.fixes.items():
            if key in prompt:
                return json.dumps({'duzeltilmis': fixed, 'degisiklik': 'kanıta göre düzeltildi'}), {}
        return json.dumps({'duzeltilmis': '', 'degisiklik': ''}), {}

GD = 'Gradient descent is a first-order iterative algorithm. It uses only the gradient, not the Hessian.'
NEWTON = "Newton's method uses the Hessian matrix of second derivatives."

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
                    return json.dumps({'birimler': [{'id': 'U1', 'olgu_var': False, 'ingilizce': '', 'arama': [],
                                                     'hesaplar': [{'sol': '1.5 - sqrt(2)', 'sag': '0.086', 'anlam': 'uzaklık', 'yaklasik': True}]}]}), {}
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
        self.assertEqual(results[0]['durum'], 'hesap_tutarli')  # "doğrulandı" değil

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

if __name__ == '__main__':
    unittest.main()
