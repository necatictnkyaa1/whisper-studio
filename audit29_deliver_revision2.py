import json
from pathlib import Path
from sessions import SessionStore
from lecture_translation import validate,validate_alignment,ModelError
root=Path('ornekler/29-09-kalite/ikinci-inceleme').resolve()
data=json.loads((root/'ayrintili-sonuc.json').read_text(encoding='utf-8'));rows=data['rows']
before=json.loads((root/'kismi-sonuc.json').read_text(encoding='utf-8'));audit=[];previous=[]
assert len(rows)==260
for i,row in enumerate(rows):
 validate([{'id':str(i),'text':row['original']}],{'translations':{str(i):row['text']}},'tr')
 validate_alignment(row['original'],row['text'],previous)
 previous=(previous+[(row['original'],row['text'])])[-2:]
 if row['text']!=before[i]['text']:
  audit.append({'row':i,'old':before[i]['text'],'new':row['text'],'reason':'Bağımsız cümleyle yeniden çeviri; dolgu sözü ve kaynak kavramı koruma denetimi.'})
data['pipeline']='topic-context-v4-full-run + v6-individual-validation-repairs'
data['validation_repairs']=audit
(root/'ayrintili-sonuc.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
(root/'ceviri-duzeltmeleri.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
store=SessionStore();identity='quality29-revision2-20261017'
if store.load(identity):raise RuntimeError('İkinci inceleme dersi zaten var; kullanıcı düzenlemelerinin üzerine yazılmadı.')
store.save(identity,'29-09-2026 · ikinci kalite incelemesi',{
 'version':1,'path':r'C:\Users\Necati\Downloads\29-09-2026.mp3','segments':rows,
 'sources':[],'speech_files':[],
 'exports':[str(root/name) for name in ('ders-metni.txt','orijinal-transkript.txt','ders-altyazi.srt')],
 'notes':'İkinci inceleme: bağlamdan cümle kopyalama, Windows adı kaybı ve okay/tamamı hataları düzeltildi. İletişim bölümü daha uzun iki ses penceresiyle yeniden çözüldü. Açılıştaki isimler ve bazı ASR ifadeleri hâlâ hatalı olabilir. Bu metin tam doğrulanmış ders kaynağı değildir.',
 'focus':'','sheet':None,'target':1,'tab':0})
assert len(store.load(identity)[1]['segments'])==260
print('SAVED',identity,'VALIDATED',len(rows),'REPAIRS',len(audit))
