"""Yerel dil modeli adaptörü (Ollama). Model ve donanım seçimi otomatiktir.

Uygulama kendi Ollama kopyasını .runtime/ollama altından yalnızca 127.0.0.1 üzerinde başlatır;
model dosyaları models/ollama altında tutulur. Ders metni hiçbir dış servise gönderilmez;
ağ yalnızca ilk model indirmesinde (ollama.com kayıt deposu) kullanılır.
"""
import json
import os
import queue
import subprocess
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OLLAMA_EXE = ROOT / '.runtime' / 'ollama' / 'ollama.exe'
OLLAMA_MODELS = ROOT / 'models' / 'ollama'
HOST = '127.0.0.1:11435'

class Cancelled(Exception):
    pass

class ModelError(Exception):
    pass

@dataclass(frozen=True)
class ModelPlan:
    name: str
    num_ctx: int
    gpu: bool
    reason: str

# Lisans: Qwen3.5 ağırlıkları Apache-2.0 (huggingface.co/Qwen/Qwen3.5-9B). Sıra: kaliteden hıza.
CANDIDATES = ('qwen3.5:9b', 'qwen3.5:4b')

def choose_model(hardware, installed=()):
    """Boş VRAM/RAM'e göre güvenli pay bırakarak model seç. Kullanıcıya soru sorulmaz."""
    if hardware.cuda and hardware.gpu_free_mb >= 9000:
        # 24K bağlam: düşünme modlu denetim ~12K token üretebiliyor. Qwen3.5'in KV önbelleği küçük
        # (16K'da 512 MiB ölçüldü); toplam VRAM ~7,5 GB'ı geçmez.
        plan = ModelPlan('qwen3.5:9b', 24576, True, 'Ekran kartında yeterli bellek var.')
    elif hardware.cuda and hardware.gpu_free_mb >= 5500:
        plan = ModelPlan('qwen3.5:4b', 16384, True, 'Ekran kartı belleği sınırlı; daha küçük model.')
    elif hardware.available_mb >= 10000:
        plan = ModelPlan('qwen3.5:9b', 8192, False, 'Ekran kartı kullanılamıyor; işlemci ile yavaş çalışır.')
    else:
        plan = ModelPlan('qwen3.5:4b', 8192, False, 'Ekran kartı/bellek sınırlı; küçük model, yavaş çalışır.')
    if installed and plan.name not in installed:
        # İnternetsiz çalışmada indirilmiş en iyi adayı kullan.
        for name in CANDIDATES:
            if name in installed:
                return ModelPlan(name, plan.num_ctx, plan.gpu, plan.reason + ' İndirilmiş model kullanılıyor.')
    return plan

def _stream(request, cancelled, timeout=600):
    """NDJSON akışını satır satır ver; iptal edilirse bağlantıyı hemen kapat."""
    lines = queue.Queue()
    holder = {}
    def reader():
        try:
            response = urllib.request.urlopen(request, timeout=timeout)
            holder['response'] = response
            for raw in response:
                lines.put(('line', raw))
            lines.put(('end', None))
        except Exception as error:
            lines.put(('error', error))
    thread = threading.Thread(target=reader, daemon=True)
    thread.start()
    try:
        while True:
            if cancelled():
                raise Cancelled()
            try:
                kind, value = lines.get(timeout=0.25)
            except queue.Empty:
                continue
            if kind == 'end':
                return
            if kind == 'error':
                if cancelled():
                    raise Cancelled()
                raise value
            raw = value.strip()
            if raw:
                yield json.loads(raw)
    finally:
        response = holder.get('response')
        if response is not None:
            try:
                response.close()
            except Exception:
                pass

