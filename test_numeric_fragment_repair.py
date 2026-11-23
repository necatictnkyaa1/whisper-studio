import unittest
from unittest.mock import Mock
from lecture_translation import LectureTranslator,ModelError


class FragmentRepairTests(unittest.TestCase):
    def translator(self):
        t=object.__new__(LectureTranslator);t.status=Mock();t.cancelled=lambda:False
        return t
    def test_minus_and_values_are_inserted_without_model_control(self):
        t=self.translator();t.batch=Mock(side_effect=[{'0':'Bu durumda'},{'2':'a'},{'4':'b olur.'}])
        result=t.repair_numeric_fragments({'id':'9','text':'In this case minus 2 a plus 3 b.'},'tr','')
        self.assertEqual(result['9'],'Bu durumda eksi 2 a artı 3 b olur.')
        self.assertTrue(all(not any(c.isdigit() for c in call.args[0][0]['text']) for call in t.batch.call_args_list))
    def test_no_digits_still_translates_full_row(self):
        t=self.translator();t.batch=Mock(return_value={'0':'Üç bir iki artı üçüncü eleman yine bir konumdadır.'})
        self.assertIn('Üç',t.repair_numeric_fragments({'id':'174','text':'and three one two plus the third element is again one on a position.'},'tr','')['174'])
    def test_missing_content_or_sign_is_not_silently_returned(self):
        t=self.translator();t.batch=Mock(side_effect=ModelError('Hedef dil yanlış'))
        with self.assertRaises(ModelError):t.repair_numeric_fragments({'id':'1','text':'We have minus 2 metres.'},'tr','')
    def test_schema_exhaustion_uses_fragment_repair(self):
        t=self.translator();t.batch=Mock(side_effect=ModelError('Sayı korumalı metin parçaları eksik veya fazla.'))
        t.repair_numeric_fragments=Mock(return_value={'1':'Sonuç'})
        self.assertEqual(t.repair_row({'id':'1','text':'source'},'tr',''),{'1':'Sonuç'})
        t.repair_numeric_fragments.assert_called_once()


if __name__=='__main__':unittest.main()
