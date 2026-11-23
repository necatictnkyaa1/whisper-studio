"""İkinci inceleme oturumunu yalnızca kullanıcı düzenlememişse günceller."""
import json
from pathlib import Path
from sessions import SessionStore
from lecture_translation import validate,validate_alignment
base=Path('ornekler/29-09-kalite').resolve();root=base/'son-motor-denemesi'
data=json.loads((root/'ayrintili-sonuc.json').read_text(encoding='utf-8'));rows=data['rows'];previous=[]
assert len(rows)==260 and data['pipeline']=='topic-context-small-batches-coverage-v6'
for i,s in enumerate(rows):
 validate([{'id':str(i),'text':s['original']}],{'translations':{str(i):s['text']}},'tr')
 validate_alignment(s['original'],s['text'],previous)
 previous=(previous+[(s['original'],s['text'])])[-2:]
store=SessionStore();identity='quality29-revision2-20261017';existing=store.load(identity)
original_note='İkinci inceleme: bağlamdan cümle kopyalama, Windows adı kaybı ve okay/tamamı hataları düzeltildi. İletişim bölümü daha uzun iki ses penceresiyle yeniden çözüldü. Açılıştaki isimler ve bazı ASR ifadeleri hâlâ hatalı olabilir. Bu metin tam doğrulanmış ders kaynağı değildir.'
old=json.loads((base/'ikinci-inceleme/ayrintili-sonuc.json').read_text(encoding='utf-8'))['rows']
untouched=(existing and existing[0]=='29-09-2026 · ikinci kalite incelemesi' and existing[1].get('segments')==old
 and existing[1].get('notes')==original_note and existing[1].get('sources')==[]
 and existing[1].get('sheet') is None and existing[1].get('focus')=='')
payload=dict(existing[1]) if untouched else {'version':1,'sources':[],'speech_files':[],'focus':'','sheet':None,'target':1,'tab':0}
payload.update(path=r'C:\Users\Necati\Downloads\29-09-2026.mp3',segments=rows,
 exports=[str(root/name) for name in ('ders-metni.txt','orijinal-transkript.txt','ders-altyazi.srt')],notes=original_note+' Son motor ayarlarıyla 260 bölüm baştan çevrildi; 213 yazılım testi geçti. Ayrıntılar KALITE-29-09-RAPORU.md dosyasında.')
if not untouched:identity=None
identity=store.save(identity,'29-09-2026 · güncel çeviri',payload)
assert store.load(identity)[1]['segments']==rows
print('SAVED',identity,'REUSED_UNEDITED_REVIEW',bool(untouched))
