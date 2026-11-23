"""Argos model paketleriyle yerel EN↔TR çeviri. Metin için ağ çağrısı yok."""
import json
import os
import shutil
import tempfile
import urllib.request
import zipfile
import hashlib
import urllib.error
import http.client
import re
from pathlib import Path, PurePosixPath

MODEL_ROOT = Path(__file__).resolve().parent / 'models' / 'translation'
INDEX = 'https://raw.githubusercontent.com/argosopentech/argospm-index/main/index.json'

class Cancelled(Exception):
    pass

EN_TR_SHA256 = '2d553a00880a0c21dea5b1c375535659e6bf18c9bf2ce9847c2a2fd2ff50316a'

def download_package(urls, archive, status, cancelled, expected_hash=None):
    failures = []
    for number, url in enumerate(urls, 1):
        if cancelled():
            raise Cancelled()
        status(f'Çeviri dosyaları hazırlanıyor · indirme kaynağı {number}/{len(urls)}')
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'DersYazi/1.0 (local translation model download)'})
            digest = hashlib.sha256()
            with urllib.request.urlopen(request, timeout=30) as response, Path(archive).open('wb') as output:
                total = int(response.headers.get('Content-Length', 0))
                received = 0
                while True:
                    if cancelled():
                        raise Cancelled()
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
                    digest.update(chunk)
                    received += len(chunk)
                    if received > 2 * 1024**3:
                        raise ValueError('İndirme beklenen dosya boyutunu aştı.')
                    status(f'Çeviri dosyaları indiriliyor · {received // 1048576} MB' +
                           (f' / {total // 1048576} MB' if total else ''))
            if total and received != total:
                raise ValueError('İndirme eksik kaldı.')
            if expected_hash and digest.hexdigest() != expected_hash:
                raise ValueError('İndirilen dosyanın bütünlük doğrulaması başarısız.')
            if not zipfile.is_zipfile(archive):
                raise ValueError('Sunucu geçerli bir model paketi göndermedi.')
            return
        except urllib.error.HTTPError as error:
            failures.append(f'Kaynak {number}: HTTP {error.code}')
        except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.IncompleteRead) as error:
            failures.append(f'Kaynak {number}: bağlantı kurulamadı veya kesildi')
        except ValueError as error:
            failures.append(f'Kaynak {number}: {error}')
        status('Bu kaynaktan indirilemedi · alternatif kaynak deneniyor' if number < len(urls)
               else 'İndirme tamamlanamadı')
    explanation = ('Sunuculardan biri HTTP 403 ile erişimi reddetti; bu, internet bağlantısının kapalı olduğu anlamına gelmez.'
                   if any('HTTP 403' in failure for failure in failures)
                   else 'Kaynaklara erişim veya indirilen dosyanın doğrulaması başarısız oldu.')
    raise RuntimeError('Çeviri dosyaları hiçbir kaynaktan indirilemedi. ' + explanation + '\n' + '\n'.join(failures))

def ensure_model(source, target, offline, status, cancelled, root=None):
    if (source, target) not in {('en', 'tr'), ('tr', 'en')}:
        raise ValueError('Bu sürümde çeviri İngilizce ↔ Türkçe arasında destekleniyor. Diğer diller için Orijinal dili koru seç.')
    root = Path(root) if root is not None else MODEL_ROOT
    destination = root / f'{source}-{target}'
    if (destination / 'model/model.bin').is_file() and (destination / 'sentencepiece.model').is_file():
        return destination
    if offline:
        raise RuntimeError('Çeviri modeli henüz indirilmemiş. Çevrimdışı seçeneğini kapat veya CeviriKurulum.bat dosyasını bir kez çalıştır.')
    root.mkdir(parents=True, exist_ok=True)
    status('Yerel çeviri modeli indiriliyor · kayıt ve metin gönderilmez')
    if (source, target) == ('en', 'tr'):
        # Resmi paket dizinindeki sabit sürüm; GitHub erişimi ayrıca gerekmiyor.
        urls = [
            'https://data.argosopentech.com/argospm/v1/translate-en_tr-1_5.argosmodel',
            'https://argosopentech.nyc3.digitaloceanspaces.com/argospm/translate-en_tr-1_5.argosmodel',
            'https://argos-net.com/v1/translate-en_tr-1_5.argosmodel',
        ]
    else:
        with urllib.request.urlopen(INDEX, timeout=30) as response:
            entries = json.load(response)
        package = next(p for p in entries if p['from_code'] == source and p['to_code'] == target)
        links = [link for link in package['links'] if link.startswith('https://')]
        filename = links[0].rsplit('/', 1)[-1]
        urls = ['https://data.argosopentech.com/argospm/v1/' + filename,
                'https://argosopentech.nyc3.digitaloceanspaces.com/argospm/' + filename] + links
    with tempfile.TemporaryDirectory(dir=root) as folder:
        archive = Path(folder) / 'model.zip'
        download_package(urls, archive, status, cancelled,
                         EN_TR_SHA256 if (source, target) == ('en', 'tr') else None)
        unpacked = Path(folder) / 'unpacked'
        with zipfile.ZipFile(archive) as z:
            for member in z.infolist():
                name = PurePosixPath(member.filename.replace('\\', '/'))
                if name.is_absolute() or '..' in name.parts or ':' in member.filename:
                    raise ValueError('Geçersiz model paketi yolu.')
                if member.file_size > 2 * 1024**3:
                    raise ValueError('Model paketi beklenenden büyük.')
            z.extractall(unpacked)
        candidates = list(unpacked.rglob('metadata.json'))
        installed = None
        for metadata in candidates:
            meta = json.loads(metadata.read_text(encoding='utf-8'))
            if meta.get('from_code') == source and meta.get('to_code') == target:
                installed = metadata.parent
                break
        if installed is None or not (installed / 'model/model.bin').is_file() or not (installed / 'sentencepiece.model').is_file():
            raise ValueError('Çeviri model paketinde gerekli dosyalar bulunamadı.')
        if cancelled():
            raise Cancelled()
        if destination.exists():
            # Yarım modelin üzerine yazmak yerine kullanıcıya açık hata göster.
            raise RuntimeError(f'Eksik çeviri model klasörünü yeniden adlandırıp tekrar dene: {destination}')
        shutil.move(str(installed), str(destination))
    return destination

