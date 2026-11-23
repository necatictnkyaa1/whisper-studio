"""İnceleme çıktısını ayrı ders olarak saklar; mevcut dersleri değiştirmez."""
import json
from pathlib import Path
from sessions import SessionStore

root=Path('ornekler/29-09-kalite').resolve()
data=json.loads((root/'ayrintili-sonuc.json').read_text(encoding='utf-8'))
assert len(data['rows'])==260
data['timing_note']='seconds: ham ASR önbelleğinden devam eden çeviri koşusu; uçtan uca süre değildir.'
data['quality_status']='İnceleme sürümü; anlamsal doğruluk tamamen doğrulanmadı.'
(root/'ayrintili-sonuc.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
store=SessionStore()
identity=store.save('quality29-large-v3-20261017','29-09-2026 · kalite incelemesi',{
 'version':1,'path':r'C:\Users\Necati\Downloads\29-09-2026.mp3',
 'segments':data['rows'],'sources':[],'speech_files':[],
 'exports':[str(root/name) for name in ('ders-metni.txt','orijinal-transkript.txt','ders-altyazi.srt')],
 'notes':'Large-v3 + Qwen3.5:9b inceleme sürümü. Bazı duyum ve anlatım hataları sürüyor; doğrulanmış ders föyü kaynağı sayılmamalı. Ham metin ve bağlam düzeltme kaydı ayrıca korunuyor.',
 'focus':'','sheet':None,'target':1,'tab':0})
assert len(store.load(identity)[1]['segments'])==260
print(identity)
