"""Açık normalizasyon ve sayılabilir sözcük/karakter düzenleme hataları."""
import unicodedata,re

def normalize(text,language):
 text=unicodedata.normalize('NFKC',text)
 if language=='tr':text=text.replace('İ','i').replace('I','ı')
 text=text.casefold().replace('\u0307','')
 text=text.replace("'",'').replace('’','').replace('ʼ','')
 text=''.join(c if c in ('-','+','−') and i+1<len(text) and text[i+1].isdigit()
              else ' ' if unicodedata.category(c)[0] in ('P','S') else c for i,c in enumerate(text))
 return re.sub(r'\s+',' ',text).strip()

def turkish_integer(number):
 if number==0:return 'sıfır'
 units=('','bir','iki','üç','dört','beş','altı','yedi','sekiz','dokuz')
 tens=('','on','yirmi','otuz','kırk','elli','altmış','yetmiş','seksen','doksan')
 if not 0<number<10000:return str(number)
 parts=[]
 if number>=1000:
  n,number=divmod(number,1000);parts.append((units[n]+' ' if n>1 else '')+'bin')
 if number>=100:
  n,number=divmod(number,100);parts.append((units[n]+' ' if n>1 else '')+'yüz')
 if number>=10:n,number=divmod(number,10);parts.append(tens[n])
 if number:parts.append(units[number])
 return ' '.join(parts)

def spoken_number_score(reference,hypothesis,language):
 """Ek gösterge: yalnızca TR'deki bağımsız 0–9999 tamsayıları sözle açılır.

 Ana WER'i değiştirmez. Ondalıklar, ek almış sayılar ve karma dil için genellenmez.
 """
 if language!='tr':return score(reference,hypothesis,language)
 def expand(text):
  # Ondalık/tarih parçasını yanlışlıkla tam sayıya çevirmemek için ham metinde uygula.
  return re.sub(r'(?<![\w.,+−-])\d{1,4}(?![\w.,])',lambda m:turkish_integer(int(m.group())),text)
 return score(expand(reference),expand(hypothesis),language)

def distance(reference,hypothesis):
 previous=list(range(len(hypothesis)+1))
 for i,ref in enumerate(reference,1):
  current=[i]
  for j,hyp in enumerate(hypothesis,1):current.append(min(previous[j]+1,current[-1]+1,previous[j-1]+(ref!=hyp)))
  previous=current
 return previous[-1]

def word_errors(reference,hypothesis):
 matrix=[list(range(len(hypothesis)+1))]
 for i,ref in enumerate(reference,1):
  current=[i]
  for j,hyp in enumerate(hypothesis,1):current.append(min(matrix[-1][j]+1,current[-1]+1,matrix[-1][j-1]+(ref!=hyp)))
  matrix.append(current)
 i,j=len(reference),len(hypothesis);operations=[];counts={'substitutions':0,'deletions':0,'insertions':0}
 while i or j:
  if i and j and reference[i-1]==hypothesis[j-1] and matrix[i][j]==matrix[i-1][j-1]:i-=1;j-=1
  elif i and j and matrix[i][j]==matrix[i-1][j-1]+1:
   operations.append({'type':'substitution','reference':reference[i-1],'hypothesis':hypothesis[j-1]});counts['substitutions']+=1;i-=1;j-=1
  elif i and matrix[i][j]==matrix[i-1][j]+1:
   operations.append({'type':'deletion','reference':reference[i-1]});counts['deletions']+=1;i-=1
  else:
   operations.append({'type':'insertion','hypothesis':hypothesis[j-1]});counts['insertions']+=1;j-=1
 return {**counts,'errors':sum(counts.values()),'reference_words':len(reference),'operations':list(reversed(operations))}

def score(reference,hypothesis,language):
 ref=normalize(reference,language);hyp=normalize(hypothesis,language)
 words=word_errors(ref.split(),hyp.split())
 chars_ref=ref.replace(' ','');chars_hyp=hyp.replace(' ','')
 return {**words,'normalized_reference':ref,'normalized_hypothesis':hyp,
  'wer':words['errors']/len(ref.split()) if ref else (0 if not hyp else None),
  'char_errors':distance(chars_ref,chars_hyp),'reference_chars':len(chars_ref),
  'cer':distance(chars_ref,chars_hyp)/len(chars_ref) if chars_ref else (0 if not chars_hyp else None)}

def aggregate(rows):
 keys=('errors','reference_words','substitutions','deletions','insertions','char_errors','reference_chars')
 result={key:sum(row['score'][key] for row in rows) for key in keys}
 return {**result,'clips':len(rows),'wer':result['errors']/max(1,result['reference_words']),
  'cer':result['char_errors']/max(1,result['reference_chars']),
  'seconds':sum(row['seconds'] for row in rows),'audio_seconds':sum(row['duration'] for row in rows)}
