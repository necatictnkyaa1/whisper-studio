import unittest
from quality_bench.metrics import normalize,score,aggregate,spoken_number_score,turkish_integer

class BenchmarkMetricTests(unittest.TestCase):
 def test_supplementary_number_format_score_does_not_replace_wrong_numbers(self):
  self.assertEqual(turkish_integer(2007),'iki bin yedi')
  self.assertEqual(spoken_number_score('on yedi kişi','17 kişi','tr')['errors'],0)
  self.assertGreater(spoken_number_score('on yedi kişi','18 kişi','tr')['errors'],0)
  self.assertGreater(score('on yedi kişi','17 kişi','tr')['errors'],0)
 def test_turkish_case_and_punctuation_do_not_change_lexical_score(self):
  self.assertEqual(normalize("IŞIK İÇİN, Ankara'da!",'tr'),'ışık için ankarada')
  self.assertEqual(score('IŞIK İÇİN','ışık için','tr')['errors'],0)
  self.assertNotEqual(normalize('sık','tr'),normalize('sik','tr'))
 def test_substitution_deletion_and_insertion_are_counted(self):
  s=score('bir iki üç dört','bir beş üç altı dört','tr')
  self.assertEqual((s['substitutions'],s['deletions'],s['insertions']),(1,0,1))
  self.assertEqual(score('bir iki üç','bir üç','tr')['deletions'],1)
  self.assertEqual(score('','uydurma','tr')['insertions'],1)
 def test_aggregate_is_word_weighted_not_mean_of_clip_percentages(self):
  rows=[{'score':score('a','b','en'),'seconds':1,'duration':2},
        {'score':score('a b c d e f g h i','a b c d e f g h i','en'),'seconds':1,'duration':3}]
  self.assertAlmostEqual(aggregate(rows)['wer'],.1)
 def test_numbers_are_not_silently_deleted(self):
  self.assertGreater(score('17 öğrenci','18 öğrenci','tr')['errors'],0)
  self.assertGreater(score('-1','1','tr')['errors'],0)
  self.assertGreater(spoken_number_score('-1','1','tr')['errors'],0)

if __name__=='__main__':unittest.main()
