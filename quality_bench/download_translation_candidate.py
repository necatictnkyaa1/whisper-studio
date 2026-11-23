"""Çeviri adayını ayrı yerel motorla indirir; ders verisi göndermez."""
from llm import OllamaClient
import time
client=OllamaClient(host='127.0.0.1:11439');last=0
def status(message):
 global last
 if time.monotonic()-last>10:print(message,flush=True);last=time.monotonic()
try:
 client.ensure_running(status,lambda:False)
 if 'translategemma:12b' not in client.installed():client.pull('translategemma:12b',status,lambda:False)
 print('READY translategemma:12b',flush=True)
finally:client.stop()
