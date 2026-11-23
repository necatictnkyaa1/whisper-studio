"""Pencere adayını aynı örneklerde temel sonuçla karşılaştır; otomatik terfi yok."""
import json,argparse
from pathlib import Path
from quality_bench.metrics import aggregate, spoken_number_score

ROOT=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--candidate',choices=('pause','pause-short'),default='pause');args=parser.parse_args()
    baseline=json.loads((ROOT/'results/whisper-production.json').read_text(encoding='utf-8'))
    candidate=json.loads((ROOT/f'results/whisper-{args.candidate}.json').read_text(encoding='utf-8'))
    if baseline['manifest_sha256']!=candidate['manifest_sha256']:
        raise ValueError('Kayıt listeleri farklı; karşılaştırma geçersiz')
    if baseline['compute_type']!=candidate['compute_type']:
        raise ValueError('Hesaplama hassasiyeti aynı olmalı')
    original={row['id']:row for row in baseline['rows']}
    proposed={row['id']:row for row in candidate['rows']}
    if original.keys()!=proposed.keys():raise ValueError('Aday koşu tamamlanmamış')
    differences=[]
    for identity,old in original.items():
        new=proposed[identity]
        for field in ('reference','group','derived','duration'):
            if old[field]!=new[field]:raise ValueError('Örnek içeriği farklı: '+identity)
        differences.append({'id':identity,'group':old['group'],'derived':old['derived'],
            'reference':old['reference'],'baseline':old['text'],'candidate':new['text'],
            'error_delta':new['score']['errors']-old['score']['errors'],
            'baseline_errors':old['score']['operations'],'candidate_errors':new['score']['operations']})
    groups={}
    for group in ['source-20','derived-4']+sorted({r['group'] for r in original.values()}):
        select=lambda rows:[r for r in rows if (not r['derived'] if group=='source-20' else r['derived'] if group=='derived-4' else r['group']==group)]
        groups[group]={}
        for name,rows in [('baseline',original.values()),('candidate',proposed.values())]:
            selected=select(rows)
            numbers=[{**row,'score':spoken_number_score(row['reference'],row['text'],row['language'])} for row in selected]
            groups[group][name]={**aggregate(selected),'number_format_wer':aggregate(numbers)['wer']}
    output={'candidate_is_default':False,'groups':groups,'differences':differences,
            'limits':'Geliştirme seti; doğal ders konuşması veya uzun kayıt doğrulaması değil. Süreler standart hız kıyası değil.'}
    (ROOT/f'results/window-comparison-{args.candidate}.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    description=('8–12' if args.candidate=='pause-short' else '16–26')
    lines=['# Konuşma aralarında pencereleme deneyi — 18 Ekim 2026','',
           f'Temel: 12 saniyelik çekirdek. Aday: {description} saniye içinde en son en az 200 ms düşük enerjili aralık; yoksa üst sınırda kesim. İki saniye bağlam payı; hiçbir ses örneği filtrelenmez. Dil geçişinde bölme korunur. Aday üretim varsayılanı değildir.','',
           '| Grup | Temel hata/sözcük | Aday hata/sözcük | Temel WER | Aday WER |','|---|---:|---:|---:|---:|']
    for group,values in groups.items():
        a,b=values['baseline'],values['candidate']
        lines.append(f"| {group} | {a['errors']}/{a['reference_words']} | {b['errors']}/{b['reference_words']} | {a['wer']:.2%} | {b['wer']:.2%} |")
    lines+=['','## Değişen örnekler','']
    for row in differences:
        if row['baseline']==row['candidate']:continue
        lines += [f"### {row['id']} — hata farkı {row['error_delta']:+}",
                  f"- Referans: {row['reference']}",f"- Temel: {row['baseline']}",f"- Aday: {row['candidate']}",'']
    lines+=['Bu set ayar geliştirmede kullanıldı; bağımsız doğrulama değildir. WER anlam doğruluğu yüzdesi değildir. Yapay stres örnekleri ana 20 kayda dahil edilmez. Ayrıntı results/window-comparison-*.json.']
    (ROOT/f'PENCERE-KIYASI-{args.candidate}.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps(groups['source-20'],ensure_ascii=False,indent=2))


if __name__=='__main__':main()
