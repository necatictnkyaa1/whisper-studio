"""Föydeki sayısal tutarlılık kontrolleri ve okunur formül gösterimi.

Dil modeli hesap doğrulayıcı sayılmaz. Burada yalnızca açıkça yazılmış sayısal eşitlikler
(ör. "0,6 − 0,1 · (−4,8) = 1,08") Python ile yeniden hesaplanır ve cevap ile açıklamanın
vardığı sonuç karşılaştırılır. Değişkenli/sembolik ifadeler doğrulanmaz; bu kontrol bir
güvenlik ağıdır, matematiksel ispat değildir.
"""
import ast
import operator
import re
import unicodedata

NUMBER = r'\d+(?:[.,]\d+)?'
TOKEN = re.compile(r'\s*(' + NUMBER + r'|[+\-−–·×*/()²³^])')
EXPRESSION = re.compile(r'^(?:\s*(?:' + NUMBER + r'|[+\-−–·×*/()²³^]))+\s*$')
BLOCKERS = set("'′″’") | set('₀₁₂₃₄₅₆₇₈₉')

def _to_python(expr):
    tokens = TOKEN.findall(expr)
    out = []
    for token in tokens:
        if re.fullmatch(NUMBER, token):
            token = token.replace(',', '.')
            if out and (out[-1] == ')' or re.fullmatch(r'[\d.]+', out[-1])):
                out.append('*')
        elif token == '(' and out and (out[-1] == ')' or re.fullmatch(r'[\d.]+', out[-1])):
            out.append('*')
        token = {'−': '-', '–': '-', '·': '*', '×': '*', '²': '**2', '³': '**3', '^': '**'}.get(token, token)
        out.append(token)
    return ''.join(out)

_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.USub: operator.neg, ast.UAdd: operator.pos}

