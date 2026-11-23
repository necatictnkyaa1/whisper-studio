"""Föy kaynakları: transkript, TXT/Markdown ve metinli PDF.

Her parça (Passage) kısa bir kimlik taşır (P1, P2, ...). Model yalnızca bu kimliklere atıf yapar;
insan okunur konum (dosya, sayfa, zaman aralığı) kimlikten geri çözülür. Kaynak metni veri olarak
işlenir: içindeki talimatlar hiçbir yetki kazanmaz.
"""
import re
from dataclasses import dataclass, field
from pathlib import Path

TEXT_EXTENSIONS = {'.txt', '.md', '.markdown'}
PDF_EXTENSIONS = {'.pdf'}
SOURCE_EXTENSIONS = TEXT_EXTENSIONS | PDF_EXTENSIONS
CHUNK_CHARS = 1400

KIND_NAMES = {'transkript': 'Ders kaydı', 'not': 'Not / metin', 'pdf': 'PDF', 'web': 'İnternet'}

@dataclass
class Passage:
    id: str
    source_id: str
    location: str
    text: str
    original: str = ''
    page: int | None = None

@dataclass
class Source:
    id: str
    kind: str
    title: str
    path: str = ''
    passages: list = field(default_factory=list)
    unread_pages: list = field(default_factory=list)
    page_count: int = 0
    url: str = ''
    retrieved: str = ''
    license: str = ''

    def summary(self):
        name = KIND_NAMES.get(self.kind, self.kind)
        if self.kind == 'web':
            return f'{name} · erişim {self.retrieved} · {self.license}'
        if self.kind == 'pdf':
            read = self.page_count - len(self.unread_pages)
            text = f'{name} · {read}/{self.page_count} sayfa okundu'
            if self.unread_pages:
                text += ' · metinsiz sayfa: ' + ', '.join(map(str, self.unread_pages[:8]))
                if len(self.unread_pages) > 8:
                    text += '…'
            return text
        return f'{name} · {len(self.passages)} parça'

class SourceError(Exception):
    pass

def clean(text):
    text = text.replace('\r\n', '\n').replace('\r', '\n').replace('\x00', '')
    text = re.sub(r'[ \t ]+', ' ', text)
    return re.sub(r'\n{3,}', '\n\n', text).strip()

def split_long(text, limit=CHUNK_CHARS):
    """Paragraf, olmazsa cümle sınırında böl; metin kaybı yok."""
    if len(text) <= limit:
        return [text]
    parts, current = [], ''
    pieces = re.split(r'(?<=\n\n)', text)
    if len(pieces) == 1:
        pieces = re.split(r'(?<=[.!?…])\s+', text)
    for piece in pieces:
        while len(piece) > limit:
            cut = piece.rfind(' ', 0, limit)
            cut = cut if cut > limit // 2 else limit
            if current:
                parts.append(current.strip())
                current = ''
            parts.append(piece[:cut].strip())
            piece = piece[cut:]
        if current and len(current) + len(piece) + 1 > limit:
            parts.append(current.strip())
            current = ''
        current = f'{current} {piece}' if current else piece
    if current.strip():
        parts.append(current.strip())
    return [p for p in parts if p]

def read_text_file(path):
    data = Path(path).read_bytes()
    for encoding in ('utf-8-sig', 'cp1254', 'latin-1'):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise SourceError('Metin dosyası okunamadı.')

def clock(seconds):
    seconds = max(0, int(seconds))
    h, rest = divmod(seconds, 3600)
    m, s = divmod(rest, 60)
    return f'{h:02}:{m:02}:{s:02}' if h else f'{m:02}:{s:02}'

