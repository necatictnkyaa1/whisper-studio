"""Belirlenimci hesap denetimi; ayrı alt süreçte çalışır (verify.SympyChecker süre aşımında öldürür).

Güvenlik: girdi metni hiçbir zaman eval/sympify/parse_expr ile yorumlanmaz. Python `ast` ile ayrıştırılır,
yalnız izinli düğümler/adlar kabul edilir ve SymPy nesneleri doğrudan kurulur. Düğüm sayısı, sayı büyüklüğü,
üs ve faktöriyel argümanı sınırlıdır.

Karar kuralları:
- Kesin iddia (varsayılan; ondalıklar tam kesir olarak alınır, 0.1 + 0.2 = 0.3 doğru, = 0.4 yanlış):
  simplify(sol - sag) == 0 → tutarli; sembolsüz ve sıfırdan farklı →
  celisiyor; sembollü ve sıfırlanmıyorsa farklı değerlerle örneklenir: karşı örnek → celisiyor, yoksa belirsiz
  (örnekleme özdeşliği ispatlamaz).
- Yaklaşık iddia (yalnız istekte yaklasik=True ise; çağıran taraf metinde ≈/"yaklaşık" işareti arar): yazılan
  basamak hassasiyeti kadar tolerans (ör. 1.414 → ±0.0005). Ondalık yazılmış olmak tek başına yaklaşıklık değildir.
"""
import ast
import json
import random
import sys

MAX_NODES = 120
MAX_NUMBER = 10 ** 9
MAX_EXPONENT = 40
MAX_FACTORIAL = 40
SYMBOLS = ('x', 'y', 'z', 't', 'a', 'b', 'h', 'n', 'w')
FUNCTIONS = {'sqrt', 'Abs', 'abs', 'exp', 'log', 'ln', 'sin', 'cos', 'tan', 'asin', 'acos', 'atan',
             'sinh', 'cosh', 'tanh', 'factorial', 'diff', 'integrate', 'limit', 'taylor', 'subs'}
CONSTANTS = {'pi', 'E', 'oo'}

class Rejected(Exception):
    pass

def normalize(text):
    text = str(text).strip()
    for a, b in (('^', '**'), ('−', '-'), ('–', '-'), ('·', '*'), ('×', '*'), ('²', '**2'), ('³', '**3'),
                 ('√', 'sqrt'), ('π', 'pi')):
        text = text.replace(a, b)
    return text

def decimals(text):
    """Ondalık sayıların en küçük basamak hassasiyeti; ondalık yoksa None (kesin iddia)."""
    import re
    found = re.findall(r'\d+\.(\d+)', normalize(text))
    return max((len(d) for d in found), default=None)

class Builder:
    def __init__(self):
        import sympy
        self.sp = sympy
        self.nodes = 0
        self.symbols = {name: sympy.Symbol(name) for name in SYMBOLS}

    def build(self, text):
        try:
            tree = ast.parse(normalize(text), mode='eval')
        except SyntaxError:
            raise Rejected('sözdizimi')
        return self.node(tree.body)

    def node(self, n):
        sp = self.sp
        self.nodes += 1
        if self.nodes > MAX_NODES:
            raise Rejected('ifade çok büyük')
        if isinstance(n, ast.Constant) and type(n.value) in (int, float):
            if abs(n.value) > MAX_NUMBER:
                raise Rejected('sayı çok büyük')
            return sp.Integer(n.value) if isinstance(n.value, int) else sp.Rational(repr(n.value))
        if isinstance(n, ast.Name):
            if n.id in self.symbols:
                return self.symbols[n.id]
            if n.id in CONSTANTS:
                return {'pi': sp.pi, 'E': sp.E, 'oo': sp.oo}[n.id]
            raise Rejected(f'izinsiz ad: {n.id}')
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd)):
            value = self.node(n.operand)
            return -value if isinstance(n.op, ast.USub) else value
        if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)):
            left, right = self.node(n.left), self.node(n.right)
            if isinstance(n.op, ast.Pow):
                if not right.is_number or abs(right) > MAX_EXPONENT:
                    raise Rejected('üs sınırı')
                return sp.Pow(left, right)
            return {ast.Add: sp.Add, ast.Sub: lambda p, q: sp.Add(p, -q), ast.Mult: sp.Mul,
                    ast.Div: lambda p, q: sp.Mul(p, sp.Pow(q, -1))}[type(n.op)](left, right)
        if isinstance(n, ast.Tuple) and len(n.elts) <= 3:
            return tuple(self.node(e) for e in n.elts)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in FUNCTIONS and not n.keywords \
                and len(n.args) <= 4:
            args = [self.node(a) for a in n.args]
            name = n.func.id
            if name == 'factorial':
                if len(args) != 1 or not (args[0].is_number and abs(args[0]) <= MAX_FACTORIAL):
                    raise Rejected('faktöriyel sınırı')
                return sp.factorial(args[0])
            if name == 'taylor':
                if len(args) != 4 or not args[3].is_Integer or not (0 <= int(args[3]) <= 12):
                    raise Rejected('taylor(f, x, nokta, derece)')
                return sp.series(args[0], args[1], args[2], int(args[3]) + 1).removeO()
            if name == 'subs':
                if len(args) != 3 or not args[1].is_Symbol:
                    raise Rejected('subs(f, x, deger)')
                return args[0].subs(args[1], args[2])
            if name == 'diff':
                if len(args) == 3 and not (args[2].is_Integer and 0 < int(args[2]) <= 6):
                    raise Rejected('türev derecesi')
                return sp.diff(*args)
            table = {'sqrt': sp.sqrt, 'Abs': sp.Abs, 'abs': sp.Abs, 'exp': sp.exp, 'log': sp.log, 'ln': sp.log,
                     'sin': sp.sin, 'cos': sp.cos, 'tan': sp.tan, 'asin': sp.asin, 'acos': sp.acos, 'atan': sp.atan,
                     'sinh': sp.sinh, 'cosh': sp.cosh, 'tanh': sp.tanh, 'integrate': sp.integrate, 'limit': sp.limit}
            return table[name](*args)
        raise Rejected(f'izinsiz yapı: {type(n).__name__}')

