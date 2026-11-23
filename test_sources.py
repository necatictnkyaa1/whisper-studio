import tempfile
import unittest
from pathlib import Path
from core import Segment
from sources import SourceLibrary, SourceError, split_long

def text_pdf(path, pages):
    """Standart Helvetica/WinAnsi metin katmanlı küçük PDF; boş metin = metinsiz sayfa."""
    objs = [b'<< /Type /Catalog /Pages 2 0 R >>', None,
            b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>']
    kids = []
    for text in pages:
        stream = ('BT /F1 12 Tf 72 720 Td (' + text + ') Tj ET').encode('cp1252')
        objs.append(b'<< /Length %d >>\nstream\n' % len(stream) + stream + b'\nendstream')
        objs.append(b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R >> >> '
                    b'/Contents %d 0 R >>' % len(objs))
        kids.append(len(objs))
    objs[1] = b'<< /Type /Pages /Kids [%s] /Count %d >>' % (b' '.join(b'%d 0 R' % k for k in kids), len(kids))
    out, offsets = b'%PDF-1.4\n', []
    for number, obj in enumerate(objs, 1):
        offsets.append(len(out))
        out += b'%d 0 obj\n' % number + obj + b'\nendobj\n'
    xref = len(out)
    out += b'xref\n0 %d\n0000000000 65535 f \n' % (len(objs) + 1) + b''.join(b'%010d 00000 n \n' % o for o in offsets)
    out += b'trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n' % (len(objs) + 1, xref)
    Path(path).write_bytes(out)

class SourceTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.dir = Path(self.folder.name)
    def tearDown(self):
        self.folder.cleanup()

    def test_pdf_pages_keep_page_numbers_and_report_textless_pages(self):
        pdf = self.dir / 'hoca.pdf'
        text_pdf(pdf, ['Gradient descent updates the weights with a learning rate.', '',
                       'Taylor series: f(x) = f(a) + f\'(a)(x-a) + ... for smooth functions.'])
        library = SourceLibrary()
        source = library.add_file(pdf)
        self.assertEqual(source.page_count, 3)
        self.assertEqual(source.unread_pages, [2])
        self.assertEqual([p.page for p in source.passages], [1, 3])
        self.assertEqual(library.describe(source.passages[1].id), 'hoca.pdf, s. 3')
        self.assertIn('2/3 sayfa okundu', source.summary())

    def test_image_only_pdf_is_rejected_honestly(self):
        pdf = self.dir / 'tarama.pdf'
        text_pdf(pdf, ['', ''])
        with self.assertRaises(SourceError) as error:
            SourceLibrary().add_file(pdf)
        self.assertIn('görsel', str(error.exception))

    def test_markdown_headings_become_locations(self):
        note = self.dir / 'notlarim.md'
        note.write_text('# Gradyan inişi\nÖğrenme oranı küçük seçilir.\n\n# Taylor serisi\nYerel yaklaşım verir.',
                        encoding='utf-8')
        library = SourceLibrary()
        source = library.add_file(note)
        self.assertEqual([p.location for p in source.passages], ['bölüm “Gradyan inişi”', 'bölüm “Taylor serisi”'])
        self.assertIn('Öğrenme oranı', source.passages[0].text)

    def test_turkish_windows_encoding_text_is_read(self):
        note = self.dir / 'eski.txt'
        note.write_bytes('Öğrenci notu: ağırlıklar güncellenir. Şimdi İstanbul.'.encode('cp1254'))
        source = SourceLibrary().add_file(note)
        self.assertIn('ağırlıklar', source.passages[0].text)
        self.assertIn('İstanbul', source.passages[0].text)

    def test_transcript_passages_carry_time_and_original(self):
        segments = [Segment(i * 30, i * 30 + 25, f'Türkçe cümle {i}. ' * 12, f'English sentence {i}. ' * 12, 'en', True)
                    for i in range(10)]
        library = SourceLibrary()
        source = library.add_transcript(segments)
        self.assertGreater(len(source.passages), 1)
        self.assertEqual(source.passages[0].location.split('–')[0], '00:00')
        self.assertIn('English sentence 0', source.passages[0].original)
        joined = ' '.join(p.text for p in source.passages)
        for i in range(10):
            self.assertIn(f'Türkçe cümle {i}.', joined)

    def test_ids_are_unique_and_removal_drops_passages(self):
        library = SourceLibrary()
        a = self.dir / 'a.txt'
        b = self.dir / 'b.txt'
        a.write_text('Birinci kaynak metni yeterince uzun.', encoding='utf-8')
        b.write_text('İkinci kaynak metni yeterince uzun.', encoding='utf-8')
        first, second = library.add_file(a), library.add_file(b)
        self.assertNotEqual(first.passages[0].id, second.passages[0].id)
        with self.assertRaises(SourceError):
            library.add_file(a)
        library.remove(first.id)
        self.assertIsNone(library.passage(first.passages[0].id))
        self.assertEqual(len(library.passages), 1)

    def test_unsupported_file_type(self):
        doc = self.dir / 'odev.docx'
        doc.write_bytes(b'PK')
        with self.assertRaises(SourceError):
            SourceLibrary().add_file(doc)

    def test_split_long_loses_no_words(self):
        text = ' '.join(f'kelime{i}' for i in range(900))
        parts = split_long(text, 500)
        self.assertTrue(all(len(p) <= 500 for p in parts))
        self.assertEqual(' '.join(parts).split(), text.split())

if __name__ == '__main__':
    unittest.main()
