"""Gerçek yerel modelle uçtan uca föy denemesi ve ölçüm. Sahte model kullanmaz.

Kullanım:
  .venv\\Scripts\\python.exe foy_e2e.py --cikti ornekler\\foy-e2e\\sonuc --transkript ders-ornek-kontrol.json
      ornekler\\foy-e2e\\hoca-ders-notu.pdf ornekler\\foy-e2e\\ogrenci-notlarim.md
Çıktı: calisma-kagidi.md, calisma-kagidi.html, olcum.json. Ders metni dışarı gönderilmez.
"""
import argparse
import json
import subprocess
import threading
import time
from pathlib import Path
from automatic import inspect_hardware
from core import Segment
from sources import SourceLibrary
import llm
import worksheet
import research

def gpu_used_mb():
    try:
        out = subprocess.run(['nvidia-smi', '--query-gpu=memory.used', '--format=csv,noheader,nounits'],
                             capture_output=True, text=True, timeout=5,
                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)).stdout
        return int(out.strip().splitlines()[0])
    except (OSError, ValueError, IndexError, subprocess.SubprocessError):
        return None

def load_segments(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    rows = []
    for item in data:
        for s in item.get('segments', [item]):
            rows.append(Segment(s['start'], s['end'], s['text'].strip(), s.get('original', ''), item.get('source_language', '')))
    return rows

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('kaynaklar', nargs='*')
    parser.add_argument('--transkript')
    parser.add_argument('--transkript-metin', action='append', default=[],
                        help='DersYazı TXT dökümü; ders kaydı olarak işaretlenir')
    parser.add_argument('--odak', default='')
    parser.add_argument('--internetsiz', action='store_true', help='Vikipedi ek araştırmasını kapat')
    parser.add_argument('--cikti', required=True)
    args = parser.parse_args()
    out = Path(args.cikti)
    out.mkdir(parents=True, exist_ok=True)

    library = SourceLibrary()
    if args.transkript:
        library.add_transcript(load_segments(args.transkript), f'Ders kaydı ({Path(args.transkript).name})')
    for path in args.transkript_metin:
        library.add_text(path, kind='transkript')
    for path in args.kaynaklar:
        library.add_file(path)
    for s in library.sources:
        print(s.id, s.title, s.summary(), flush=True)

    before = inspect_hardware()
    samples, stop = [], threading.Event()
    def sample():
        while not stop.is_set():
            used = gpu_used_mb()
            free = inspect_hardware().available_mb
            samples.append((used, free))
            stop.wait(1.0)
    threading.Thread(target=sample, daemon=True).start()

    client = llm.OllamaClient()
    started = time.monotonic()
    plan = llm.prepare(client, before, False, lambda m: print('  ', m, flush=True), lambda: False)
    ready = time.monotonic()
    model = worksheet.LocalModel(client, plan, lambda: False)
    sheet = worksheet.build_worksheet(library, model, lambda: False,
                                      lambda text, step, total: print(f'[{step}/{total}] {text}', flush=True), args.odak,
                                      None if args.internetsiz else research.research)
    loaded = client.loaded()
    client.unload(plan.name)
    client.stop()  # yalnızca bu betiğin başlattığı sunucu kapanır
    stop.set()

    markdown = worksheet.render_markdown(sheet)
    (out / 'calisma-kagidi.md').write_text(markdown, encoding='utf-8')
    (out / 'calisma-kagidi.html').write_text('<!doctype html><html lang="tr"><head><meta charset="utf-8"><title>Çalışma kağıdı'
        '</title></head><body style="background:#f2e9d9;max-width:860px;margin:24px auto;padding:24px;">'
        + worksheet.render_html(sheet) + '</body></html>', encoding='utf-8')
    (out / 'icerik.json').write_text(json.dumps(sheet.content, ensure_ascii=False, indent=2), encoding='utf-8')
    gpu = [u for u, _ in samples if u is not None]
    seconds = sheet.stats.get('seconds') or 1
    report = {
        'model': plan.name, 'plan': plan.reason, 'num_ctx': plan.num_ctx, 'gpu': plan.gpu,
        'hazirlik_sn': round(ready - started, 1), 'uretim_sn': sheet.stats.get('seconds'),
        'asamalar_sn': sheet.stats.get('stages'), 'mod': sheet.stats.get('mode'),
        'cagri': sheet.stats.get('calls'), 'yeniden_deneme': sheet.stats.get('retries'),
        'girdi_token': sheet.stats.get('prompt_tokens'), 'cikti_token': sheet.stats.get('output_tokens'),
        'ortalama_cikti_token_sn': round((sheet.stats.get('output_tokens') or 0) / seconds, 1),
        'vram_baslangic_kullanim_mb': gpu[0] if gpu else None,
        'vram_tepe_kullanim_mb': max(gpu) if gpu else None,
        'ollama_model_vram_mb': sum(m.get('size_vram', 0) for m in loaded) // 1048576,
        'bos_ram_en_dusuk_mb': min(f for _, f in samples) if samples else None,
        'uyarilar': sheet.warnings,
        'internet': {'durum': sheet.content.get('internet_durumu'), 'sorgular': sheet.content.get('arama_sorgulari'),
                     'sayfalar': [s.url for s in library.sources if s.kind == 'web'],
                     'ek_arastirma_madde': len(sheet.content.get('ek_arastirma', []))},
        'ornek_etiketleri': [(e.get('model_etiketi', e.get('dayanak')), e.get('dayanak'), e.get('dayanak_notu', ''))
                             for e in sheet.content.get('cozumlu_ornekler', [])],
        'tarama': {'kabul': sheet.stats.get('scan_flagged', 0), 'red': sheet.stats.get('scan_rejected', 0)},
        'enjeksiyon_metni_ciktida': 'ŞİFRE' in markdown or '1234' in markdown,
        'kaynaklar': [{'id': s.id, 'baslik': s.title, 'ozet': s.summary()} for s in library.sources],
    }
    (out / 'olcum.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
