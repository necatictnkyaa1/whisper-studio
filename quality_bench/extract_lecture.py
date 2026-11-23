"""Özel ders kayıtları açık benchmark verisinden ayrı work klasöründe kalır."""
import json
from pathlib import Path
import core,av
from faster_whisper.audio import decode_audio
from quality_bench.prepare import write_audio
ROOT=Path(__file__).resolve().parent;folder=(ROOT.parent/'../../work/quality-lecture-clips').resolve();folder.mkdir(exist_ok=True)
source=Path(r'C:\Users\Necati\Downloads\29-09-2026.mp3')
with av.open(str(source)) as container:format_name=container.format.name
audio=decode_audio(str(source));rows=[]
for name,start,end in [('opening',0,24),('parameters',170,194),('process',272,296),('communication',432,454),('call-names',508,534)]:
 path=folder/(name+'.wav');write_audio(path,audio[start*16000:end*16000]);rows.append({'clip':name,'start':start,'end':end,'file':str(path)})
(folder/'clips.json').write_text(json.dumps({'source_container':format_name,'rows':rows},indent=2),encoding='utf-8')
print('PRIVATE_CLIPS',len(rows),'CONTAINER',format_name,flush=True)
