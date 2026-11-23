"""EN/TR cümle ipuçları; geniş ses penceresindeki dil uyuşmazlığını yakalar."""
import re
EN = set('the what which where when why who how is are was were do does did this that these those we you they it in on of to and with for have has had will would should can previous last told'.split())
TR = set('bir bu şu o ve veya ile için ama fakat hangi ne nasıl neden nerede zaman biz siz onlar ben sen mı mi mu mü değil olan olarak burada önce geçen'.split())
def text_language_hint(text):
    words = re.findall(r'[^\W\d_]+', text.casefold(), re.UNICODE)
    if len(words) < 4:
        return None
    tokens = set(words)
    en, tr = len(tokens & EN), len(tokens & TR)
    if en >= 3 and en >= tr + 2:
        return 'en'
    if tr >= 2 and tr >= en + 1:
        return 'tr'
    if any(c in text.casefold() for c in 'ğış') and tr:
        return 'tr'
    return None
