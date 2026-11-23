"""Bağlam paylı kısa ses pencereleri: zamanları korur, filtreyle konuşma atmaz."""
from dataclasses import replace
from types import SimpleNamespace

RATE=16000
DOMAINS=[
    (('operating system','system call','parameter','register','stack','kernel','solaris'),
     'parameter passing, register, stack, push, pop, block, system call, process control, file management, device management, information maintenance, communication, protection, user mode, kernel mode, fork, exec, FreeBSD, Arduino, linker, loader, object file, executable, bugs, locks, synchronization, debugging, attach, detach, single step execution'),
    (('gradient','derivative','polynomial','taylor','hessian','sine'),
     'gradient descent, partial derivative, polynomial approximation, Taylor series, sine, cosine, Hessian, loss function, mean squared error')]


def constrain_lecture_languages(engine):
    """Bu EN/TR ürününde, gürültünün üçüncü bir dil uydurmasını engelle."""
    engine._lecture_languages=True
    original=engine.detect_language
    def detect(*args,**kwargs):
        language,confidence,probabilities=original(*args,**kwargs)
        if language not in ('en','tr'):
            allowed=[(name,p) for name,p in probabilities if name in ('en','tr')]
            if allowed:language,confidence=max(allowed,key=lambda pair:pair[1])
        return language,confidence,probabilities
    engine.detect_language=detect


def pause_boundaries(audio,cancelled,max_seconds=26,min_seconds=16):
    """Düşük enerjili aralarda kes; konuşma/sessizlik dahil hiçbir örneği atma.

    Enerji eşiği konuşma sınıflandırıcısı değildir. Aralık bulunamazsa üst
    sınırda kesilir; iki saniyelik bağlamla model girdisi 30 saniyeyi aşmaz.
    """
    import numpy as np
    if max_seconds<=min_seconds or min_seconds<=0:raise ValueError('Geçersiz pencere aralığı')
    size=len(audio);frame=320;start=0
    while start<size and not cancelled():
        limit=min(size,start+round(max_seconds*RATE))
        end=limit
        if limit<size:
            region=audio[start:limit]
            frames=len(region)//frame
            energy=np.sqrt(np.mean(np.square(region[:frames*frame].reshape(frames,frame),dtype=np.float64),axis=1))
            threshold=min(.003,max(.00005,float(np.median(energy))*.15))
            quiet=energy<threshold
            # 200 ms kesintisiz düşük enerji. Kısa ünsüz boşluklarını tercih etme.
            eligible=np.convolve(quiet.astype(int),np.ones(10,dtype=int),'valid')==10
            candidates=np.flatnonzero(eligible)+5
            candidates=candidates[candidates*frame>=min_seconds*RATE]
            if len(candidates):end=start+int(candidates[-1])*frame
        yield start/RATE,end/RATE
        start=end


def _plans(engine,audio,language,window_seconds,pad_seconds,cancelled,strategy='fixed'):
    constrained=getattr(engine,"_lecture_languages",False) is True
    if constrained and language is None:window_seconds=12
    duration=len(audio)/RATE
    if strategy not in ('fixed','pause','pause-short'):raise ValueError('Bilinmeyen pencere stratejisi')
    boundaries=(pause_boundaries(audio,cancelled,12,8) if strategy=='pause-short' else
                pause_boundaries(audio,cancelled) if strategy=='pause' else
                ((start,min(duration,start+window_seconds)) for start in range(0,int(duration)+1,window_seconds)))
    for start,end in boundaries:
        if start>=duration or cancelled():return
        selected=language
        if constrained and selected is None:
            if end-start>=8:
                middle=(start+end)/2
                first,confidence1,_=engine.detect_language(audio=audio[round(start*RATE):round(middle*RATE)],vad_filter=False)
                second,confidence2,_=engine.detect_language(audio=audio[round(middle*RATE):round(end*RATE)],vad_filter=False)
                if first!=second and min(confidence1,confidence2)>=.35:
                    yield start,middle,first
                    yield middle,end,second
                    continue
                if first==second:selected=first
            if selected is None:
                selected,_,_=engine.detect_language(audio=audio[max(0,round((start-pad_seconds)*RATE)):min(len(audio),round((end+pad_seconds)*RATE))],vad_filter=False)
        yield start,end,selected


def _windows(engine,audio,cancelled,language=None,window_seconds=24,pad_seconds=2,strategy='fixed'):
    import numpy as np
    duration=len(audio)/RATE
    heard=set()
    # Dijital sessizlikte dil algılayıcıyı da çalıştırma.
    if len(audio)==0 or np.max(np.abs(audio))<1e-5:return
    for core_start,core_end,selected in _plans(engine,audio,language,window_seconds,pad_seconds,cancelled,strategy):
        if cancelled():return
        left=max(0,core_start-pad_seconds);right=min(duration,core_end+pad_seconds)
        sample=audio[round(left*RATE):round(right*RATE)]
        if len(sample)==0 or np.max(np.abs(sample))<1e-5:continue
        hotwords=next((terms for anchors,terms in DOMAINS if len(heard.intersection(anchors))>=3),None)
        rows,_=engine.transcribe(sample,language=selected,hotwords=hotwords,
            multilingual=selected is None,beam_size=5,vad_filter=False,
            condition_on_previous_text=False,temperature=0.0,word_timestamps=True,
            hallucination_silence_threshold=2.0,repetition_penalty=1.05,no_repeat_ngram_size=6)
        for row in rows:
            if cancelled():return
            body=row.text.casefold()
            for anchors,_ in DOMAINS:
                heard.update(anchor for anchor in anchors if anchor in body)
            words=getattr(row,'words',None)
            if words:
                kept=[word for word in words if core_start <= left+(word.start+word.end)/2 < core_end]
                if not kept:continue
                values=dict(start=max(core_start,left+kept[0].start),end=min(core_end,left+kept[-1].end),
                            text=''.join(word.word for word in kept).strip())
            else:
                if not core_start<=left+(row.start+row.end)/2<core_end:continue
                values=dict(start=left+row.start,end=left+row.end,text=row.text)
            try:yield replace(row,**values)
            except TypeError:yield SimpleNamespace(**{**vars(row),**values})


def speech_windows(engine,audio,cancelled,language=None,strategy='fixed'):
    """Pencere sınırında yarım kalan cümleyi çeviriden önce birleştir."""
    from language_checks import text_language_hint
    pending=None
    for row in _windows(engine,audio,cancelled,language,strategy=strategy):
        if pending is not None:
            first,second=text_language_hint(pending.text),text_language_hint(row.text)
            join=(not pending.text.rstrip().endswith(('.', '?', '!', ':', ';'))
                  and row.start-pending.end<=2.0 and row.end-pending.start<=35
                  and not (first and second and first!=second))
            if join:
                values=dict(end=row.end,text=pending.text.rstrip()+' '+row.text.lstrip(),
                    avg_logprob=min(getattr(pending,'avg_logprob',0),getattr(row,'avg_logprob',0)),
                    compression_ratio=max(getattr(pending,'compression_ratio',0),getattr(row,'compression_ratio',0)))
                try:pending=replace(pending,**values)
                except TypeError:pending=SimpleNamespace(**{**vars(pending),**values})
                continue
            yield pending
        pending=row
    if pending is not None and not cancelled():yield pending
