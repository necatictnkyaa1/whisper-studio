"""Aşama 2: föyü internetten güvenilir kaynaklarla genişletme (ilk sınırlı sürüm).

Kaynak: Vikipedi (tr, sonra en) MediaWiki API — ücretsiz, anahtarsız. Metin CC BY-SA 4.0; föyde
başlık, bağlantı, erişim tarihi ve lisans gösterilir, uzun kopya yapılmaz (model özetler).
Gizlilik: sorgular yalnızca föyün terim adlarından üretilir; ders metni, transkript veya kişisel
bilgi internete gönderilmez. Sorgular föyde listelenir. Web sayfaları da veri sayılır.
Bütün interneti taramaya çalışmaz; genel web araması (SearXNG + Trafilatura) sonraki adım.
"""
import difflib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import date

USER_AGENT = 'DersYazi/0.1 (yerel masaustu egitim prototipi; Python urllib)'
API = 'https://{lang}.wikipedia.org/w/api.php'
MAX_PAGES = 5
PAGE_CHARS = 3200
LICENSE = 'CC BY-SA 4.0'

class ResearchError(Exception):
    pass

@dataclass
class WebPage:
    title: str
    url: str
    lang: str
    text: str
    query: str
    retrieved: str = field(default_factory=lambda: date.today().strftime('%d.%m.%Y'))
    license: str = LICENSE

def http_get(url, params, timeout=20, opener=urllib.request.urlopen, sleep=time.sleep):
    """Gerçek ağ çağrısı. Testlerde yerine sahte bir fonksiyon verilir.
    HTTP 429 (16.10.2026 gerçek denemede tr.wikipedia.org'dan alındı): Retry-After kadar bekle, bir kez tekrarla."""
    full = url + '?' + urllib.parse.urlencode(params)
    request = urllib.request.Request(full, headers={'User-Agent': USER_AGENT})
    for attempt in range(2):
        try:
            with opener(request, timeout=timeout) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as error:
            if error.code == 429 and attempt == 0:
                try:
                    wait = float(error.headers.get('Retry-After', 2))
                except (TypeError, ValueError):
                    wait = 2
                sleep(min(max(wait, 1), 5))
                continue
            raise ResearchError(f'HTTP {error.code}')
        except (urllib.error.URLError, TimeoutError, ConnectionError, ValueError) as error:
            raise ResearchError(str(getattr(error, 'reason', error)))

def term_queries(terms, limit=5):
    """'Gradyan İnişi (Gradient Descent)' → [('tr','Gradyan İnişi'), ('en','Gradient Descent')]."""
    queries, seen = [], set()
    for term in terms:
        term = re.sub(r'\s+', ' ', str(term)).strip()
        if not term:
            continue
        main = re.sub(r'\s*\([^)]*\)', '', term).strip()
        inner = re.findall(r'\(([^)]+)\)', term)
        pairs = []
        if 2 <= len(main) <= 60:
            pairs.append(('tr', main))
        for part in inner:
            part = part.strip()
            # Parantez içi İngilizce terim (ör. Gradient Descent); Δ gibi semboller sorgu değildir.
            if re.fullmatch(r'[A-Za-z][A-Za-z \-]{2,50}', part):
                pairs.append(('en', part))
        # Kişisel bilgi sızmasın: sorgu en çok 6 sözcük, rakam yok.
        pairs = [(lang, q) for lang, q in pairs if len(q.split()) <= 6 and not re.search(r'\d', q)]
        key = main.casefold()
        if pairs and key not in seen:
            seen.add(key)
            queries.append(pairs)
        if len(queries) >= limit:
            break
    return queries

def title_matches(query, title):
    """Başlık terimle aynı/çok benzer ya da sorgunun içinde geçiyor ("Taylor Series Approximation" → "Taylor series").
    İçerme durumunda yanlış sayfayı anlam ayrımı ve ders sözcükleri filtresi eler."""
    a, b = query.casefold(), re.sub(r'\s*\([^)]*\)', '', title).casefold()
    if a == b or difflib.SequenceMatcher(None, a, b).ratio() >= 0.8:
        return True
    specific = len(b.split()) >= 2 or len(b) >= 0.6 * len(a)  # tek genel sözcük ("Öğrenme") yetmez
    return len(b) >= 6 and specific and re.search(r'(?<!\w)' + re.escape(b) + r'(?!\w)', a) is not None

