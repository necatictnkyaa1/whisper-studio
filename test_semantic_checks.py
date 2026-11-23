import unittest
from semantic_checks import rank_requirements,missing_ranks,missing_past_marker,missing_state_transition
from lecture_translation import validate,ModelError

class RankCheckTests(unittest.TestCase):
 def test_state_values_cannot_flip_despite_correct_time_markers(self):
  source='This server used to be offline, but it is online now.'
  self.assertTrue(missing_state_transition(source,'Bu sunucu daha önce çevrimdışıydı, ancak şimdi çevrimdışı.'))
  self.assertTrue(missing_state_transition(source,'Bu sunucu daha önce çevrimiçiydi, ancak şimdi çevrimdışı.'))
  self.assertTrue(missing_state_transition(source,'Bu sunucu daha önce çevrimdışıydı, şimdi çevrimiçi değil.'))
  self.assertFalse(missing_state_transition(source,'Bu sunucu daha önce çevrim dışıydı, şimdi çevrim içi.'))
 def test_reverse_state_transition_is_checked_in_its_own_direction(self):
  source='The server used to be online but now it is offline.'
  self.assertFalse(missing_state_transition(source,'Sunucu eskiden çevrimiçiydi, şimdi çevrimdışı.'))
  self.assertTrue(missing_state_transition(source,'Sunucu eskiden çevrimdışıydı, şimdi çevrimiçi.'))
 def test_explicit_former_and_current_state_remains_distinct(self):
  source='The server used to be offline, but now it is online.'
  with self.assertRaises(ModelError):
   validate([{'id':'1','text':source}],{'translations':{'1':'Sunucu artık çevrimdışı ama artık çevrimiçi.'}},'tr')
  validate([{'id':'1','text':source}],{'translations':{'1':'Sunucu daha önce çevrimdışıydı, şimdi çevrimiçi.'}},'tr')
 def test_ordinary_now_sentence_does_not_require_a_past_claim(self):
  self.assertFalse(missing_past_marker('The server is online now.','Sunucu şimdi çevrimiçi.'))
  self.assertFalse(missing_past_marker("Now translate the phrase 'used to be'.","Şimdi 'used to be' ifadesini çevir."))
 def test_wrong_written_rank_is_rejected(self):
  source='Anna finished ninth and Katja finished tenth.'
  with self.assertRaises(ModelError):
   validate([{'id':'1','text':source}],{'translations':{'1':'Anna dördüncü, Katja onuncu oldu.'}},'tr')
  validate([{'id':'1','text':source}],{'translations':{'1':'Anna dokuzuncu, Katja onuncu oldu.'}},'tr')
 def test_digit_rank_equivalent_is_allowed(self):
  validate([{'id':'1','text':'The runner placed seventh.'}],{'translations':{'1':'Koşucu 7. sırada yer aldı.'}},'tr')
 def test_discourse_first_and_time_second_are_not_ranking_claims(self):
  self.assertEqual(rank_requirements('First, wait a second and call the second process.'),[])
  self.assertEqual(missing_ranks('He came first.','İlk sırada geldi.'),[])
 def test_compound_ranks_outside_scope_are_not_guessed(self):
  self.assertEqual(rank_requirements('She finished twenty-first.'),[])
 def test_inflected_and_separately_written_turkish_ordinals(self):
  self.assertEqual(missing_ranks('She finished thirteenth.','On üçüncüydü.'),[])
  self.assertEqual(missing_ranks('She finished ninth.','Dokuzunculuğu elde etti.'),[])

if __name__=='__main__':unittest.main()
