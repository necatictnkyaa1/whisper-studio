import tempfile,unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock,patch
from core import Segment
from automatic import Hardware
import quality_pipeline

class PipelineTests(unittest.TestCase):
 def test_asr_finishes_before_translation_and_cache_reuses_original(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'input.wav';path.write_bytes(b'audio');events=[]
   translator=Mock()
   translator.translate.side_effect=lambda rows,target,emit,start_at=0: (events.append('translation'),emit(replace(rows[0],original=rows[0].text),90)) if start_at==0 else None
   def runner(path,model,language,device,offline,emit,status,cancelled,**kw):
    self.assertIsNone(kw.get('target_language'));events.append('asr');emit(Segment(1,2,'original'),20)
   def automatic(path,offline,emit,status,cancelled,target,run):
    self.assertIsNone(target);run(path,'large-v3',None,'cuda',offline,emit,status,cancelled,target_language=None)
   with patch('quality_pipeline.__file__',str(Path(folder)/'quality_pipeline.py')),patch('quality_pipeline.inspect_hardware',return_value=Hardware(16000,3000,12000,True)),patch('quality_pipeline.cached',return_value=True),patch('quality_pipeline.run_automatic',side_effect=automatic) as automatic_mock,patch('lecture_translation.LectureTranslator',return_value=translator):
    for _ in range(2):quality_pipeline.run(path,True,lambda s,p:events.append('published'),Mock(),lambda:False,'tr',runner)
    self.assertEqual(automatic_mock.call_count,1)
   self.assertEqual(events,['asr','translation','published','published'])
   self.assertEqual(translator.close.call_count,2)
 def test_cancelled_asr_never_creates_complete_cache(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'input.wav';path.write_bytes(b'audio');cancel=[False];translator=Mock()
   def automatic(*args):cancel[0]=True
   with patch('quality_pipeline.__file__',str(Path(folder)/'quality_pipeline.py')),patch('quality_pipeline.inspect_hardware',return_value=Hardware(16000,3000,12000,True)),patch('quality_pipeline.cached',return_value=True),patch('quality_pipeline.run_automatic',side_effect=automatic),patch('lecture_translation.LectureTranslator',return_value=translator):
    quality_pipeline.run(path,True,Mock(),Mock(),lambda:cancel[0],'tr',Mock())
   translator.translate.assert_not_called();translator.close.assert_called_once()
   self.assertEqual(list(Path(folder).rglob('*.json')),[])

if __name__=='__main__':unittest.main()