def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        right = _eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 6:
            raise ValueError('üs çok büyük')
        return _OPS[type(node.op)](_eval(node.left), right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError('desteklenmeyen ifade')

def evaluate(expr):
    """Yalnız sayı ve + − · / ( ) ² içeren ifadeyi hesapla; değilse None."""
    if not expr or not EXPRESSION.match(expr) or not re.search(r'\d', expr):
        return None
    try:
        return float(_eval(ast.parse(_to_python(expr), mode='eval')))
    except (SyntaxError, ValueError, ZeroDivisionError, OverflowError, TypeError):
        return None

def _has_operator(expr):
    return bool(re.search(r'[+\-−–·×*/²³^]|\d\s*\(|\)\s*\(', expr.strip().lstrip('-−–')))

def _left_expression(segment):
    for start in range(len(segment)):
        candidate = segment[start:]
        if candidate.strip() and EXPRESSION.match(candidate):
            before = segment[start - 1] if start else ''
            if before and (before.isalpha() or before in BLOCKERS or before == ')'):
                return None
            return candidate
    return None

def _right_expression(segment):
    match = re.match(r'(?:\s*(?:' + NUMBER + r'|[+\-−–·×*/()²³^]))+', segment)
    if not match:
        return None
    expr = match.group(0)
    rest = segment[len(expr):]
    if rest[:1].isalpha() or rest[:1] in BLOCKERS:
        return None
    return expr.rstrip(' .,(')  # cümle sonu noktası/virgülü ifadeye dahil değil

def close(a, b):
    return abs(a - b) <= max(1e-6, 0.006 * max(abs(a), abs(b)))

def _number(text):
    return float(text.replace(',', '.'))

def arithmetic_issues(text):
    """'ifade = ifade' zincirlerindeki hatalı sayısal adımları listele."""
    issues = []
    for line in re.split(r'[\n;]|(?<=\D)\.\s', str(text)):
        parts = line.split('=')
        for i in range(len(parts) - 1):
            left, right = _left_expression(parts[i]), _right_expression(parts[i + 1])
            if not left or not right or not (_has_operator(left) or _has_operator(right)):
                continue
            a, b = evaluate(left), evaluate(right)
            if a is not None and b is not None and not close(a, b):
                issues.append(f'{left.strip()} = {right.strip()} (doğrusu ≈ {fmt(a)})')
    return issues

def final_value(text):
    """Açıklamanın vardığı son sayısal sonuç: son '= sayı'."""
    values = re.findall(r'=\s*([+\-−–]?\s*' + NUMBER + r')(?![\d,.]*\s*[\w(])', str(text))
    if not values:
        return None
    return _number(re.sub(r'\s|[−–]', lambda m: '-' if m.group(0) in '−–' else '', values[-1]))

def answer_mismatch(answer, explanation):
    """Cevaptaki sayı açıklamanın son sonucuyla çelişiyorsa açıklama metni döndür."""
    numbers = [_number(n) for n in re.findall(r'(?<![\w₀-₉])[+\-−]?' + NUMBER, str(answer).replace('−', '-'))]
    result = final_value(explanation)
    if not numbers or result is None or any(close(n, result) for n in numbers):
        return None
    return f'cevap {", ".join(fmt(n) for n in numbers)}, açıklamanın sonucu {fmt(result)}'

def fmt(value):
    text = f'{value:.4f}'.rstrip('0').rstrip('.')
    return text.replace('.', ',')

# ---------- LaTeX → okunur Unicode ----------

SYMBOLS = {r'\eta': 'η', r'\nabla': '∇', r'\cdot': '·', r'\times': '×', r'\sum': 'Σ', r'\dots': '…',
           r'\ldots': '…', r'\cdots': '⋯', r'\approx': '≈', r'\leq': '≤', r'\geq': '≥', r'\le': '≤',
           r'\ge': '≥', r'\neq': '≠', r'\infty': '∞', r'\alpha': 'α', r'\beta': 'β', r'\gamma': 'γ',
           r'\delta': 'δ', r'\Delta': 'Δ', r'\theta': 'θ', r'\lambda': 'λ', r'\mu': 'μ', r'\sigma': 'σ',
           r'\pi': 'π', r'\partial': '∂', r'\to': '→', r'\rightarrow': '→', r'\leftarrow': '←',
           r'\pm': '±', r'\in': '∈', r'\sqrt': '√', r'\prime': '′', r'\epsilon': 'ε', r'\varepsilon': 'ε',
           r'\quad': ' ', r'\,': ' ', r'\;': ' ', r'\!': '', r'\left': '', r'\right': ''}
SUPERSCRIPT = str.maketrans('0123456789+-n', '⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻ⁿ')
SUBSCRIPT = str.maketrans('0123456789+-ioknt', '₀₁₂₃₄₅₆₇₈₉₊₋ᵢₒₖₙₜ')

def readable_math(text):
    """Modelin yazdığı basit LaTeX'i ($\\eta$, \\frac{1}{2}, x^2, y_i) düz okunur metne çevir."""
    if not isinstance(text, str) or ('\\' not in text and '$' not in text and '^' not in text and '_' not in text):
        return text
    def frac(m):
        a, b = m.group(1), m.group(2)
        wrap = lambda s: s if re.fullmatch(r'[\w.,]+', s) else f'({s})'
        return f'{wrap(a)}/{wrap(b)}'
    for _ in range(3):
        text = re.sub(r'\\[dt]?frac\{([^{}]*)\}\{([^{}]*)\}', frac, text)
    text = re.sub(r'\\hat\{(\w)\}', lambda m: m.group(1) + '\u0302', text)
    text = re.sub(r'\\(?:text|mathrm|mathbf|operatorname)\{([^{}]*)\}', r'\1', text)
    for key in sorted(SYMBOLS, key=len, reverse=True):
        # Önek işaretlerinden (∇L, √x, ∂f) sonraki LaTeX ayırıcı boşluğu atılır.
        spacing = r'\s*' if SYMBOLS[key] in '∇√∂' else ''
        text = re.sub(re.escape(key) + r'(?![A-Za-z])' + spacing, SYMBOLS[key], text)
    def sup(m):
        body = m.group(1) or m.group(2)
        return body.translate(SUPERSCRIPT) if all(c in '0123456789+-n' for c in body) else '^' + body
    def sub(m):
        body = m.group(1) or m.group(2)
        return body.translate(SUBSCRIPT) if all(c in '0123456789+-ioknt' for c in body) else '_' + body
    text = re.sub(r'\^\{([^{}]+)\}|\^(\w)', sup, text)
    text = re.sub(r'(?<=[\ŵ])_\{([^{}]+)\}|(?<=[\ŵ])_(\w)', sub, text)
    text = text.replace('$', '').replace('\\{', '{').replace('\\}', '}')
    return unicodedata.normalize('NFC', re.sub(r'[ \t]{2,}', ' ', text))
