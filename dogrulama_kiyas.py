"""Doğrulama/düzeltme hattını fixture üzerinde gerçek yerel modelle çalıştırır ve raporlar.

Kullanım:
  .venv\\Scripts\\python.exe dogrulama_kiyas.py                      (çalıştır + ham kayıt + rapor)
  .venv\\Scripts\\python.exe dogrulama_kiyas.py --rapor <klasör>     (elle-etiket.json ile raporu yeniden üret)

GPU paylaşımı: kendi Ollama sunucusu ayrı portta (11436) başlatılır; ayrı port GPU'yu ayırmaz. Bu yüzden her model
çağrısından önce kullanıcının motorunda (11435) yüklü model olup olmadığı salt-okunur /api/ps ile ve GPU belleği
nvidia-smi ile denetlenir; meşgulse beklenir. Kullanıcı motoruna istek gönderilmez, o motor kapatılmaz.
Modele yalnız id, metin, bağlam gider; altın/not/kaynak alanları gitmez (test_verify).
Ham model yanıtları (biçimlendirme, yargı, düzeltme) ham-kayit.json içinde 'model_yanitlari' altında saklanır.
"""
import argparse
import json
import subprocess
import threading
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from automatic import inspect_hardware
import llm
import verify
import worksheet

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / 'ornekler' / 'dogrulama' / 'fixture-2026-10-16.json'
CACHE = ROOT / 'ornekler' / 'dogrulama' / 'kanit-onbellek'
USER_ENGINE = 'http://127.0.0.1:11435'
OWN_HOST = '127.0.0.1:11436'
# Kullanıcı föyündeki eski denetçi uyarıları (karşılaştırma için; modele verilmez).
PREVIOUS = {'Y1': 'işaret yok', 'Y2': 'doğru uyarı', 'Y3': 'doğru uyarı', 'Y4': 'yanlış gerekçeli uyarı (0.04 hakkında)',
            'Y5': 'doğru uyarı', 'Y6': 'işaret yok', 'Y8': 'işaret yok', 'Y9': 'yanlış gerekçeli uyarı (tekil/tanımsız)',
            'Y11': 'işaret yok', 'D1': 'kaynakta yok notu', 'D3': 'kaynakta yok notu', 'D4': 'işaret yok',
            'D7': 'işaret yok', 'D9': 'yanlış alarm'}

def gpu_used_mb():
    try:
        out = subprocess.run(['nvidia-smi', '--query-gpu=memory.used', '--format=csv,noheader,nounits'],
                             capture_output=True, text=True, timeout=5,
                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)).stdout
        return int(out.strip().splitlines()[0])
    except (OSError, ValueError, IndexError, subprocess.SubprocessError):
        return None

def user_engine_busy():
    """Kullanıcı motorunda yüklü model var mı (salt-okunur durum sorgusu)."""
    try:
        with urllib.request.urlopen(USER_ENGINE + '/api/ps', timeout=3) as response:
            return bool(json.loads(response.read().decode('utf-8')).get('models'))
    except (OSError, ValueError):
        return False  # motor kapalı → meşgul değil

class GuardedModel:
    """Her çağrıdan önce GPU'nun başka bir model işinde olmadığını doğrular; değilse bekler."""
    def __init__(self, inner, own_client, log, max_wait=900):
        self.inner, self.own, self.log, self.max_wait = inner, own_client, log, max_wait
        self.name = inner.name
        self.waited = 0.0

    def generate(self, *args, **kwargs):
        started = time.monotonic()
        while True:
            own_loaded = sum(m.get('size_vram', 0) for m in self.own.loaded()) // 1048576
            used = gpu_used_mb()
            foreign = (used - own_loaded) if used is not None else 0
            if not user_engine_busy() and foreign < 1500:
                break
            if time.monotonic() - started > self.max_wait:
                raise verify.BudgetExceeded('GPU başka bir işte; bekleme süresi doldu')
            self.log.append(f'{time.strftime("%H:%M:%S")} GPU meşgul (kullanıcı motoru veya {foreign} MiB yabancı); bekleniyor')
            time.sleep(10)
        self.waited += time.monotonic() - started
        return self.inner.generate(*args, **kwargs)

