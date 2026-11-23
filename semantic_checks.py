"""Açık sıralama ifadelerinde yazıyla söylenen sayılar için dar anlam denetimi."""
import re
_FIRST_TEN='birinci ikinci üçüncü dördüncü beşinci altıncı yedinci sekizinci dokuzuncu onuncu'.split()
RANKS={word:(i+1,turkish) for i,(word,turkish) in enumerate(zip(
 'first second third fourth fifth sixth seventh eighth ninth tenth eleventh twelfth thirteenth fourteenth fifteenth sixteenth seventeenth eighteenth nineteenth twentieth'.split(),
 _FIRST_TEN+['on '+word for word in _FIRST_TEN[:9]]+['yirminci']))}
PATTERN=re.compile(r'\b(?:finish(?:ing|ed)?|ranked|placed|came)\s+(?:(?:in|at)\s+)?(?:the\s+)?('+ '|'.join(RANKS)+r')\b',re.I)

def rank_requirements(source):
 return [{'value':RANKS[m.group(1).lower()][0],'source':m.group(1),
          'turkish':RANKS[m.group(1).lower()][1]} for m in PATTERN.finditer(source)]

def time_requirements(source):
 """Açık used-to-be / now karşıtlığı; genel zaman çözümleyicisi değildir."""
 if re.search(r'\bnow\b',source,re.I) and re.search(r'\bused\s+to\s+be\s+[A-Za-z]',source,re.I):
  return {'past_source':'used to be','present_source':'now','turkish_past_hint':'daha önce / eskiden'}
 return {}

def missing_past_marker(source,target):
 if not time_requirements(source):return False
 text=target.replace('İ','i').replace('I','ı').casefold().replace('\u0307','')
 # Çeviri sözleşmesi bu açık karşıtlıkta geçmişi açık bir zaman belirteciyle ifade eder.
 return not re.search(r'\b(?:eskiden|önce|önceden|önceleri|geçmişte)\b',text)

def state_transition(source):
 """Yalnızca basit ve açık online/offline geçmiş→şimdi ilişkisi."""
 if not time_requirements(source):return {}
 past=re.search(r'\bused\s+to\s+be\s+(online|offline)\b',source,re.I)
 if not past:return {}
 remaining=re.findall(r'\b(?:online|offline)\b',source[past.end():],re.I)
 if len(remaining)!=1:return {}
 words={'online':'çevrimiçi','offline':'çevrimdışı'}
 return {'past':words[past.group(1).lower()],'present':words[remaining[0].lower()]}

def missing_state_transition(source,target):
 expected=state_transition(source)
 if not expected:return False
 text=target.replace('İ','i').replace('I','ı').casefold().replace('\u0307','')
 markers=list(re.finditer(r'\b(?:şimdi|şimdiyse|artık|şu\s+anda|günümüzde)\b',text))
 if not markers:return True
 marker=markers[-1]
 for part,state in ((text[:marker.start()],expected['past']),(text[marker.end():],expected['present'])):
  pattern=r'\bçevrim\s*'+('içi' if state=='çevrimiçi' else 'dışı')
  match=re.search(pattern,part)
  if not match:return True
  tail=' '.join(part[match.end():].split()[:3])
  if re.search(r'\b(?:değil\w*|olmad\w*|olmay\w*|olmaz\w*|yok\w*)',tail):return True
 return False

def missing_ranks(source,target):
 text=target.replace('İ','i').replace('I','ı').casefold().replace('\u0307','');missing=[]
 for requirement in rank_requirements(source):
  value=requirement['value'];word=requirement['turkish']
  # 11–19 Türkçede bitişik veya ayrı yazılabilir; çekim ekleri kabul edilir.
  pattern=re.escape(word).replace(r'\ ',r'\s*')
  written=re.search(r'\b'+pattern,text) or (value==1 and re.search(r'\bilk\b',text))
  numeric=re.search(rf'(?<!\d){value}(?:\s*\.|[’\x27]?\s*(?:inci|ıncı|uncu|üncü)|\s+sıra)',text)
  if not written and not numeric:missing.append(requirement)
 return missing
