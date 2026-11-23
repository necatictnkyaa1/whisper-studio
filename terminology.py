"""Dar kapsamlı, denetlenebilir ders terimi normalizasyonu; ham ASR metni korunur."""
import re

VERSION='context-terms-1'

def normalize(text,context=''):
    original=text;edits=[]
    combined=(context+' '+text).casefold()
    def change(pattern,replacement,rule):
        nonlocal text
        def apply(match):
            value=replacement(match) if callable(replacement) else replacement
            if value!=match.group(0):edits.append({'from':match.group(0),'to':value,'rule':rule})
            return value
        text=re.sub(pattern,apply,text,flags=re.I)
    if 'process control' in combined:
        change(r'\b(a\s+)?process\s+control\s+system\s+call(?:ed)?\s+type\b(?!\s*\()',
               lambda m:('a ' if m.group(1) else '')+'type of process control system call','call-type-grammar')
    if 'shared data' in combined and ('process' in combined or 'synchron' in combined):
        change(r'\b(?:logs|lux)(?=\s+for\s+managing\s+access\s+to\s+shared\s+data)', 'locks','shared-access-lock')
    security=any(term in combined for term in ('cybersecurity','intrusion','network attack','penetration testing'))
    if 'device management' in combined and not security:
        change(r'\b(?:locally|logically)\s*[,;]?\s*(?:attack|attach)\s+or\s+(?:detect|detach)\s+devices\b',
               'logically attach or detach devices','device-attach-detach')
    if 'communication' in combined and not security:
        change(r'\b(?:attack|attach)\s+(?:and|or)\s+(?:detect|detach)\s+remote\s+devices\b',
               'attach and detach remote devices','remote-device-attach-detach')
        if 'shared memory model' in combined:
            change(r'\bpassing\s+(?:passing\s+)?model\b','message-passing model','communication-message-passing')
    # Yalnızca önceki açık süreç tanımı sorusuyla birlikte görülen ses tanıma karışıklığı.
    # HTML hakkında gerçek bir açıklamaya veya belirsiz başka isme uygulanmaz.
    questions=re.findall(r'what\s+is\s+(?:the\s+)?([a-z]+)',combined,re.I)
    if questions and questions[-1]=='process':
        change(r'\bHTML(?=\s+in\s+Turkish\b)','işlem','bilingual-process-term')
    return text,edits

def required_turkish(text,context=''):
    combined=(context+' '+text).casefold();found=[]
    if any(term in combined for term in ('system call','operating system','parameter','memory')):
        if re.search(r'\bregisters?\b',text,re.I):found.append('yazmaç')
        if re.search(r'\bstack(?:s|ing|ed)?\b',text,re.I):found.append('yığın')
    if re.search(r'\bsystem\s+calls?\b',text,re.I):found.append('sistem çağr')
    if 'file management' in text.casefold():found.append('dosya yönet')
    # Kaynakta hem sayı hem uzunluk anılıyorsa, yalnızca birini çevirip diğerini düşürme.
    if (re.search(r'\bparameters?\b',text,re.I) and re.search(r'\bnumber\b',text,re.I)
            and re.search(r'\blength\b',text,re.I)):
        found.extend(('sayı','uzunlu'))
    return found
