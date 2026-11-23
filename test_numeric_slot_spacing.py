import unittest
from lecture_translation import mask_numbers,assemble_number_slots,validate,ModelError


class NumericSlotSpacingTests(unittest.TestCase):
    def test_negative_slot_after_word_without_model_whitespace(self):
        source='We have 10 and minus 9.'
        _,tokens=mask_numbers(source,'tr')
        answer={'translations':{'1':{'before':'Değerler','betweena':'ve','after':'olur.'}}}
        answer=assemble_number_slots(answer,{'1':tokens})
        self.assertEqual(answer['translations']['1'],'Değerler 10 ve eksi 9 olur.')
        validate([{'id':'1','text':source}],answer,'tr')
    def test_actual_failed_row_keeps_minus_boundaries(self):
        source='we will have micrometre that is 10 on degree minus six or as we have one divided with one there we have nanometers 10 to the degree of minus 9,'
        _,tokens=mask_numbers(source,'tr')
        answer={'translations':{'119':{'before':'Mikrometre','betweena':'üzeri eksi altı; nanometre','betweenaa':'üzeri','after':'olur.'}}}
        answer=assemble_number_slots(answer,{'119':tokens})
        self.assertIn('üzeri eksi 9',answer['translations']['119'])
        validate([{'id':'119','text':source}],answer,'tr')
    def test_lost_minus_is_still_rejected(self):
        with self.assertRaisesRegex(ModelError,'eksi işareti'):
            validate([{'id':'1','text':'minus 9'}],{'translations':{'1':'9 olur.'}},'tr')
    def test_superscript_numbers_cannot_be_smuggled_into_fragments(self):
        _,tokens=mask_numbers('minus 9','tr')
        with self.assertRaises(ModelError):
            assemble_number_slots({'translations':{'1':{'before':'¹⁰⁻⁹','after':''}}},{'1':tokens})
    def test_written_negative_exponent_cannot_disappear(self):
        source='10 on degree minus six and minus 9'
        with self.assertRaisesRegex(ModelError,'yazıyla'):
            validate([{'id':'1','text':source}],{'translations':{'1':'10 ve eksi 9'}},'tr')
        validate([{'id':'1','text':source}],{'translations':{'1':'10 üzeri eksi altı ve eksi 9'}},'tr')


if __name__=='__main__':unittest.main()