class OllamaClient:
    def __init__(self, host=HOST, executable=OLLAMA_EXE, models_dir=OLLAMA_MODELS):
        self.base = f'http://{host}'
        self.host = host
        self.executable = Path(executable)
        self.models_dir = Path(models_dir)
        self.process = None

    def _request(self, path, payload=None, method=None):
        data = json.dumps(payload).encode('utf-8') if payload is not None else None
        return urllib.request.Request(self.base + path, data=data, method=method or ('POST' if data else 'GET'),
                                      headers={'Content-Type': 'application/json'})

    def _get_json(self, path, payload=None, timeout=10):
        with urllib.request.urlopen(self._request(path, payload), timeout=timeout) as response:
            return json.loads(response.read().decode('utf-8'))

    def alive(self):
        try:
            return 'version' in self._get_json('/api/version', timeout=2)
        except (OSError, ValueError, urllib.error.URLError):
            return False

    def ensure_running(self, on_status, cancelled):
        if self.alive():
            return
        if not self.executable.is_file():
            raise ModelError('Çalışma kağıdı motoru bu bilgisayarda kurulu değil. '
                             'İnternet açıkken Çalışma kağıdı oluştur düğmesi onu otomatik indirir.')
        self.models_dir.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ, OLLAMA_HOST=self.host, OLLAMA_MODELS=str(self.models_dir),
                   OLLAMA_KEEP_ALIVE='5m', OLLAMA_NUM_PARALLEL='1', OLLAMA_MAX_LOADED_MODELS='1',
                   OLLAMA_NO_CLOUD='1')
        on_status('Çalışma kağıdı motoru başlatılıyor')
        log = (ROOT / '.runtime' / 'ollama-sunucu.log').open('ab')
        self.process = subprocess.Popen([str(self.executable), 'serve'], env=env, stdout=log, stderr=log,
                                        stdin=subprocess.DEVNULL, cwd=str(self.executable.parent),
                                        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        log.close()
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            if cancelled():
                raise Cancelled()
            if self.process.poll() is not None:
                raise ModelError('Çalışma kağıdı motoru başlatılamadı. Ayrıntı: .runtime/ollama-sunucu.log')
            if self.alive():
                return
            time.sleep(0.3)
        raise ModelError('Çalışma kağıdı motoru zamanında yanıt vermedi.')

    def stop(self):
        """Yalnızca bu uygulamanın başlattığı sunucuyu kapat."""
        if self.process and self.process.poll() is None:
            if os.name == 'nt':
                # Ollama'nın alt llama-server süreçlerini sahipsiz bırakma.
                # Yalnız bu istemcinin başlattığı, halen yaşayan süreç ağacı.
                try:
                    subprocess.run(['taskkill', '/PID', str(self.process.pid), '/T', '/F'],
                                   capture_output=True, timeout=10,
                                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                except (OSError, subprocess.TimeoutExpired):
                    pass
                if self.process.poll() is not None:
                    self.process = None
                    return
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None

    def installed(self):
        return {m['name'] for m in self._get_json('/api/tags').get('models', [])}

    def pull(self, name, on_status, cancelled, stall_seconds=90, restarts=3):
        """Modeli indir. İlerleme durursa isteği yeniden başlat; Ollama kaldığı parçadan devam eder."""
        for attempt in range(restarts + 1):
            if self._pull_once(name, on_status, cancelled, stall_seconds):
                return
            on_status('İndirme yavaşladı · bağlantı yenileniyor, kaldığı yerden devam edecek')
        raise ModelError('Model indirmesi ilerlemiyor. İnternet bağlantısını kontrol edip tekrar dene; '
                         'indirilen kısım korunur.')

    def _pull_once(self, name, on_status, cancelled, stall_seconds):
        last_change = time.monotonic()
        layers = {}  # Ollama ilerlemeyi katman katman bildirir; kullanıcıya toplamı göster.
        best = 0
        window = []  # (zaman, bayt): hız son ~30 sn'den; devam ettirilen eski baytlar sayılmaz
        stalled = lambda: cancelled() or time.monotonic() - last_change > stall_seconds
        try:
            for event in _stream(self._request('/api/pull', {'model': name, 'stream': True}), stalled, timeout=120):
                if 'error' in event:
                    raise ModelError('Model indirilemedi: ' + str(event['error']))
                if event.get('status') == 'success':
                    return True
                if event.get('total'):
                    layers[event.get('digest', '')] = (event['total'], event.get('completed') or 0)
                total = sum(t for t, _ in layers.values())
                done = sum(c for _, c in layers.values())
                if done > best:
                    best, last_change = done, time.monotonic()
                elif not total:
                    last_change = time.monotonic()  # manifest/doğrulama aşaması
                if total and done:
                    now = time.monotonic()
                    window.append((now, done))
                    while len(window) > 2 and now - window[0][0] > 30:
                        window.pop(0)
                    rate = max(0, done - window[0][1]) / max(now - window[0][0], 1) / 1048576
                    on_status(f'Çalışma kağıdı modeli indiriliyor (ilk kullanım) · {done / 1073741824:.1f} / '
                              f'{total / 1073741824:.1f} GB · {rate:.1f} MB/sn')
                elif event.get('status'):
                    on_status('Çalışma kağıdı modeli hazırlanıyor · ' + event['status'])
        except Cancelled:
            if cancelled():
                raise
            return False
        return True

    def chat(self, plan, messages, cancelled, schema=None, on_progress=None, temperature=0.6, max_tokens=4096, think=False):
        """Tam yanıt metnini ve ölçümleri döndür. Düşünme modu varsayılan kapalı; düşünme metni yanıta katılmaz."""
        payload = {'model': plan.name, 'messages': messages, 'stream': True, 'think': bool(think),
                   'keep_alive': '5m',
                   'options': {'temperature': temperature, 'top_p': 0.8, 'top_k': 20,
                               'presence_penalty': 1.5 if schema is None else 0.0,
                               'num_ctx': plan.num_ctx, 'num_predict': max_tokens}}
        if schema is not None:
            payload['format'] = schema
        if not plan.gpu:
            payload['options']['num_gpu'] = 0
        parts, stats, thought = [], {}, 0
        try:
            events = _stream(self._request('/api/chat', payload), cancelled)
            first = next(events, None)
        except urllib.error.HTTPError as error:
            # Ör. gemma4:12b bu GPU'da Flash Attention çekirdeğinde çöktü → Ollama HTTP 500 (16.10.2026).
            detail = ''
            try:
                detail = json.loads(error.read().decode('utf-8')).get('error', '')
            except Exception:
                pass
            raise ModelError(f'Yerel model çalıştırılamadı (HTTP {error.code}). {detail}'.strip())
        def chained():
            if first is not None:
                yield first
            yield from events
        for event in chained():
            if 'error' in event:
                raise ModelError(str(event['error']))
            message = event.get('message', {})
            content = message.get('content', '')
            thought += len(message.get('thinking', '') or '')
            if content:
                parts.append(content)
            if (content or message.get('thinking')) and on_progress:
                # Düşünme sırasında da ilerleme göster; yoksa pencere dakikalarca donmuş görünür.
                on_progress(sum(len(p) for p in parts) + thought)
            if event.get('done'):
                stats = {k: event.get(k) for k in ('prompt_eval_count', 'eval_count', 'eval_duration',
                                                   'prompt_eval_duration', 'total_duration', 'done_reason')}
        return ''.join(parts), stats

    def loaded(self):
        try:
            return self._get_json('/api/ps').get('models', [])
        except (OSError, ValueError, urllib.error.URLError):
            return []

    def unload(self, name):
        """İş bitince VRAM'i transkripsiyon için boşalt."""
        try:
            self._get_json('/api/generate', {'model': name, 'keep_alive': 0}, timeout=30)
        except (OSError, ValueError, urllib.error.URLError):
            pass

# Resmî GitHub sürümü; özet GitHub release varlık kaydından (digest) alındı.
ENGINE_VERSION = 'v0.40.5'
ENGINE_URL = f'https://github.com/ollama/ollama/releases/download/{ENGINE_VERSION}/ollama-windows-amd64.zip'
ENGINE_SHA256 = '5134ce7e3bc8e94d0494721c799ec293b429450d0c52461b0ee3647dd3bb4bb7'

def install_engine(target, on_status, cancelled, url=ENGINE_URL, expected=ENGINE_SHA256):
    """Ollama'yı sistem geneline kurmadan proje klasörüne indir, doğrula ve aç."""
    import hashlib
    import shutil
    import zipfile
    target = Path(target)
    staging = target.parent / 'indirme'
    staging.mkdir(parents=True, exist_ok=True)
    archive = staging / Path(url).name
    digest = hashlib.sha256()
    if archive.is_file():
        with archive.open('rb') as existing:
            for chunk in iter(lambda: existing.read(1 << 20), b''):
                digest.update(chunk)
    if digest.hexdigest() != expected:
        digest = hashlib.sha256()
        request = urllib.request.Request(url, headers={'User-Agent': 'DersYazi/1.0'})
        started = time.monotonic()
        with urllib.request.urlopen(request, timeout=60) as response, archive.open('wb') as output:
            total = int(response.headers.get('Content-Length', 0))
            received = 0
            while True:
                if cancelled():
                    raise Cancelled()
                chunk = response.read(1 << 20)
                if not chunk:
                    break
                output.write(chunk)
                digest.update(chunk)
                received += len(chunk)
                rate = received / max(time.monotonic() - started, 1) / 1048576
                on_status(f'Föy motoru indiriliyor (ilk kullanım) · {received // 1048576} / {total // 1048576} MB · {rate:.1f} MB/sn')
        if digest.hexdigest() != expected:
            archive.unlink(missing_ok=True)
            raise ModelError('Föy motoru indirmesinin bütünlük doğrulaması başarısız; dosya silindi. Tekrar dene.')
    on_status('Föy motoru açılıyor')
    temporary = target.with_name(target.name + '-yeni')
    shutil.rmtree(temporary, ignore_errors=True)
    with zipfile.ZipFile(archive) as package:
        root = temporary.resolve()
        for member in package.namelist():
            if not (temporary / member).resolve().is_relative_to(root):
                raise ModelError('Föy motoru paketinde geçersiz dosya yolu var.')
        package.extractall(temporary)
    if not (temporary / 'ollama.exe').is_file():
        raise ModelError('Föy motoru paketinde ollama.exe bulunamadı.')
    shutil.rmtree(target, ignore_errors=True)
    temporary.rename(target)
    archive.unlink(missing_ok=True)

def prepare(client, hardware, offline, on_status, cancelled):
    """Motoru başlat, modeli seç ve gerekirse indir. ModelPlan döndür."""
    if not client.alive() and not client.executable.is_file():
        if offline:
            raise ModelError('İnternetsiz çalışmada föy motoru henüz indirilmemiş. '
                             'İnternetsiz çalış seçeneğini kapatıp ilk indirmeyi tamamla.')
        install_engine(client.executable.parent, on_status, cancelled)
    client.ensure_running(on_status, cancelled)
    # Önceki işten bellekte kalan kendi modelimiz VRAM'i dolu gösterir; onu boş say, yoksa
    # gereksiz yere işlemci planı (çok yavaş) seçilir. 16.10.2026'da gerçek olarak yaşandı.
    held = sum(m.get('size_vram', 0) for m in client.loaded()) // 1048576
    if held and hardware.cuda:
        from dataclasses import replace
        hardware = replace(hardware, gpu_free_mb=hardware.gpu_free_mb + held)
    installed = client.installed()
    plan = choose_model(hardware, installed if offline else ())
    if plan.name not in installed:
        if offline:
            raise ModelError('İnternetsiz çalışmada çalışma kağıdı modeli henüz indirilmemiş. '
                             'İnternetsiz çalış seçeneğini kapatıp ilk indirmeyi tamamla.')
        client.pull(plan.name, on_status, cancelled)
    return plan
