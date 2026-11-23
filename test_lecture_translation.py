import unittest
from unittest.mock import Mock,patch
from dataclasses import replace
from core import Segment
from lecture_translation import validate,validate_alignment,context_terms,LectureTranslator,ModelError

class LectureTranslationTests(unittest.TestCase):
 def test_english_target_uses_english_system_not_turkish_examples(self):
  import json
  from lecture_translation import SYSTEM_EN
  t=object.__new__(LectureTranslator);t.cancelled=lambda:False;t.plan=Mock();t.client=Mock()
  t.client.chat.return_value=(json.dumps({'translations':{'1':'This is an example.'}}),{})
  self.assertEqual(t.batch([{'id':'1','text':'Bu bir örnektir.'}],'en')['1'],'This is an example.')
  self.assertEqual(t.client.chat.call_args.args[1][0]['content'],SYSTEM_EN)
 def test_parameter_length_must_not_disappear_while_count_survives(self):
  source='Block and stack methods do not limit the number or length of parameters.'
  with self.assertRaises(ModelError):
   validate([{'id':'1','text':source}],{'translations':{'1':'Yığın yöntemleri parametre sayısını sınırlamaz.'}},'tr')
  validate([{'id':'1','text':source}],{'translations':{'1':'Bloklama ve yığına yerleştirme yöntemleri parametre sayısını veya uzunluğunu sınırlamaz.'}},'tr')
 def test_okay_is_not_tamami_but_real_whole_is_preserved(self):
  with self.assertRaises(ModelError):
   validate([{'id':'1','text':'The number is not limited, okay?'}],{'translations':{'1':'Sayı sınırlı değildir, tamamı?'}},'tr')
  validate([{'id':'1','text':'All of them, okay?'}],{'translations':{'1':'Tamamı, tamam mı?'}},'tr')
  validate([{'id':'1','text':'The parameters are stored, okay?'}],{'translations':{'1':'Parametrelerin tamamı saklanır, tamam mı?'}},'tr')
 def test_long_rows_are_translated_in_their_own_requests(self):
  t=object.__new__(LectureTranslator);t.status=Mock();t.cancelled=lambda:False
  long='This sentence explains the parameter passing method. '*7
  t.batch=Mock(side_effect=[{'0':'Yazmaç.'},{'1':'Uzun açıklama.'},{'2':'Yığın.'}])
  t.translate([Segment(0,1,'Register.'),Segment(2,3,long),Segment(4,5,'Stack.')],'tr',Mock())
  self.assertEqual([len(call.args[0]) for call in t.batch.call_args_list],[1,1,1])
 def test_previous_sentences_are_not_sent_as_translation_input(self):
  import json
  context='Do not translate this previous sentence. The operating system keeps parameters in a register. Windows.'
  self.assertIn('register',context_terms(context))
  self.assertNotIn(context,context_terms(context))
  t=object.__new__(LectureTranslator);t.cancelled=lambda:False;t.plan=Mock();t.client=Mock()
  t.client.chat.return_value=(json.dumps({'translations':{'1':'Bu bir örnektir.'}}),{})
  t.batch([{'id':'1','text':'This is an example.'}],'tr',context)
  request=json.loads(t.client.chat.call_args.args[1][1]['content'])
  self.assertNotIn('context_only_do_not_translate',request)
  self.assertEqual(request['rows'][0]['text'],'This is an example.')
  self.assertEqual(request['previous_topic_terms_not_sentences'],context_terms(context))
 def test_context_cannot_replace_a_different_source_row(self):
  prior='Daha önce sistem çağrılarının farklı işlemlere ayrıldığını söyledik. Burada bu işlemler için bazı örnekler göreceksiniz.'
  with self.assertRaises(ModelError):
   validate_alignment('This system call name belongs to Windows.',prior,[('System calls are divided into parts. Here are examples.',prior)])
  validate_alignment('System calls are divided into parts. Here are examples.',prior,[('System calls are divided into parts. Here are examples.',prior)])
  validate_alignment('This is a system call.','Bu bir sistem çağrısıdır.',[('That is a system call.','Bu bir sistem çağrısıdır.')])
 def test_windows_must_not_disappear_or_become_context(self):
  with self.assertRaises(ModelError):
   validate([{'id':'64','text':'This system call name belongs to Windows.'}],{'translations':{'64':'Bu sistem çağrısının adı işletim sistemine göre değişebilir.'}},'tr')
 def test_context_leak_is_retried_without_adjacent_context(self):
  t=object.__new__(LectureTranslator);t.status=Mock();t.cancelled=lambda:False
  prior='Daha önce sistem çağrılarının farklı işlemlere ayrıldığını söyledik. Burada bu işlemler için bazı örnekler göreceksiniz.'
  t.previous_translations=[Segment(0,1,prior,original='System calls are divided into parts. Here are examples.')]
  t.batch=Mock(side_effect=[{'0':prior},{'0':'Bu sistem çağrısının adı Windows sistemine aittir.'}]);result=[]
  t.translate([Segment(2,3,'This system call name belongs to Windows.')],'tr',lambda s,p:result.append(s))
  self.assertIn('Windows',result[0].text)
  self.assertEqual(t.batch.call_args.args[2],'')
 def test_mapping_rejects_missing_duplicate_and_changed_digits(self):
  rows=[{'id':'1','text':'The register contains 13.'}]
  for answer in [{'translations':[]},{'translations':[{'id':'1','text':'Yazmaç 12 içerir.'}]},{'translations':[{'id':'2','text':'Yazmaç 13 içerir.'}]}]:
   with self.assertRaises(ModelError):validate(rows,answer)
 def test_english_left_inside_turkish_output_is_rejected(self):
  rows=[{'id':'1','text':'It has to be repeated.'}]
  with self.assertRaises(ModelError):
   validate(rows,{'translations':[{'id':'1','text':'Bu bir konu, It has to be repeated.'}]},'tr')
 def test_misheard_executables_is_not_an_exec_function(self):
  rows=[{'id':'1','text':'Modern systems do not link libraries into exec tables.'}]
  result=validate(rows,{'translations':{'1':'Modern sistemler kütüphaneleri çalıştırılabilir dosyalara bağlamaz.'}},'tr')
  self.assertIn('1',result)
  with self.assertRaises(ModelError):
   validate([{'id':'1','text':'An exec() call loads the process.'}],{'translations':{'1':'Bir çağrı işlemi yükler.'}},'tr')
 def test_names_and_numbers_survive(self):
  rows=[{'id':'7','text':'FreeBSD uses fork, example 13.'}]
  answer={'translations':[{'id':'7','text':'FreeBSD fork kullanır, örnek 13.'}]}
  self.assertEqual(validate(rows,answer)['7'],answer['translations'][0]['text'])
  answer['translations'][0]['text']='FreeBSD çatal kullanır, örnek 13.'
  with self.assertRaises(ModelError):validate(rows,answer)
 def test_retry_is_individual_and_timestamps_are_preserved(self):
  t=object.__new__(LectureTranslator);t.status=Mock();t.cancelled=lambda:False
  t.batch=Mock(side_effect=[ModelError('incomplete'),{'0':'Yığın kullanılır.'},{'1':'Yazmaç kullanılır.'}])
  rows=[Segment(1,3,'Stack is used.'),Segment(4,8,'A register is used.')];result=[]
  t.translate(rows,'tr',lambda row,p:result.append(row))
  self.assertEqual([(s.start,s.end) for s in result],[(1,3),(4,8)])
  self.assertEqual(result[0].original,'Stack is used.')
  self.assertEqual(t.batch.call_count,3)
 def test_cancellation_never_publishes_untranslated_rows(self):
  from llm import Cancelled
  t=object.__new__(LectureTranslator);t.cancelled=lambda:True;t.batch=Mock()
  with self.assertRaises(Cancelled):t.translate([Segment(0,2,'test')],'tr',Mock())
  t.batch.assert_not_called()
 def test_offline_missing_quality_model_stops_owned_server(self):
  client=Mock();client.installed.return_value=set()
  with patch('lecture_translation.OllamaClient',return_value=client),patch('lecture_translation.inspect_hardware'):
   with self.assertRaises(ModelError):LectureTranslator(True,Mock(),lambda:False)
  client.stop.assert_called_once()

if __name__=='__main__':unittest.main()
