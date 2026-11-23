from pathlib import Path
import json
from core import Segment
from lecture_translation import LectureTranslator
from llm import OllamaClient
cases=[
('We put the parameters in a block in memory and pass the address in a register. The parameters can also be pushed onto the stack.', ['yazmaç','yığın']),
('Block and stack methods do not limit the number of parameters.', ['parametre','sınır']),
('The shell executes the fork system call to create a process.', ['fork','kabuk','sistem çağr']),
('System calls include process control, file management, device management and information maintenance.', ['dosya yönet','bilgi bakım']),
('The linker combines object files, and the loader places the executable in memory.', ['bağlayıcı','yükleyici','belle']),
('A system call switches execution from user mode to kernel mode.', ['kullanıcı','çekirdek']),
('FreeBSD supports multiple processes, whereas this Arduino example runs one program.', ['FreeBSD','Arduino']),
('The sine function and its derivative are evaluated at x = 0.', ['sin','türev','0'])]
client=OllamaClient(host='127.0.0.1:11438');translator=None;out=[]
try:
 translator=LectureTranslator(True,lambda _:None,lambda:False,client)
 translator.translate([Segment(i,i+1,text) for i,(text,_) in enumerate(cases)],'tr',lambda row,p:out.append(row))
 results=[]
 for (source,wanted),row in zip(cases,out):
  results.append({'source':source,'output':row.text,'term_checks':{term:term.casefold() in row.text.casefold() for term in wanted}})
 Path('ornekler/29-09-kalite/ceviri-denetimi.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
 print('CASES',len(results),'TERM_CHECKS',sum(sum(r['term_checks'].values()) for r in results),'/',sum(len(r['term_checks']) for r in results),flush=True)
finally:
 if translator:translator.close()
 client.stop()
