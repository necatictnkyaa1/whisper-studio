"""EN/TR cümle ipuçları; geniş ses penceresindeki dil uyuşmazlığını yakalar."""
import re
EN = set('the what which where when why who how is are was were do does did this that these those we you they it in on of to and with for have has had will would should can previous last told'.split())
TR = set('bir bu şu o ve veya ile için ama fakat hangi ne nasıl neden nerede zaman biz siz onlar ben sen mı mi mu mü değil olan olarak burada önce geçen'.split())
def text_language_hint(text):
    words = re.findall(r'[^\W\d_]+', text.casefold(), re.UNICODE)
    if len(words) < 2:
        return None
    tokens = set(words)
    en, tr = len(tokens & EN), len(tokens & TR)
    if en >= 2 and en >= tr + 2:
        return 'en'
    if tr >= 2 and tr >= en + 1:
        return 'tr'
    if any(c in text.casefold() for c in 'ğış') and tr:
        return 'tr'
    return None


def repetitive(text):
    from collections import Counter
    words=re.findall(r'[^\W\d_]+',text.casefold())
    return len(words)>=8 and max(Counter(words).values(),default=0)>=max(4,len(words)*.45)


def translate_sentences(text,source,target,get_translator):
    """Ses penceresi etiketi, açıkça başka dildeki cümleyi bastıramaz."""
    sentences=[p.strip() for p in re.split(r'(?<=[.!?])\s+',text.strip()) if p.strip()]
    output=[]
    changed=False
    for sentence in sentences:
        actual=text_language_hint(sentence) or source
        if actual==target or (actual,target) not in {('en','tr'),('tr','en')}:
            output.append(sentence);continue
        translator=get_translator(actual)
        candidate=translator.translate(sentence)
        if repetitive(candidate) or (text_language_hint(candidate)==actual and len(sentence.split())>=3):
            retry=translator.translate(sentence,careful=True)
            if retry.strip() and not repetitive(retry):candidate=retry
        # Model, uzun cümlenin yalnızca bir kısmını çevirmiş olabilir.
        # Kalan açık kaynak-dil cümleciklerini bir kez daha çöz; Türkçeyi yeniden çevirme.
        if text_language_hint(candidate)==actual:
            parts=re.split(r'(?<=[.!?;,])\s+',candidate)
            for i,part in enumerate(parts):
                if text_language_hint(part)==actual:
                    retried=translator.translate(part,careful=True)
                    if retried.strip() and not repetitive(retried) and text_language_hint(retried)!=actual:
                        parts[i]=retried.strip()
            candidate=' '.join(parts)
        if repetitive(candidate):candidate=sentence
        output.append(candidate.strip() or sentence)
        changed |= candidate.strip().casefold()!=sentence.casefold()
    # Tüm paragraf Türkçe ağırlıklı olsa bile virgül arkasındaki İngilizce
    # cümlecik kendi diline göre değerlendirilir.
    combined=' '.join(output)
    opposite='en' if target=='tr' else 'tr'
    clauses=re.split(r'(?<=[.!?;,])\s+',combined)
    for i,clause in enumerate(clauses):
        if text_language_hint(clause)==opposite:
            revised=get_translator(opposite).translate(clause,careful=True)
            if revised.strip() and not repetitive(revised) and text_language_hint(revised)!=opposite:
                clauses[i]=revised.strip()
    combined=' '.join(clauses)
    return combined,combined.casefold()!=text.casefold()
