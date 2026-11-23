import tempfile
import unittest
from pathlib import Path
from dataclasses import replace
from batch_transcription import create_job,load_job,run_job
from core import Segment


class FakeTranslator:
    calls=[]
    def __init__(self,*args):pass
    def translate(self,rows,target,publish,start_at=0):
        self.calls.append((target,start_at))
        for row in rows[start_at:]:publish(replace(row,text=target+' metin',original=row.text),99)
    def close(self):pass


class BatchTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);FakeTranslator.calls=[]
    def tearDown(self):self.tmp.cleanup()
    def source(self,name):
        p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'audio');return p
    def run_queue(self,path,runner,cancelled=lambda:False,factory=FakeTranslator):
        return run_job(path,True,lambda text:None,cancelled,lambda i,r:None,runner,factory)
    def test_43_recordings_two_named_txt_each_asr_only_once_and_resume(self):
        sources=[self.source(f'Ders {i}.mp3') for i in range(43)]
        manifest=create_job(sources,self.root);calls=[]
        def runner(path,*args,**kwargs):calls.append(path);args[4](Segment(1,2,'original'),99)
        job=self.run_queue(manifest,runner)
        self.assertEqual(len(calls),43);self.assertTrue(all(r['state']=='Tamamlandı' for r in job['records']))
        self.assertEqual(len(list(manifest.parent.glob('*.txt'))),86)
        for lang in ('tr','en'):
            text=(manifest.parent/f'Ders 0-{lang}.txt').read_text(encoding='utf-8-sig')
            self.assertEqual(text,lang+' metin\n');self.assertNotIn('00:00:',text)
        self.run_queue(manifest,runner);self.assertEqual(len(calls),43)
    def test_same_title_separate_directories_never_overwrite(self):
        path=create_job([self.source('a/lesson.mp3'),self.source('b/lesson.wav')],self.root)
        self.assertEqual([r['title'] for r in load_job(path)['records']],['lesson','lesson (2)'])
    def test_single_language_and_original_export_only_requested_text(self):
        source=self.source('lesson.m4a')
        def runner(path,*args,**kwargs):
            self.assertIsNone(kwargs['target_language'])
            args[4](Segment(0,1,'Merhaba, hello.'),99)
        for mode,expected,calls in (
            ('tr','tr metin',[('tr',0)]),
            ('en','en metin',[('en',0)]),
            ('original','Merhaba, hello.',[]),
        ):
            with self.subTest(mode=mode):
                FakeTranslator.calls=[]
                manifest=create_job([source],self.root,mode)
                job=self.run_queue(manifest,runner)
                self.assertEqual(job['records'][0]['state'],'Tamamlandı')
                files=list(manifest.parent.glob('*.txt'))
                self.assertEqual([f.name for f in files],[f'lesson-{mode}.txt'])
                self.assertEqual(files[0].read_text(encoding='utf-8-sig').strip(),expected)
                self.assertEqual(FakeTranslator.calls,calls)
    def test_one_failure_does_not_stop_next_recording(self):
        manifest=create_job([self.source('bad.mp3'),self.source('good.mp3')],self.root)
        def runner(path,*args,**kwargs):
            if path.stem=='bad':raise ValueError('bozuk ses')
            args[4](Segment(0,1,'Hello'),99)
        job=self.run_queue(manifest,runner)
        self.assertEqual([r['state'] for r in job['records']],['Hata','Tamamlandı'])
        self.assertIn('bozuk ses',job['records'][0]['error'])
    def test_cancel_translation_resumes_without_retranscribing(self):
        manifest=create_job([self.source('lesson.mp3')],self.root);calls=[];stop=[False]
        def runner(path,*args,**kwargs):
            calls.append(path)
            for i in range(3):args[4](Segment(i,i+1,'Original'),90)
        class Interrupted(FakeTranslator):
            def translate(self,rows,target,publish,start_at=0):
                publish(replace(rows[0],text='tr metin'),90);stop[0]=True
        job=self.run_queue(manifest,runner,lambda:stop[0],Interrupted)
        self.assertEqual(job['records'][0]['state'],'Durduruldu')
        self.assertEqual(len(list(manifest.parent.glob('*.txt'))),0)
        stop[0]=False;job=self.run_queue(manifest,runner)
        self.assertEqual(len(calls),1);self.assertIn(('tr',1),FakeTranslator.calls)
        self.assertEqual(job['records'][0]['state'],'Tamamlandı')
    def test_changed_source_is_rejected_and_empty_asr_is_not_success(self):
        source=self.source('lesson.mp3');manifest=create_job([source],self.root)
        source.write_bytes(b'changed')
        job=self.run_queue(manifest,lambda *a,**k:None)
        self.assertEqual(job['records'][0]['state'],'Hata')
        manifest=create_job([source],self.root);job=self.run_queue(manifest,lambda *a,**k:None)
        self.assertEqual(job['records'][0]['state'],'Hata')
        self.assertFalse(list(manifest.parent.glob('*.txt')))


if __name__=='__main__':unittest.main()
