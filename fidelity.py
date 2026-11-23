"""Çözümlü örneklerin kaynağa sadakati: sayı ve formül eşleştirmesi.

Modelin "kaynakta" demesi kanıt sayılmaz. Örneğin sorusundaki kurulum sayıları ve formülleri
kaynak metninde gerçekten geçiyor mu, burada mekanik olarak denetlenir:
- kaynakta:   sorudaki formüller ve önemli sayıların hepsi kaynakta var;
- uyarlanmis: kaynakla bağ var (atıf veya eşleşen sayı/formül) ama kurulumun bir kısmı kaynakta yok;
- uretilmis:  kaynakla doğrulanabilir bağ yok.
Kavramsal (sayısız, formülsüz) örneklerde mekanik denetim yapılamaz; modelin etiketi atıf varsa korunur.
"""
import re

NUMBER = re.compile(r'(?<![\w₀-₉.,])\d+(?:[.,]\d+)?(?![\d₀-₉])')
# Konuşma dökümünde sayılar çoğunlukla sözcükle geçer. "bir" (1) zaten önemsiz sayıdır.
WORDS = {'iki': 2, 'üç': 3, 'dört': 4, 'beş': 5, 'altı': 6, 'yedi': 7, 'sekiz': 8, 'dokuz': 9,
         'two': 2, 'three': 3, 'four': 4, 'five': 5}
TRIVIAL = {0.0, 1.0, 2.0}
MATH_TOKEN = re.compile(r"[A-Za-zα-ωΑ-Ω0-9²³⁴₀-₉′'()\[\]+\-−–*/·^.,√π∇]+")

def numbers(text):
    """Metindeki sayılar (ondalık virgül/nokta eşit sayılır)."""
    found = {float(n.replace(',', '.')) for n in NUMBER.findall(str(text))}
    for word in re.findall(r'[^\W\d_]+', str(text).casefold()):
        if word in WORDS:
            found.add(float(WORDS[word]))
    return found

def important_numbers(text):
    return {n for n in numbers(text) if n not in TRIVIAL}

def _mathy(token):
    if not token or len(token) > 24 or not MATH_TOKEN.fullmatch(token):
        return False
    return len(token) == 1 or bool(re.search(r'[\d()+\-−–*/·^²³√∇]', token))

def normalize_expression(text):
    text = str(text).casefold().replace('−', '-').replace('–', '-').replace(',', '.')
    text = text.replace('″', "''").replace('′', "'").replace('’', "'")
    return re.sub(r'[\s·*]', '', text)

def expressions(text):
    """'f(w) = (w − 3)²', 'x² - 4 = 0' gibi kurulum ifadeleri (harf + eşittir + sağ taraf)."""
    found = []
    for line in str(text).splitlines():
        found += _line_expressions(line)
    return found

def _line_expressions(text):
    found = []
    for match in re.finditer(r'(?<![<>=!≈])=(?!=)', text):
        left, right = text[:match.start()].split(), text[match.end():].split()
        lhs, rhs = [], []
        for token in reversed(left):
            if not _mathy(token) or (lhs and token[-1] in ',;:'):
                break  # "…(w − 3), η = 0,1": virgül önceki ifadeyi bitirir
            lhs.insert(0, token)
        for token in right:
            clean = token.rstrip('.,;:')
            suffix = re.search(r"(?<=[\d)])['’][a-zçğıöşü]+$", clean)
            if suffix:  # "x = 2'deki": Türkçe ek ifadenin parçası değil, ifade burada biter
                rhs.append(clean[:suffix.start()])
                break
            if not _mathy(clean):
                break
            rhs.append(clean)
            if clean != token:
                break
        while rhs and re.fullmatch(r'[+\-−–*/·^]+', rhs[-1]):
            rhs.pop()  # "w(t) −" gibi yarım kalan sağ taraf
        expression = ' '.join(lhs) + ' = ' + ' '.join(rhs)
        norm = normalize_expression(expression)
        if lhs and rhs and len(norm) >= 5 and re.search(r'[a-zα-ω]', norm):
            found.append(expression.strip())
    return found

def setup_text(example):
    """Örneğin kurulumu: soru; soruda sayı/formül yoksa çözümün ilk cümleleri."""
    question = str(example.get('soru', ''))
    if important_numbers(question) or expressions(question):
        return question
    return str(example.get('cozum', ''))[:240]

def check_example(example, passages, all_passages):
    """Örneğin kaynak bağını denetle. (etiket, not, otomatik_atif) döndürür."""
    setup = setup_text(example)
    wanted_numbers = important_numbers(setup)
    wanted_expressions = expressions(setup)
    cited_text = ' '.join(f'{p.text} {p.original}' for p in passages)
    all_text = ' '.join(f'{p.text} {p.original}' for p in all_passages)
    source_numbers = numbers(all_text)
    source_expressions = normalize_expression(all_text)
    missing_numbers = sorted(n for n in wanted_numbers if n not in source_numbers)
    missing_expressions = [e for e in wanted_expressions if normalize_expression(e) not in source_expressions]
    matched = (len(wanted_numbers) - len(missing_numbers)) + (len(wanted_expressions) - len(missing_expressions))
    checkable = bool(wanted_numbers or wanted_expressions)
    claim = example.get('dayanak') or 'uretilmis'
    cited = bool(passages)

    auto_cite = None
    if checkable and not missing_numbers and not missing_expressions and not cited:
        # Model atıf vermediyse, kurulumun en çok geçtiği parçayı bul.
        def score(p):
            body = f'{p.text} {p.original}'
            return (sum(n in numbers(body) for n in wanted_numbers)
                    + sum(normalize_expression(e) in normalize_expression(body) for e in wanted_expressions))
        best = max(all_passages, key=score, default=None)
        if best is not None and score(best) >= max(2, matched):
            auto_cite = best.id

    def note():
        parts = []
        if missing_expressions:
            parts.append('kaynakta geçmeyen ifade: ' + '; '.join(missing_expressions[:3]))
        if missing_numbers:
            parts.append('kaynakta geçmeyen sayı: ' + ', '.join(fmt(n) for n in missing_numbers[:6]))
        return ' · '.join(parts)

    if not checkable:
        label = claim if cited else 'uretilmis'
        if label == 'kaynakta' and not cited:
            label = 'uretilmis'
        return label, '', None
    if not missing_numbers and not missing_expressions:
        if cited or auto_cite:
            # Model "uyarlanmış" dediyse (yöntem/soru değişmiş olabilir) daha temkinli etiketi koru.
            return ('uyarlanmis' if claim == 'uyarlanmis' else 'kaynakta'), '', auto_cite
        return 'uretilmis', '', None
    if matched or cited:
        return 'uyarlanmis', note(), None
    return 'uretilmis', note(), None

def fmt(value):
    return (f'{value:.6f}'.rstrip('0').rstrip('.')).replace('.', ',')

def transcript_only(passages, library):
    """Atıflar yalnızca konuşma dökümüne mi dayanıyor?"""
    kinds = {library.source(p.source_id).kind for p in passages if p}
    return bool(kinds) and kinds <= {'transkript'}
