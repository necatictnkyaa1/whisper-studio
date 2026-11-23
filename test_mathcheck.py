import unittest
from mathcheck import arithmetic_issues, answer_mismatch, evaluate, readable_math

class MathCheckTests(unittest.TestCase):
    def test_correct_turkish_decimal_steps_pass(self):
        text = ("1. Adım: f'(0) = 2(0-3) = -6. w₁ = 0 − 0,1 · (−6) = 0 + 0,6 = 0,6. "
                "2. Adım: f'(0,6) = 2(0,6-3) = -4,8'dir. w₂ = 0,6 − 0,1 · (−4,8) = 1,08 olur.")
        self.assertEqual(arithmetic_issues(text), [])

    def test_wrong_step_is_found(self):
        issues = arithmetic_issues('w₁ = 2 - 0,2(4) = 1,4 olur.')
        self.assertEqual(len(issues), 1)
        self.assertIn('1,2', issues[0])

    def test_function_application_is_not_evaluated_as_number(self):
        self.assertEqual(arithmetic_issues("f'(2) = 4 ve g(3) = 9, x₁(5) = 1"), [])

    def test_symbolic_and_list_text_is_ignored(self):
        self.assertEqual(arithmetic_issues('w(t+1) = w(t) − η·∇L ve x = 1, 2, 3; MSE = (1/n) · Σ (y − ŷ)²'), [])

    def test_real_answer_key_contradiction_from_first_e2e(self):
        # 16.10.2026 gerçek qwen3.5:9b denemesinde görülen hata.
        explanation = ("1. Adım: f'(w) = 2w. f'(2) = 4. w₁ = 2 - 0,2(4) = 1,2. 2. Adım: f'(1,2) = 2,4. "
                       "w₂ = 1,2 - 0,2(2,4) = 1,2 - 0,48 = 0,72.")
        self.assertEqual(arithmetic_issues(explanation), [])
        self.assertEqual(answer_mismatch('w₂ = 0,8', explanation), 'cevap 0,8, açıklamanın sonucu 0,72')
        self.assertIsNone(answer_mismatch('w₂ = 0,72', explanation))
        self.assertIsNone(answer_mismatch('Algoritma yavaş yakınsar.', explanation))

    def test_evaluator_rejects_code(self):
        self.assertIsNone(evaluate('__import__("os")'))
        self.assertIsNone(evaluate('2 ** 99999'))
        self.assertAlmostEqual(evaluate('2(0,6−3)'), -4.8)
        self.assertAlmostEqual(evaluate('3²'), 9)

    def test_latex_becomes_readable(self):
        self.assertEqual(readable_math(r'$w(t+1) = w(t) - \eta \cdot \nabla L$'), 'w(t+1) = w(t) - η · ∇L')
        self.assertEqual(readable_math(r"$\frac{1}{2} f''(a)(x - a)^2$"), "1/2 f''(a)(x - a)²")
        self.assertEqual(readable_math(r'$MSE = \frac{1}{n} \sum (y_i - \hat{y}_i)^2$'), 'MSE = 1/n Σ (yᵢ - ŷᵢ)²')
        self.assertEqual(readable_math('Düz metin değişmez.'), 'Düz metin değişmez.')

if __name__ == '__main__':
    unittest.main()