class SourceLibrary:
    """Bir dersin kaynakları; kimlikler eklenme sırasına göre K1, K2 ve P1, P2…"""

    def __init__(self):
        self.sources = []
        self._passages = {}

    @property
    def passages(self):
        return [p for s in self.sources for p in s.passages]

    def passage(self, passage_id):
        return self._passages.get(passage_id)

    def source(self, source_id):
        return next((s for s in self.sources if s.id == source_id), None)

    def _new_source(self, kind, title, path=''):
        source = Source(f'K{len(self.sources) + 1}', kind, title, str(path))
        return source

    def _add_passage(self, source, location, text, original='', page=None):
        passage = Passage(f'P{len(self._passages) + 1}', source.id, location, text, original, page)
        self._passages[passage.id] = passage
        source.passages.append(passage)

    def _commit(self, source):
        if not source.passages:
            raise SourceError(f'{source.title}: okunabilir metin bulunamadı.' +
                              (' Sayfalar görsel/taranmış olabilir; bu sürüm görsel PDF okumaz.' if source.kind == 'pdf' else ''))
        self.sources.append(source)
        return source

    def add_transcript(self, segments, title='Ders kaydı'):
        """segments: start, end, text, original alanlı nesneler. Çeviri varsa orijinal de saklanır."""
        source = self._new_source('transkript', title)
        rows = [s for s in segments if s.text.strip()]
        group, length = [], 0
        def flush():
            if not group:
                return
            text = ' '.join(re.sub(r'\s+', ' ', s.text).strip() for s in group)
            original = ' '.join(re.sub(r'\s+', ' ', s.original or s.text).strip() for s in group)
            self._add_passage(source, f'{clock(group[0].start)}–{clock(group[-1].end)}', text,
                              original if original.casefold() != text.casefold() else '')
        for segment in rows:
            if group and length + len(segment.text) > CHUNK_CHARS:
                flush()
                group, length = [], 0
            group.append(segment)
            length += len(segment.text) + 1
        flush()
        return self._commit(source)

    def add_file(self, path, kind=None):
        """kind='transkript' yalnız TXT/Markdown için: ders kaydı dökümü olarak işaretler."""
        path = Path(path)
        suffix = path.suffix.lower()
        if not path.is_file():
            raise SourceError(f'{path.name}: dosya bulunamadı.')
        if any(s.path and Path(s.path) == path for s in self.sources):
            raise SourceError(f'{path.name} zaten eklendi.')
        if suffix in PDF_EXTENSIONS:
            return self.add_pdf(path)
        if suffix in TEXT_EXTENSIONS:
            return self.add_text(path, kind=kind or 'not')
        raise SourceError(f'{path.name}: bu sürüm yalnızca TXT, Markdown ve metin içeren PDF okur.')

    def add_text(self, path, title=None, kind='not'):
        """kind='transkript': DersYazı'nın dışa aktardığı konuşma dökümü (tanıma hatası içerebilir)."""
        path = Path(path)
        source = self._new_source(kind, title or path.name, path)
        text = clean(read_text_file(path))
        # Markdown başlıklarını konum olarak kullan; yoksa paragraf numarası.
        sections, heading, buffer = [], None, []
        for line in text.split('\n'):
            match = re.match(r'^#{1,6}\s+(.+)$', line.strip())
            if match:
                if '\n'.join(buffer).strip():
                    sections.append((heading, '\n'.join(buffer).strip()))
                heading, buffer = match.group(1).strip(), [line]
            else:
                buffer.append(line)
        if '\n'.join(buffer).strip():
            sections.append((heading, '\n'.join(buffer).strip()))
        paragraph = 0
        for heading, body in sections:
            for chunk in split_long(body):
                paragraph += 1
                location = f'bölüm “{heading[:40]}”' if heading else f'parça {paragraph}'
                self._add_passage(source, location, chunk)
        return self._commit(source)

    def add_pdf(self, path, title=None):
        path = Path(path)
        source = self._new_source('pdf', title or path.name, path)
        for number, text in pdf_pages(path):
            source.page_count = max(source.page_count, number)
            text = clean(text)
            if len(re.sub(r'\W', '', text)) < 20:
                source.unread_pages.append(number)
                continue
            chunks = split_long(text)
            for index, chunk in enumerate(chunks, 1):
                location = f's. {number}' + (f' ({index}/{len(chunks)})' if len(chunks) > 1 else '')
                self._add_passage(source, location, chunk, page=number)
        return self._commit(source)

    def add_web(self, page):
        """research.WebPage → web kaynağı. Ders kaynaklarından ayrı tutulur ve ayrı gösterilir."""
        source = self._new_source('web', f'Vikipedi ({page.lang}): “{page.title}”')
        source.url, source.retrieved, source.license = page.url, page.retrieved, page.license
        for number, chunk in enumerate(split_long(clean(page.text)), 1):
            self._add_passage(source, f'parça {number}', chunk)
        return self._commit(source)

    def lesson_passages(self):
        """İnternet dışı (dersin kendi) kaynak parçaları."""
        return [p for s in self.sources if s.kind != 'web' for p in s.passages]

    def remove(self, source_id):
        source = self.source(source_id)
        if source:
            self.sources.remove(source)
            for passage in source.passages:
                self._passages.pop(passage.id, None)

    def describe(self, passage_id):
        passage = self.passage(passage_id)
        if not passage:
            return None
        source = self.source(passage.source_id)
        if source.kind == 'web':
            return f'{source.title}, {passage.location} — {source.url} (erişim {source.retrieved}, {source.license})'
        return f'{source.title}, {passage.location}'

def pdf_pages(path):
    """(sayfa_no, metin) üretir. Qt PDF (PDFium) metin katmanını okur; OCR yapmaz."""
    from PySide6.QtPdf import QPdfDocument
    document = QPdfDocument()
    error = document.load(str(path))
    if error != QPdfDocument.Error.None_:
        names = {QPdfDocument.Error.IncorrectPassword: 'PDF parola korumalı.',
                 QPdfDocument.Error.UnsupportedSecurityScheme: 'PDF güvenlik şeması desteklenmiyor.',
                 QPdfDocument.Error.InvalidFileFormat: 'Geçerli bir PDF değil.',
                 QPdfDocument.Error.FileNotFound: 'PDF bulunamadı.'}
        raise SourceError(f'{Path(path).name}: ' + names.get(error, 'PDF açılamadı.'))
    try:
        for index in range(document.pageCount()):
            yield index + 1, document.getAllText(index).text()
    finally:
        document.close()