def category(record, gold, label=None):
    state = record['durum']
    if label:
        return label
    # Ölçüler: hatalı temizlendi / temiz korundu / yanlış doğrulandı / çözülemedi (onaylanmadan kaldı veya çıkarıldı).
    if gold == 'yanlis':
        if state == 'duzeltildi':
            return 'hatalı temizlendi (elle teyit gerekli)'
        if state in ('dogrulandi', 'hesap_tutarli'):
            return f'yanlış doğrulandı ({state})'
        if state == 'cozulemedi':
            return 'çözülemedi (ana metinden çıktı, ekte açık)'
        return f'çözülemedi (onaylanmadan kaldı: {state})'
    if state in ('dogrulandi', 'kontrol_disi', 'hesap_tutarli', 'kanit_yetersiz', 'yorum_denetlenemedi', 'denetlenmedi'):
        return f'temiz korundu ({state})'
    if state == 'duzeltildi':
        return 'temiz cümle değişti (inceleme gerekli)'
    return 'temiz içerik kaybı (ekte)'

def report(folder):
    folder = Path(folder)
    raw = json.loads((folder / 'ham-kayit.json').read_text(encoding='utf-8'))
    labels_path = folder / 'elle-etiket.json'
    labels = json.loads(labels_path.read_text(encoding='utf-8')) if labels_path.is_file() else {}
    units = {u['id']: u for u in raw['birimler']}
    rows, counts = [], {}
    for record in raw['sonuclar']:
        unit = units[record['id']]
        cat = category(record, unit['altin'], labels.get(record['id'], {}).get('kategori'))
        counts[cat] = counts.get(cat, 0) + 1
        rows.append((unit, record, cat, labels.get(record['id'], {}).get('not', '')))
    s = raw['olcum']
    out = [f'# Doğrulama/düzeltme kıyası · {raw["zaman"]}', '',
           f'Model: {raw["model"]} (bağlam {raw["baglam"]}), kendi sunucu {OWN_HOST}. Süre {s["total_seconds"]} sn, '
           f'{s["calls"]} model çağrısı, {s["web_requests"]} web isteği (önbellek dışı), aşama kullanımı {s.get("stage_use")}, '
           f'süre sınırı: {s["limit"] or "aşılmadı"}. '
           f'VRAM tepe {raw["kaynak"]["vram_tepe_mb"]} MiB, boş RAM en düşük {raw["kaynak"]["bos_ram_min_mb"]} MB, '
           f'GPU bekleme {raw["kaynak"]["gpu_bekleme_sn"]} sn. Ham model yanıtı: {len(raw.get("model_yanitlari", []))} '
           f'(ham-kayit.json → model_yanitlari).', '',
           '## Özet', ''] + [f'- {k}: {v}' for k, v in sorted(counts.items())] + ['', '## Birimler', '']
    for unit, record, cat, note in rows:
        out += [f'### {unit["id"]} · {unit["tur"]} · altın: {unit["altin"]} → **{cat}**', '',
                f'- Önceki denetçi: {PREVIOUS.get(unit["id"], "-")}',
                f'- Hat kararı: `{record["durum"]}`' + (f' — {record.get("neden")}' if record.get('neden') else ''),
                f'- Orijinal: {record["orijinal"]}',
                f'- Son metin: {record["son_metin"] if record["son_metin"] is not None else "— (ana metinden çıkarıldı)"}']
        if record.get('duzeltme'):
            out.append(f'- Önerilen düzeltme: {record["duzeltme"]} ({record.get("degisiklik", "")})')
        if record.get('duzeltme_yolu'):
            choice = record.get('anlam_secimi', {})
            tried = ', '.join(f'{c["tur"]}: {c["sonuc"][0]}' for c in choice.get('adaylar', []))
            out.append(f'- Düzeltme yolu: {record["duzeltme_yolu"]}; iddia edilen anlam {choice.get("iddia_edilen")}, '
                       f'denenen: {tried or "-"}, seçilen: {choice.get("secilen", "yok")}')
        if record.get('duzeltme_kaynagi'):
            out.append('- Dayanak: ' + ' | '.join(record['duzeltme_kaynagi']))
        if record.get('ders_kaynagi'):
            out.append('- Özgün ifadenin ders kaynağı (kanıt değildir): ' + ', '.join(record['ders_kaynagi']))
        if note:
            out.append(f'- Elle değerlendirme: {note}')
        out.append('')
    (folder / 'rapor.md').write_text('\n'.join(out), encoding='utf-8')
    return counts

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rapor')
    parser.add_argument('--cikti')
    parser.add_argument('--birimler', help='virgülle ayrılmış fixture kimlikleri (ör. Y2,Y4,D1,D9)')
    parser.add_argument('--onbellek', action='store_true', help='yalnız yerel kanıt önbelleği; web isteği yok')
    args = parser.parse_args()
    if args.rapor:
        print(report(args.rapor))
        return
    out = Path(args.cikti or ROOT / 'ornekler' / 'dogrulama' / f'sonuc-{datetime.now():%Y%m%d-%H%M}')
    out.mkdir(parents=True, exist_ok=True)
    fixture = json.loads(FIXTURE.read_text(encoding='utf-8'))
    chosen = set(args.birimler.split(',')) if args.birimler else None
    fixture['birimler'] = [u for u in fixture['birimler'] if chosen is None or u['id'] in chosen]
    units = [{'id': u['id'], 'metin': u['metin'], 'baglam': u.get('baglam', ''), 'kaynaklar': u.get('kaynaklar', [])}
             for u in fixture['birimler']]
    if user_engine_busy():
        print('Kullanıcı motorunda yüklü model var; GPU boşalınca başlanacak.', flush=True)
    samples, stop, log = [], threading.Event(), []
    def sample():
        while not stop.is_set():
            samples.append((gpu_used_mb(), inspect_hardware().available_mb))
            stop.wait(1.0)
    threading.Thread(target=sample, daemon=True).start()
    client = llm.OllamaClient(host=OWN_HOST)
    client.ensure_running(print, lambda: False)
    plan = llm.ModelPlan('qwen3.5:9b', 8192, True, 'doğrulama (küçük bağlam)')
    model = GuardedModel(worksheet.LocalModel(client, plan, lambda: False), client, log)
    evidence = verify.EvidenceStore(CACHE, offline=args.onbellek)
    verifier = verify.Verifier(model, evidence, on_status=lambda m: print(time.strftime('%H:%M:%S'), m, flush=True),
                               budget=verify.Budget(max_units=20, max_seconds=900, biçimlendirme=8, kanıt_yargısı=16,
                                                                düzeltme=8, web=24))
    try:
        results = verifier.run(units)
    finally:
        client.unload(plan.name)
        client.stop()  # yalnız bu betiğin başlattığı sunucu
        stop.set()
    gpu = [g for g, _ in samples if g is not None]
    raw = {'zaman': f'{datetime.now():%d.%m.%Y %H:%M}', 'model': plan.name, 'baglam': plan.num_ctx,
           'birimler': fixture['birimler'], 'sonuclar': results, 'olcum': verifier.stats,
           'model_yanitlari': verifier.raw,
           'mod': 'yalnız önbellek' if args.onbellek else 'web + önbellek',
           'kaynak': {'vram_tepe_mb': max(gpu) if gpu else None, 'bos_ram_min_mb': min(r for _, r in samples) if samples else None,
                      'gpu_bekleme_sn': round(model.waited, 1), 'bekleme_kaydi': log[-20:],
                      'web_hatalari': evidence.errors, 'sympy_yeniden_baslatma': verifier.sympy.restarts}}
    (out / 'ham-kayit.json').write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report(out), ensure_ascii=False), flush=True)
    print('çıktı:', out, flush=True)

if __name__ == '__main__':
    main()