def stems(text):
    return {w[:5] for w in re.findall(r'[^\W\d_]{5,}', str(text).casefold())}

def trim(text, limit=PAGE_CHARS):
    """Başlık/kaynakça bölümlerini at, paragraf sınırında kes."""
    text = re.split(r'\n\s*(?:References|Kaynakça|See also|Ayrıca bakınız|Notes|Notlar|External links|Dış bağlantılar)\s*\n',
                    text)[0]
    # Vikipedi düz metninde formüller "{\displaystyle a=0}" + satır satır "a / = / 0" olarak gelir; birleştir.
    lines, merged = [l for l in text.split('\n') if '\\displaystyle' not in l], []
    for line in lines:
        piece = line.strip()
        if not piece and merged and merged[-1].endswith('⁣'):
            continue  # formül parçaları arasındaki boş satırlar
        if piece and len(piece) <= 3 and merged and merged[-1].endswith('⁣'):
            merged[-1] = merged[-1][:-1] + piece + '⁣'
        elif piece and len(piece) <= 3:
            merged.append(piece + '⁣')
        else:
            merged.append(line)
    text = '\n'.join(l.replace('⁣', '') for l in merged)
    text = re.sub(r'\n\s*\n(\s*\n)+', '\n\n', text).strip()
    if len(text) <= limit:
        return text
    cut = text.rfind('\n', 0, limit)
    return text[:cut if cut > limit // 2 else limit].strip()

def search(get, lang, query):
    data = get(API.format(lang=lang), {'action': 'query', 'list': 'search', 'srsearch': query, 'srlimit': 3,
                                        'format': 'json', 'formatversion': 2})
    return [r['title'] for r in data.get('query', {}).get('search', [])]

def fetch(get, lang, title):
    data = get(API.format(lang=lang), {'action': 'query', 'prop': 'extracts|info|pageprops', 'explaintext': 1,
                                        'exsectionformat': 'plain', 'inprop': 'url', 'ppprop': 'disambiguation',
                                        'redirects': 1, 'titles': title, 'format': 'json', 'formatversion': 2})
    pages = data.get('query', {}).get('pages', [])
    if not pages or pages[0].get('missing') or not pages[0].get('extract'):
        return None
    page = pages[0]
    if 'disambiguation' in page.get('pageprops', {}):
        return None  # "Delta şu anlamlara gelebilir…" gibi anlam ayrımı sayfaları kaynak değildir
    return page['title'], page.get('fullurl') or f'https://{lang}.wikipedia.org/wiki/{urllib.parse.quote(page["title"])}', page['extract']

def research(terms, lesson_text, cancelled, on_status, get=http_get, max_pages=MAX_PAGES, pause=1.0):
    """Terimler için Vikipedi sayfaları bul. (sayfalar, sorgular, sorunlar) döndürür; hata föyü durdurmaz."""
    pages, queries, problems, seen = [], [], [], set()
    vocabulary = stems(lesson_text)
    for pairs in term_queries(terms):
        if len(pages) >= max_pages:
            break
        for lang, query in pairs:
            if cancelled():
                return pages, queries, problems
            on_status(f'İnternette ek kaynak aranıyor · “{query}”')
            queries.append(f'{query} ({lang}.wikipedia.org)')
            try:
                titles = [t for t in search(get, lang, query) if title_matches(query, t)]
                if not titles:
                    continue
                found = fetch(get, lang, titles[0])
            except ResearchError as error:
                problems.append(f'{lang}.wikipedia.org erişilemedi: {error}')
                if len(problems) >= 2:
                    return pages, queries, problems  # bağlantı yoksa bütün föyü bekletme
                continue
            finally:
                time.sleep(pause)
            if not found:
                continue
            title, url, text = found
            if url in seen:
                break
            text = trim(text)
            # Ders konusuyla ortak sözcük yoksa (ör. aynı adlı başka bir kavram) sayfayı kullanma.
            if len(stems(text) & vocabulary) < 3:
                problems.append(f'“{title}” ders konusuyla ilgisiz göründüğü için kullanılmadı.')
                continue
            seen.add(url)
            pages.append(WebPage(title, url, lang, text, query))
            break  # bu terim için bir sayfa yeterli
    return pages, queries, problems
