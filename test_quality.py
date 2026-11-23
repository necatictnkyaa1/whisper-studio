import unittest
from unittest.mock import Mock
from types import SimpleNamespace as NS
import numpy as np
from recognition import speech_windows
from language_checks import translate_sentences,repetitive,text_language_hint
from automatic import Hardware,profiles

class QualityTests(unittest.TestCase):
    def test_third_language_is_not_reintroduced_inside_decoder(self):
        from recognition import constrain_lecture_languages
        engine=Mock()
        engine.detect_language.return_value=('pt',.6,[('pt',.6),('en',.3),('tr',.1)])
        engine.transcribe.return_value=(iter([]),None)
        constrain_lecture_languages(engine)
        list(speech_windows(engine,np.ones(16000,dtype='float32'),lambda:False))
        self.assertEqual(engine.transcribe.call_args.kwargs['language'],'en')
        self.assertFalse(engine.transcribe.call_args.kwargs['multilingual'])

    def test_a_language_change_inside_window_splits_the_audio(self):
        from recognition import constrain_lecture_languages,_plans
        engine=Mock();engine.detect_language.side_effect=[('tr',.9,[]),('en',.95,[])]
        constrain_lecture_languages(engine)
        plans=list(_plans(engine,np.ones(12*16000),None,24,2,lambda:False))
        self.assertEqual(plans,[(0,6.0,'tr'),(6.0,12.0,'en')])

    def test_domain_hint_requires_actual_earlier_topic_evidence(self):
        from recognition import _windows
        engine=Mock()
        engine.transcribe.side_effect=[
            (iter([NS(start=0,end=10,text='Operating system parameter register',words=None)]),None),
            (iter([NS(start=3,end=8,text='file management',words=None)]),None)]
        list(_windows(engine,np.ones(48*16000,dtype='float32'),lambda:False))
        self.assertIsNone(engine.transcribe.call_args_list[0].kwargs['hotwords'])
        self.assertIn('file management',engine.transcribe.call_args_list[1].kwargs['hotwords'])

    def test_short_english_question_has_language(self):
        self.assertEqual(text_language_hint('What is MSA?'),'en')
        self.assertIsNone(text_language_hint('MSA'))
    def test_mixed_sentences_keep_turkish_and_translate_english(self):
        translator=Mock();translator.translate.return_value='Son konu neydi?'
        factory=Mock(return_value=translator)
        result,changed=translate_sentences('Bu konuyu geçen hafta anlattım. What was the last topic?', 'tr','tr',factory)
        self.assertEqual(result,'Bu konuyu geçen hafta anlattım. Son konu neydi?')
        factory.assert_called_once_with('en');self.assertTrue(changed)
    def test_english_clause_inside_turkish_paragraph_is_translated(self):
        translator=Mock();translator.translate.return_value='Tekrarlanması gerekiyor,'
        text,_=translate_sentences('Bu bir konu, It has to be iterated, yaklaşık bir çözüm ve burada biz çalışacağız.', 'tr','tr',lambda _:translator)
        self.assertNotIn('It has to',text)
        self.assertIn('yaklaşık bir çözüm ve burada biz çalışacağız.',text)

    def test_repetition_is_retried_not_shown(self):
        translator=Mock();translator.translate.side_effect=['Hangi '*16,'Hangisi?']
        text,_=translate_sentences('Which function?', 'en','tr',lambda _:translator)
        self.assertEqual(text,'Hangisi?');self.assertFalse(repetitive(text))
    def test_overlap_has_single_word_ownership_and_absolute_time(self):
        def word(start,end,text):return NS(start=start,end=end,word=text)
        engine=Mock()
        engine.transcribe.side_effect=[
            (iter([NS(start=22,end=25,text='First second.',words=[word(22,23,' First'),word(24,25,' second.')])]),None),
            (iter([NS(start=0,end=3,text='First second.',words=[word(0,1,' First'),word(2,3,' second.')])]),None)]
        rows=list(speech_windows(engine,np.ones(48*16000,dtype='float32'),lambda:False))
        self.assertEqual(' '.join(row.text for row in rows),'First second.')
        self.assertEqual(rows[0].start,22);self.assertEqual(rows[-1].end,25)
        self.assertFalse(engine.transcribe.call_args.kwargs['vad_filter'])
    def test_silence_and_cancel_never_invent_text(self):
        engine=Mock()
        self.assertEqual(list(speech_windows(engine,np.zeros(16000),lambda:False)),[])
        self.assertEqual(list(speech_windows(engine,np.ones(16000),lambda:True)),[])
        engine.transcribe.assert_not_called()
    def test_gpu_quality_is_not_demoted_at_three_gb_ram(self):
        self.assertEqual(profiles(Hardware(16000,3200,12000,True))[0].model,'large-v3')
        self.assertEqual(profiles(Hardware(16000,800,12000,True))[0].model,'small')

if __name__=='__main__':unittest.main()
