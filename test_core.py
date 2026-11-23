import unittest
from core import Segment, stamp, render

class ExportTests(unittest.TestCase):
    def test_plain_text_has_paragraphs_without_timestamps(self):
        from core import render_plain
        rows = [Segment(i * 2, i * 2 + 1, 'Bu bir ders cümlesidir. ' * 5) for i in range(12)]
        text = render_plain(rows)
        self.assertIn('\n\n', text)
        self.assertNotIn('00:', text)
        self.assertEqual(text.count('Bu bir ders cümlesidir.'), 60)
    def test_timestamp_rounding(self):
        self.assertEqual(stamp(59.9996, True), '00:01:00,000')
        self.assertEqual(stamp(3600.125), '01:00:00.125')
    def test_srt(self):
        self.assertEqual(render([Segment(0, 1.25, ' Türkçe ders ')], True),
                         '1\n00:00:00,000 --> 00:00:01,250\nTürkçe ders\n')
    def test_txt(self):
        self.assertIn('İstanbul', render([Segment(1, 2, 'İstanbul')]))

if __name__ == '__main__':
    unittest.main()
