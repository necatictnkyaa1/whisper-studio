"""Yerel transkripsiyon ve kayıpsız dışa aktarma."""
import os
import sys
import re
from pathlib import Path
from dataclasses import dataclass

ROOT = Path(__file__).resolve().parent
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
_dlls = []
if sys.platform == 'win32':
    for folder in (Path(sys.prefix) / 'Lib/site-packages/nvidia').glob('*/bin'):
        os.environ['PATH'] = str(folder) + os.pathsep + os.environ.get('PATH', '')
        _dlls.append(os.add_dll_directory(str(folder)))

MODELS = {'Hızlı · small': 'small', 'Dengeli · large-v3-turbo': 'turbo',
          'Kaliteli · large-v3': 'large-v3', 'Deneme · tiny': 'tiny'}

@dataclass
class Segment:
    start: float
    end: float
    text: str
    original: str = ''
    source_language: str = ''
    translated: bool = False
    review: bool = False

def stamp(seconds, srt=False):
    ms = max(0, round(seconds * 1000))
    h, rest = divmod(ms, 3600000)
    m, rest = divmod(rest, 60000)
    s, ms = divmod(rest, 1000)
    return f'{h:02}:{m:02}:{s:02}{"," if srt else "."}{ms:03}'

def render(segments, srt=False):
    if srt:
        return '\n\n'.join(f'{i}\n{stamp(s.start, True)} --> {stamp(s.end, True)}\n{s.text.strip()}'
                           for i, s in enumerate(segments, 1)) + '\n'
    return '\n'.join(f'[{stamp(s.start)} – {stamp(s.end)}] {s.text.strip()}' for s in segments)

def render_plain(segments):
    """Zaman damgasız; sözcükleri değiştirmeden okunabilir paragraflar."""
    paragraphs, current = [], []
    previous_end, length = None, 0
    for segment in segments:
        text = re.sub(r'\s+', ' ', segment.text).strip()
        if not text:
            continue
        gap = segment.start - previous_end if previous_end is not None else 0
        if current and ((gap >= 8 and length >= 140) or length + len(text) > 700):
            paragraphs.append(' '.join(current))
            current, length = [], 0
        current.append(text)
        length += len(text) + 1
        previous_end = segment.end
    if current:
        paragraphs.append(' '.join(current))
    return '\n\n'.join(paragraphs) + ('\n' if paragraphs else '')

def refine_segment(engine, audio, segment, source, on_status, cancelled):
    """Zayıf çıktıyı otomatik yeniden çöz; yalnızca daha güçlü adayı kullan."""
    from language_checks import repetitive
    weak = repetitive(segment.text) or getattr(segment, 'avg_logprob', 0) < -1.0 or getattr(segment, 'compression_ratio', 0) > 2.4
    original = segment.text.strip()
    if not weak or audio is None or cancelled():
        return original, weak
    start = max(0, int(segment.start * 16000))
    end = min(len(audio), int(segment.end * 16000))
    if end - start < 8000:
        return original, weak
    on_status(f'Bu bölüm daha ayrıntılı çözümleniyor · {stamp(segment.start)}')
    candidates, _ = engine.transcribe(audio[start:end], language=source if source in ('en', 'tr') else None,
        multilingual=source not in ('en', 'tr'), beam_size=8, temperature=0.0,
        condition_on_previous_text=False, vad_filter=False, word_timestamps=True,
        hallucination_silence_threshold=2.0)
    rows = []
    for row in candidates:
        if cancelled():
            return original, weak
        rows.append(row)
    text = ' '.join(row.text.strip() for row in rows if row.text.strip())
    if not text or not rows or any(getattr(row, 'compression_ratio', 0) > 2.4 for row in rows):
        return original, weak
    score = sum(getattr(row, 'avg_logprob', -10) for row in rows) / len(rows)
    if (repetitive(original) and not repetitive(text)) or score > getattr(segment, 'avg_logprob', -1):
        return text, score < -1.0
    return original, weak