class LocalTranslator:
    def __init__(self, source, target, offline, status, cancelled):
        try:
            import sentencepiece
        except ImportError as e:
            raise RuntimeError('Çeviri bileşeni kurulmamış. CeviriKurulum.bat dosyasını bir kez çalıştırıp uygulamayı yeniden aç.') from e
        folder = ensure_model(source, target, offline, status, cancelled)
        import ctranslate2
        self.tokenizer = sentencepiece.SentencePieceProcessor(model_file=str(folder / 'sentencepiece.model'))
        self.engine = ctranslate2.Translator(str(folder / 'model'), device='cpu', compute_type='int8',
                                            inter_threads=1, intra_threads=min(8, os.cpu_count() or 4))
        self.cancelled = cancelled
        meta = json.loads((folder / 'metadata.json').read_text(encoding='utf-8'))
        self.prefix = meta.get('target_prefix', '')
        self.target = target
        self.source = source

    def translate(self, text, careful=False):
        # Kaynakta açıkça bulunan teknik terimleri çeviride koru. Kaynakta olmayan
        # bir terimi tahmin ederek ekleme veya MSA gibi kısaltmaları değiştirme.
        if getattr(self, 'source', None) == 'en' and getattr(self, 'target', None) == 'tr':
            terms = [(r'\bgradient descent\b', 'gradyan inişi'),
                     (r'\bmean squared? error\b', 'ortalama karesel hata'),
                     (r'\bTaylor series\b', 'Taylor serisi')]
            protected, replacements = text, {}
            for i, (pattern, turkish) in enumerate(terms):
                marker = f'ZXQTERM{i}ZXQ'
                protected, count = re.subn(pattern, marker, protected, flags=re.IGNORECASE)
                if count:
                    replacements[marker] = turkish
            if replacements:
                output = self._translate(protected, careful)
                if all(marker.casefold() in output.casefold() for marker in replacements):
                    for marker, value in replacements.items():
                        output = re.sub(re.escape(marker), value, output, flags=re.IGNORECASE)
                    return output
                # Koruma işareti çevrilemediyse işareti kullanıcı metnine sızdırma.
        return self._translate(text, careful)

    def _translate(self, text, careful=False):
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+', text.strip()) if s.strip()]
        if len(sentences) > 1:
            return ' '.join(self.translate(sentence, careful=careful) for sentence in sentences)
        # Çok uzun bir bölüm sessizce kırpılmasın; tüm parçalar çevrilir.
        tokens = self.tokenizer.encode(text, out_type=str)
        translated = []
        chunk_size = 90 if careful else 180
        for start in range(0, len(tokens), chunk_size):
            if self.cancelled():
                raise Cancelled()
            options = {'target_prefix': [[self.prefix]]} if self.prefix else {}
            result = self.engine.translate_batch([tokens[start:start + chunk_size]], beam_size=8 if careful else 4,
                max_input_length=0, max_decoding_length=512, replace_unknowns=True, **options)
            words = result[0].hypotheses[0]
            value = self.tokenizer.decode(words)
            if self.prefix and value.startswith(self.prefix):
                value = value[len(self.prefix):]
            translated.append(value.strip())
        output = ' '.join(translated)
        if not careful:
            from language_checks import text_language_hint
            target = getattr(self, 'target', None)
            if target and text_language_hint(output) not in (None, target):
                retried = self.translate(text, careful=True)
                if retried.strip():
                    return retried
        if not careful and text.strip() and (not output.strip() or
                (len(text.split()) >= 4 and output.casefold().strip() == text.casefold().strip())):
            retried = self.translate(text, careful=True)
            return retried if retried.strip() else (output or text)
        return output

def setup():
    try:
        ensure_model('en', 'tr', False, print, lambda: False)
        translator = LocalTranslator('en', 'tr', True, print, lambda: False)
        sample = translator.translate('Today we will study mathematics. Students should take notes.')
        print('İngilizce → Türkçe test sonucu:', sample)
        if not sample.strip():
            raise RuntimeError('Çeviri testi boş çıktı üretti.')
    except Exception as error:
        print('\nKurulum tamamlanamadı:\n' + str(error))
        return 1
    return 0

if __name__ == '__main__':
    raise SystemExit(setup())
