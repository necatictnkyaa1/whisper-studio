import json,time
from pathlib import Path
from core import Segment,render,render_plain
from language_checks import translate_sentences,text_language_hint,repetitive
from translation import LocalTranslator
root=Path('ornekler/kalite-20261016')
data=json.loads((root/'ayrintili-sonuc.json').read_text(encoding='utf-8'))
translator=LocalTranslator('en','tr',True,lambda _:None,lambda:False)
started=time.monotonic()
for row in data['rows']:
    original=row['original'];source=text_language_hint(original) or row['source_language']
    row['text'],row['translated']=translate_sentences(original,source,'tr',lambda _:translator)
    row['review']=text_language_hint(row['text'])=='en'
data['translation_recheck_seconds']=round(time.monotonic()-started,2)
(root/'ayrintili-sonuc.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
segments=[Segment(**s) for s in data['rows']]
(root/'ders-metni.txt').write_text(render_plain(segments),encoding='utf-8-sig')
(root/'ders-altyazi.srt').write_text(render(segments,True),encoding='utf-8-sig')
print('DONE',len(segments),'English hints',sum(text_language_hint(s.text)=='en' for s in segments),'markers',sum('ZXQ' in s.text for s in segments),'seconds',data['translation_recheck_seconds'],flush=True)
