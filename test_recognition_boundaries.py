import unittest
import numpy as np
from recognition import pause_boundaries, RATE, _plans, constrain_lecture_languages
from unittest.mock import Mock


class BoundaryTests(unittest.TestCase):
    def test_quiet_gap_is_used_without_dropping_any_audio(self):
        audio=np.ones(60*RATE,dtype=np.float32)*.1
        audio[20*RATE:21*RATE]=0
        ranges=list(pause_boundaries(audio,lambda:False))
        self.assertTrue(20<ranges[0][1]<21)
        self.assertEqual(ranges[0][0],0)
        self.assertEqual(ranges[-1][1],60)
        for left,right in zip(ranges,ranges[1:]):self.assertEqual(left[1],right[0])
        self.assertTrue(all(0<b-a<=26 for a,b in ranges))

    def test_continuous_speech_has_bounded_chunks_and_tail(self):
        self.assertEqual(list(pause_boundaries(np.ones(53*RATE),lambda:False)),[(0,26),(26,52),(52,53)])
        self.assertEqual(list(pause_boundaries(np.ones(17),lambda:False)),[(0,17/RATE)])

    def test_cancellation_and_empty(self):
        self.assertEqual(list(pause_boundaries(np.ones(RATE),lambda:True)),[])
        self.assertEqual(list(pause_boundaries(np.array([]),lambda:False)),[])

    def test_mixed_language_split_survives_candidate(self):
        engine=Mock();engine.detect_language.side_effect=[('tr',.9,[]),('en',.9,[])]
        constrain_lecture_languages(engine)
        self.assertEqual(list(_plans(engine,np.ones(24*RATE),None,24,2,lambda:False,'pause')),
                         [(0,12,'tr'),(12,24,'en')])

    def test_invalid_settings_fail(self):
        with self.assertRaises(ValueError):list(pause_boundaries(np.ones(RATE),lambda:False,10,16))

    def test_short_candidate_covers_tail_and_never_exceeds_twelve_seconds(self):
        audio=np.ones(25*RATE,dtype=np.float32)*.1
        audio[9*RATE:10*RATE]=0
        engine=Mock()
        plans=list(_plans(engine,audio,'en',24,2,lambda:False,'pause-short'))
        self.assertEqual(plans[0][0],0)
        self.assertTrue(9<plans[0][1]<10)
        self.assertEqual(plans[-1][1],25)
        self.assertTrue(all(0<b-a<=12 for a,b,_ in plans))
        for left,right in zip(plans,plans[1:]):self.assertEqual(left[1],right[0])


if __name__=='__main__':unittest.main()