def compare(left, right, approximate=False):
    import sympy as sp
    builder = Builder()
    try:
        a, b = builder.build(left), builder.build(right)
    except Rejected as error:
        return 'belirsiz', f'ifade reddedildi: {error}'
    if isinstance(a, tuple) or isinstance(b, tuple):
        return 'belirsiz', 'ifade bir değer değil'
    places = decimals(right)
    difference = sp.simplify(a - b)
    if not approximate:
        if difference == 0:
            return 'tutarli', f'{left} = {right} (sembolik olarak özdeş)'
        if not difference.free_symbols:
            value = sp.N(difference, 30)
            if value == 0:
                return 'tutarli', f'{left} = {right}'
            return 'celisiyor', f'{left} = {sp.N(a, 8)}; iddia {right} = {sp.N(b, 8)}'
        return sample(difference, left, right, tolerance=1e-9)
    tolerance = 0.5 * 10 ** (-(places or 6)) * 1.0001
    if difference.free_symbols:
        return sample(difference, left, right, tolerance=tolerance)
    gap = abs(complex(sp.N(difference, 30)))
    if gap <= tolerance:
        return 'tutarli', f'{left} ≈ {sp.N(a, 8)}; iddia {right} (±{tolerance:.2g})'
    return 'celisiyor', f'{left} = {sp.N(a, 8)}; iddia {right} (fark {gap:.4g} > ±{tolerance:.2g})'

def sample(difference, left, right, tolerance):
    """Yalnız karşı örnek arar: bulunursa çelişki; bulunmazsa belirsiz (ispat değildir)."""
    rng = random.Random(7)
    symbols = sorted(difference.free_symbols, key=str)
    for _ in range(6):
        point = {s: rng.uniform(0.2, 1.7) for s in symbols}  # her sembole farklı değer
        try:
            value = abs(complex(difference.subs(point).evalf()))
        except (TypeError, ValueError):
            continue
        if value > tolerance:
            shown = ', '.join(f'{s}={v:.3f}' for s, v in point.items())
            return 'celisiyor', f'{left} ile {right} özdeş değil (karşı örnek {shown})'
    return 'belirsiz', f'{left} ile {right} sınanan noktalarda eşit, sembolik olarak ispatlanamadı'

def main():
    # -I ile PYTHONIOENCODING yok sayılır; Windows varsayılanı cp1254 olabilir. Kanal her iki uçta UTF-8.
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    for line in sys.stdin:
        try:
            request = json.loads(line)
            state, detail = compare(request['sol'], request['sag'], bool(request.get('yaklasik')))
        except Exception as error:  # alt süreç asla çökmez; belirsiz döner
            state, detail = 'belirsiz', f'hesaplanamadı: {type(error).__name__}'
        sys.stdout.write(json.dumps({'durum': state, 'ayrinti': detail}, ensure_ascii=False) + '\n')
        sys.stdout.flush()

if __name__ == '__main__':
    main()
