import json
from pathlib import Path
from llm import OllamaClient,ModelPlan
client=OllamaClient(host='127.0.0.1:11438')
try:
 client.ensure_running(print,lambda:False)
 print('INSTALLED',client.installed(),flush=True)
 source=[{'id':'1','text':'We put the parameters in a block or table in memory and pass the address in a register. The parameters can also be pushed onto the stack and popped by the operating system.'},
 {'id':'2','text':'System calls can be grouped into process control, file management, device management, information maintenance, communications, and protection.'},
 {'id':'3','text':'The shell executes the fork system call to create a process. FreeBSD supports multiple processes.'}]
 schema={'type':'object','properties':{'translations':{'type':'array','items':{'type':'object','properties':{'id':{'type':'string'},'text':{'type':'string'}},'required':['id','text'],'additionalProperties':False}}},'required':['translations'],'additionalProperties':False}
 messages=[{'role':'system','content':'You are a faithful technical lecture translator. Translate each input into natural Turkish. Preserve ids, numbers, code identifiers, negation and modality. In operating systems: stack = yığın, register = yazmaç, system call = sistem çağrısı, fork stays fork, file management = dosya yönetimi. Do not summarize, add facts, explain or correct the lecturer. Return JSON matching the schema.'},{'role':'user','content':json.dumps(source,ensure_ascii=False)}]
 text,stats=client.chat(ModelPlan('qwen3.5:9b',4096,True,'local translation'),messages,lambda:False,schema=schema,temperature=0,max_tokens=2048)
 Path('../../work/audit29/qwen-probe.json').write_text(json.dumps({'output':text,'stats':stats},ensure_ascii=False,indent=2),encoding='utf-8')
 print(text,flush=True)
finally:
 if client.alive():client.unload('qwen3.5:9b')
 client.stop()
