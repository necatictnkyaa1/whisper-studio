import unittest
from lecture_translation import protected_identifiers,validate,ModelError


class IdentifierContextTests(unittest.TestCase):
    def test_wall_windows_are_translatable(self):
        source='But if we have this wall and this wall with the windows, do they have the same points?'
        self.assertEqual(protected_identifiers(source),[])
        validate([{'id':'1','text':source}],{'translations':{'1':'Bu duvar ile pencereleri olan bu duvarın ortak noktaları var mı?'}},'tr')
    def test_windows_operating_system_stays_protected(self):
        for source in ('We use Windows.','We use windows operating system.','The computer near the wall runs windows.'):
            self.assertTrue(protected_identifiers(source))
            with self.assertRaisesRegex(ModelError,'özel ad'):
                validate([{'id':'1','text':source}],{'translations':{'1':'Bu sistem burada kullanılıyor.'}},'tr')
    def test_other_identifiers_are_unchanged(self):
        self.assertEqual(protected_identifiers('Linux and Arduino near the wall with the windows.'),['Linux','Arduino'])


if __name__=='__main__':unittest.main()
