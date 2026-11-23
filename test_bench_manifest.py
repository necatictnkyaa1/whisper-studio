import hashlib,json,unittest,wave
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parent/'quality_bench'

class BenchmarkManifestTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.samples=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))['samples']
 def test_sources_and_artificial_controls_stay_distinct(self):
  originals=[s for s in self.samples if not s['derived']]
  self.assertEqual(len(originals),20)
  self.assertEqual(Counter(s['group'] for s in originals),{'fleurs-tr':5,'media-tr':5,'libri-clean':5,'libri-other':5})
  self.assertEqual(len({s['id'] for s in self.samples}),24)
  self.assertEqual(len({s['sha256'] for s in originals}),20)
  for sample in originals:
   self.assertTrue(sample['reference']);self.assertTrue(sample['attribution'])
   self.assertEqual(sample['license'],'CC-BY-4.0')
 def test_files_match_the_frozen_hash_and_sampling_format(self):
  for sample in self.samples:
   path=ROOT/sample['file']
   self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),sample['sha256'])
   with wave.open(str(path)) as audio:
    self.assertEqual((audio.getnchannels(),audio.getsampwidth(),audio.getframerate()),(1,2,16000))
    self.assertAlmostEqual(audio.getnframes()/16000,sample['duration'],places=3)
 def test_derived_references_are_only_their_parent_references(self):
  by_id={s['id']:s for s in self.samples}
  for sample in self.samples:
   if sample['derived']:
    self.assertEqual(sample['reference'],' '.join(by_id[p]['reference'] for p in sample['parents']))
    self.assertTrue(sample['transformation'])

if __name__=='__main__':unittest.main()