def transcribe(path, model, language, device, offline, on_segment, on_status, cancelled, target_language=None):
    if model == 'auto':
        from quality_pipeline import run
        return run(path, offline, on_segment, on_status, cancelled, target_language, transcribe)
    from faster_whisper import WhisperModel
    import ctranslate2
    if device == 'auto':
        try:
            device = 'cuda' if ctranslate2.get_cuda_device_count() else 'cpu'
        except Exception:
            device = 'cpu'
    # Çeviri için gereken modeli uzun kaydı işlemeye başlamadan doğrula.
    translators = {}
    if target_language and (language is None or language != target_language):
        from translation import LocalTranslator, Cancelled
        source = ('en' if target_language == 'tr' else 'tr') if language is None else language
        try:
            translators[source] = LocalTranslator(source, target_language, offline, on_status, cancelled)
        except Cancelled:
            return
    if cancelled():
        return
    on_status('Yazıya dönüştürme hazırlanıyor · ilk kullanımda gerekli dosyalar indirilebilir')
    local_large=ROOT/'models'/'large-v3-quality'
    selected=str(local_large) if model=='large-v3' and (local_large/'model.bin').is_file() else model
    engine = WhisperModel(selected, device=device,
                          compute_type='int8_float16' if device == 'cuda' else 'int8',
                          cpu_threads=min(8, os.cpu_count() or 4),
                          download_root=str(ROOT / 'models'), local_files_only=offline)
    if language is None:
        from recognition import constrain_lecture_languages
        constrain_lecture_languages(engine)
    if cancelled():
        return
    audio = None
    if language is None:
        from faster_whisper.audio import decode_audio
        on_status('Ses okunuyor · karışık diller için bölüm bazında dil algılama hazırlanıyor')
        audio = decode_audio(str(path), sampling_rate=16000)
    if audio is not None:
        from recognition import speech_windows
        from types import SimpleNamespace
        segments = speech_windows(engine, audio, cancelled, language)
        info = SimpleNamespace(language=language or 'tr', duration=len(audio)/16000)
    else:
        segments, info = engine.transcribe(str(path), language=language, beam_size=5,
            vad_filter=True, condition_on_previous_text=False, temperature=0.0,
            word_timestamps=True, hallucination_silence_threshold=2.0)
    language_cache = {}
    on_status(f'Dersin kelimeleri çözümleniyor · kayıt uzunluğu {info.duration / 60:.1f} dk')
    for s in segments:
        if cancelled():
            return
        original = s.text.strip()
        text = original
        source = info.language
        language_uncertain = False
        translation_review = False
        if audio is not None:
            # info.language yalnızca başlangıç dilidir. EN/TR geçişlerinde buna güvenme.
            window = int(s.start // 20)
            if window not in language_cache:
                left = window * 20 * 16000
                sample = audio[left:min(len(audio), left + 20 * 16000)]
                source_detected, confidence, _ = engine.detect_language(audio=sample, vad_filter=True)
                language_cache[window] = (source_detected, confidence)
            source, confidence = language_cache[window]
            if confidence < 0.5:
                left = max(0, int((s.start - 5) * 16000))
                right = min(len(audio), int((s.end + 5) * 16000))
                retried_source, retried_confidence, _ = engine.detect_language(audio=audio[left:right], vad_filter=False)
                if retried_confidence > confidence:
                    source, confidence = retried_source, retried_confidence
            language_uncertain = confidence < 0.5
            translation_review = language_uncertain
            from language_checks import text_language_hint
            hint = text_language_hint(original)
            if hint and hint != source:
                left = max(0, int(s.start * 16000))
                right = min(len(audio), int(s.end * 16000))
                local_source, local_confidence, _ = engine.detect_language(audio=audio[left:right], vad_filter=False)
                if local_source == hint or hint != target_language:
                    source, language_uncertain = hint, False
                elif local_confidence >= 0.5:
                    source, language_uncertain = local_source, False
                translation_review = language_uncertain
        original, recognition_review = refine_segment(engine, audio, s, source, on_status, cancelled)
        text = original
        if cancelled():
            return
        translated = False
        if target_language and source != target_language and (source, target_language) not in {('en', 'tr'), ('tr', 'en')}:
            translation_review = True
        if target_language:
            from translation import LocalTranslator, Cancelled
            from language_checks import translate_sentences,text_language_hint
            def get_translator(actual):
                if actual not in translators:
                    translators[actual]=LocalTranslator(actual,target_language,offline,on_status,cancelled)
                return translators[actual]
            if source != target_language or text_language_hint(original) != target_language:
                on_status(f'{"Türkçeye" if target_language == "tr" else "İngilizceye"} çevriliyor · {stamp(s.start)}')
            try:
                text,translated=translate_sentences(original,source,target_language,get_translator)
            except Cancelled:
                return
            translation_review = text_language_hint(text) not in (None,target_language)
        review = translation_review or recognition_review
        on_segment(Segment(s.start, s.end, text, original, source, translated, review), min(99, int(100 * s.end / max(info.duration, 1))))
