"""Föy denetimi kıyası: aynı föy üzerinde tekrarlı bağımsız denetim turları, farklı modeller.

Kullanım: .venv\\Scripts\\python.exe denetim_kiyas.py --model qwen3.5:9b --tur 2 --cikti kisisel\\denetim-kiyas
Uygulamadaki Builder.scan aynen kullanılır (düşünme modu, madde madde, birebir alıntı şartı).
Altın etiketler: 13.10.2026 dersinden üretilen iki föyde elle doğrulanmış sorunlu maddeler (GELISTIRME-DURUMU 5c).
"""
import argparse
import copy
import json
import time
from pathlib import Path
from sources import SourceLibrary
import llm
import worksheet

TRANSCRIPT = Path(__file__).resolve().parent.parent / '13-10-2026-paragraf-duzeni.txt'
FOYS = {
    'A': ('kisisel/foy-13-10-2026-sadakat/icerik.json',
          {'A2': 'geri yayılım = GD uzantısı', 'T6': 'geri yayılım = GD uzantısı', 'A5': 'Delta İtalyanca/Latince; x farkı y ekseninde',
           'O5': 'Delta İtalyanca/Latince', 'A6': '"sel yüzeyler"', 'C1': 'tek fonksiyon y eksenine simetrik'}),
    'B': ('kisisel/foy-13-10-2026-sadakat-2/icerik.json',
          {'A3': 'GD = geri yayılım uzantısı', 'A4': 'merkezi fark tüm geriye dönük; +h geriye dönük',
           'T7': '+h geriye dönük fark', 'O4': 'analitik sonuç 2²/2 = 2'}),
}

def item_ids(content):
    ids = {}
    for key, prefix in (('anlatim', 'A'), ('terimler', 'T'), ('formuller', 'F'), ('ek_arastirma', 'E'),
                        ('cozumlu_ornekler', 'O'), ('alistirmalar', 'C')):
        for number, item in enumerate(content.get(key, []), 1):
            ids[id(item)] = f'{prefix}{number}'
    return ids

def run_scan(model, library, content):
    content = copy.deepcopy(content)
    for key in ('anlatim', 'terimler', 'formuller', 'ek_arastirma', 'cozumlu_ornekler', 'alistirmalar'):
        for item in content.get(key, []):
            item.pop('olasi_hata', None)
    builder = worksheet.Builder(library, model, lambda: False, lambda *a: None)
    builder.total = 1
    started = time.monotonic()
    builder.scan(content)
    seconds = round(time.monotonic() - started, 1)
    ids, flags = item_ids(content), []
    for key in ('anlatim', 'terimler', 'formuller', 'ek_arastirma', 'cozumlu_ornekler', 'alistirmalar'):
        for item in content.get(key, []):
            for problem in item.get('olasi_hata', []):
                flags.append({'madde': ids[id(item)], 'tur': problem['tur'], 'ifade': problem['ifade'], 'neden': problem['neden']})
    return {'sn': seconds, 'cikti_token': builder.stats.get('output_tokens'), 'isaretler': flags,
            'red': builder.stats.get('scan_rejected_items', []), 'degerlendirilen': builder.stats.get('scan_reviewed'),
            'madde': builder.stats.get('scan_items'), 'uyarilar': builder.warnings,
            'hata': builder.stats.get('scan_error'), 'ayristirma': builder.stats.get('parse_failures', [])}

def score(flagged, gold):
    hit = sorted(set(flagged) & set(gold))
    return {'yakalanan': hit, 'kacirilan': sorted(set(gold) - set(flagged)), 'fazladan': sorted(set(flagged) - set(gold)),
            'yakalama': f'{len(hit)}/{len(gold)}'}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True)
    parser.add_argument('--tur', type=int, default=2)
    parser.add_argument('--baglam', type=int, default=24576)
    parser.add_argument('--cikti', default='kisisel/denetim-kiyas')
    parser.add_argument('--fa-kapali', action='store_true',
                        help='Flash Attention kapalı (gemma4:12b bu GPU\'da FA çekirdeğinde çöktü)')
    parser.add_argument('--dusunme', choices=['acik', 'kapali'], default='acik',
                        help='kapali: düşünme modu yok, şemadaki "kontrol" alanıyla doğrulama')
    args = parser.parse_args()
    worksheet.SCAN_THINK = args.dusunme == 'acik'
    if args.fa_kapali:
        import os
        os.environ['OLLAMA_FLASH_ATTENTION'] = '0'  # yalnız bu betiğin başlattığı sunucuya geçer
    out = Path(args.cikti)
    out.mkdir(parents=True, exist_ok=True)
    library = SourceLibrary()
    library.add_text(TRANSCRIPT, kind='transkript')
    client = llm.OllamaClient()
    client.ensure_running(print, lambda: False)
    plan = llm.ModelPlan(args.model, args.baglam, True, 'kıyas')
    model = worksheet.LocalModel(client, plan, lambda: False)
    report = {'model': args.model, 'baglam': args.baglam, 'dusunme': args.dusunme, 'grup': worksheet.SCAN_GROUP, 'foylar': {}}
    try:
        for name, (path, gold) in FOYS.items():
            content = json.loads(Path(path).read_text(encoding='utf-8'))
            rounds = []
            for number in range(args.tur):
                result = run_scan(model, library, content)
                result['puan'] = score({f['madde'] for f in result['isaretler']}, gold)
                rounds.append(result)
                print(f'{args.model} föy {name} tur {number + 1}: {result["sn"]} sn, {result["cikti_token"]} token, '
                      f'yakalama {result["puan"]["yakalama"]}, fazladan {result["puan"]["fazladan"]}, '
                      f'red {len(result["red"])}', flush=True)
            sets = [{f['madde'] for f in r['isaretler']} for r in rounds]
            report['foylar'][name] = {'altin': gold, 'turlar': rounds,
                                      'birlesim': score(set().union(*sets), gold),
                                      'kesisim': score(set.intersection(*sets) if sets else set(), gold)}
            print(f'  birleşim {report["foylar"][name]["birlesim"]["yakalama"]}, '
                  f'kesişim {report["foylar"][name]["kesisim"]["yakalama"]}', flush=True)
    finally:
        client.unload(args.model)
        client.stop()
        (out / f'{args.model.replace(":", "_")}-{args.dusunme}.json').write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                                                   encoding='utf-8')

if __name__ == '__main__':
    main()
