import json,time
from pathlib import Path
from core import Segment,render_plain,render
from lecture_translation import LectureTranslator
from llm import OllamaClient
from terminology import normalize,required_turkish
root=Path('ornekler/29-09-kalite');data=json.loads((root/'ayrintili-sonuc.json').read_text(encoding='utf-8'))
rows=data['rows'];client=OllamaClient(host='127.0.0.1:11438');translator=None;audit=[]
try:
 translator=LectureTranslator(True,print,lambda:False,client)
 for i,row in enumerate(rows):
  context=' '.join(s['original'] for s in rows[max(0,i-2):i])
  normalized,edits=normalize(row['original'],context)
  missing=[term for term in required_turkish(normalized,context) if term not in row['text'].casefold()]
  if edits or missing:
   old=row['text'];mapping=translator.batch([{'id':str(i),'text':row['original']}],'tr',context)
   row['text']=mapping[str(i)];row['translated']=row['text'].casefold()!=row['original'].casefold()
   audit.append({'row':i,'start':row['start'],'original_asr':row['original'],'normalizations':edits,'required_terms_missing_before':missing,'old_translation':old,'new_translation':row['text']})
   print('REPAIRED',i,row['text'],flush=True)
finally:
 if translator:translator.close()
 client.stop()
data['normalization_audit']=audit
(root/'ayrintili-sonuc.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
(root/'normalizasyon-kaydi.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
segments=[Segment(**s) for s in rows]
(root/'ders-metni.txt').write_text(render_plain(segments),encoding='utf-8-sig')
(root/'ders-altyazi.srt').write_text(render(segments,True),encoding='utf-8-sig')
(root/'orijinal-transkript.txt').write_text(render_plain([Segment(s.start,s.end,s.original) for s in segments]),encoding='utf-8-sig')
print('FINAL_REPAIRS',len(audit),flush=True)
