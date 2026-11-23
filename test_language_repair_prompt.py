import json
import unittest
from unittest.mock import Mock
from lecture_translation import LectureTranslator,validate,ModelError


class LanguageRepairPromptTests(unittest.TestCase):
    def test_clause_repair_checks_full_reassembled_row(self):
        t=object.__new__(LectureTranslator);t.status=lambda _:None;t.cancelled=lambda:False
        t.repair_target_language=Mock(side_effect=[{'0':'1a ifadesini çalıştır.'},{'1':'Sonra 1b ifadesini çalıştır.'}])
        row={'id':'154','text':'Execute statement 1a. Then execute statement 1b.'}
        self.assertIn('1b',t.repair_short_clauses(row,'tr')['154'])
        t.repair_target_language.side_effect=[{'0':'İfadeyi çalıştır.'},{'1':'Sonra ifadeyi çalıştır.'}]
        with self.assertRaisesRegex(ModelError,'sayısal'):
            t.repair_short_clauses(row,'tr')
    def test_repeated_plain_response_uses_bounded_clause_repair(self):
        t=object.__new__(LectureTranslator);t.status=lambda _:None
        t.batch=Mock(side_effect=ModelError('token repeat limit reached'))
        t.repair_target_language=Mock(side_effect=ModelError('token repeat limit reached'))
        t.repair_short_clauses=Mock(return_value={'1':'Hazır.'})
        row={'id':'1','text':'Ready. Go.'}
        self.assertEqual(t.repair_row(row,'tr',''),{'1':'Hazır.'})
        t.repair_short_clauses.assert_called_once_with(row,'tr')
    def test_repetition_abort_switches_to_validated_plain_translation(self):
        t=object.__new__(LectureTranslator);t.status=lambda _:None
        t.batch=Mock(side_effect=ModelError('prediction aborted, token repeat limit reached'))
        t.repair_target_language=Mock(return_value={'1':'1b ifadesini çalıştır.'})
        row={'id':'1','text':'Execute statement 1b.'}
        self.assertEqual(t.repair_row(row,'tr','')['1'],'1b ifadesini çalıştır.')
        self.assertEqual(t.batch.call_count,1)
        t.repair_target_language.assert_called_once_with(row,'tr')
    def test_plain_fallback_is_still_validated(self):
        t=object.__new__(LectureTranslator);t.client=Mock();t.plan=Mock();t.cancelled=lambda:False
        row={'id':'49','text':'Oh no, I have to change everything.'}
        t.client.chat.return_value=('Hayır, her şeyi değiştirmem gerekiyor.',{})
        self.assertIn('değiştirmem',t.repair_target_language(row,'tr')['49'])
        self.assertIsNone(t.client.chat.call_args.kwargs['schema'])
        t.client.chat.return_value=(row['text'],{})
        with self.assertRaises(ModelError):t.repair_target_language(row,'tr')
    def test_empty_word_response_uses_validated_plain_retry(self):
        t=object.__new__(LectureTranslator);t.status=lambda _:None
        t.batch=Mock(side_effect=ModelError('Çeviri metin uzunluğu doğrulanamadı.'))
        t.repair_target_language=Mock(return_value={'47':'boş'})
        row={'id':'47','text':'blank'}
        self.assertEqual(t.repair_row(row,'tr',''),{'47':'boş'})
        self.assertEqual(t.batch.call_count,3)
        t.repair_target_language.assert_called_once_with(row,'tr')
    def test_truncated_response_uses_fragment_repair(self):
        t=object.__new__(LectureTranslator);t.status=lambda _:None
        t.batch=Mock(side_effect=ModelError('Çeviri yanıtı sınırda kesildi.'))
        t.repair_numeric_fragments=Mock(return_value={'1':'10 üzeri 2'})
        row={'id':'1','text':'10 on degree 2'}
        self.assertEqual(t.repair_row(row,'tr',''),{'1':'10 üzeri 2'})
        t.repair_numeric_fragments.assert_called_once_with(row,'tr','')
    def test_foreign_sentence_retry_changes_prompt_and_keeps_target(self):
        t=object.__new__(LectureTranslator);t.client=Mock();t.plan=Mock();t.cancelled=lambda:False
        t.client.chat.return_value=(json.dumps({'translations':{'49':'Hayır, her şeyi değiştirmem gerekiyor. Bunun için teşekkür ederim.'}}),{})
        source='Oh no, I have to change everything, Thank you for that with me.'
        output=t.batch([{'id':'49','text':source}],'tr',repair_feedback='Çeviride hedef dil dışında cümle kaldı.')
        self.assertIn('değiştirmem',output['49'])
        prompt=t.client.chat.call_args.args[1][0]['content']
        self.assertIn('translator into Turkish',prompt)
        self.assertIn('Do not copy a foreign-language sentence',prompt)
        with self.assertRaisesRegex(ModelError,'hedef dil'):
            validate([{'id':'49','text':source}],{'translations':{'49':source}},'tr')


if __name__=='__main__':unittest.main()
