import copy, pathlib, tempfile, unittest, os
from project_utils import ROOT, read_json
import workflow as w
EVIDENCE=pathlib.Path(os.environ.get('TEST_EVIDENCE_DIR',str(ROOT/'evidence/tests')))

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        EVIDENCE.mkdir(parents=True,exist_ok=True)
        self.wiki,self.records=w.load_sources(ROOT); self.plan=read_json(ROOT/'slide_plan.json')
        self.slides=w.draft_slides(w.retrieve(self.wiki,self.plan))
    def test_schema_and_sources(self):
        self.assertEqual(w.validate_schema(self.wiki)['sources'],5)
        self.assertEqual(w.ingest(self.wiki,self.records)['ingested'],5)
    def test_source_missing_summary_rejected(self):
        self.records['S01']['summary']=''
        with self.assertRaises(w.ValidationError): w.ingest(self.wiki,self.records)
    def test_unknown_source_rejected(self):
        self.wiki['entries'][0]['sources']=['S99']
        with self.assertRaises(w.ValidationError): w.validate_schema(self.wiki)
    def test_source_backlinks_validated(self):
        self.wiki['sources'][0]['related']=[]
        with self.assertRaises(w.ValidationError): w.validate_schema(self.wiki)
    def test_ten_slides_all_entries_and_claims(self):
        r=w.validate_claims(self.wiki,self.slides)
        self.assertEqual(r['slides'],10); self.assertEqual(len(r['referenced_entries']),6)
    def test_missing_citation_rejected(self):
        self.slides[0]['claims'][0]['source_ids']=[]
        with self.assertRaises(w.ValidationError): w.validate_claims(self.wiki,self.slides)
    def test_drifted_claim_rejected(self):
        self.slides[1]['claims'][0]['text']='無來源的保證'
        with self.assertRaises(w.ValidationError): w.validate_claims(self.wiki,self.slides)
    def test_wiki_edit_flows_into_generated_claim(self):
        self.wiki['entries'][0]['summary']='這是測試中修改的 Wiki 摘要。'
        slides=w.draft_slides(w.retrieve(self.wiki,self.plan))
        self.assertEqual(slides[1]['claims'][0]['text'],self.wiki['entries'][0]['summary'])
        w.validate_claims(self.wiki,slides)
    def test_no_retrieval_match_rejected(self):
        with self.assertRaises(w.ValidationError): w.retrieve(self.wiki,[{'title':'x','label':'x','queries':[{'query':'unfindablexyz','fields':['summary']}]}])
    def test_citation_failure_recovers_by_retrieval(self):
        with tempfile.TemporaryDirectory() as t:
            state=w.run(out=pathlib.Path(t),fault='citation-once')
            fail=[e for e in state['events'] if e['status']=='failed']
            self.assertEqual(len(fail),1); self.assertEqual(fail[0]['retry_target'],'retrieve'); self.assertTrue(state['published'])
            path=EVIDENCE/'citation-recovery.json'
            path.write_text((pathlib.Path(t)/'execution_log.json').read_text(encoding='utf-8'),encoding='utf-8')
    def test_permanent_citation_failure_never_overwrites_release(self):
        with tempfile.TemporaryDirectory() as t:
            p=pathlib.Path(t); (p/'slides.html').write_text('existing release',encoding='utf-8')
            with self.assertRaises(w.ValidationError): w.run(out=p,fault='citation-always',max_retries=2)
            self.assertEqual((p/'slides.html').read_text(encoding='utf-8'),'existing release')
            log=read_json(p/'execution_log.json'); self.assertEqual(log['status'],'rejected'); self.assertFalse(log['published'])
            self.assertEqual(sum(e['status']=='failed' for e in log['events']),3)
            (EVIDENCE/'citation-rejected.json').write_text((p/'execution_log.json').read_text(encoding='utf-8'),encoding='utf-8')
    def test_source_failure_recovers(self):
        with tempfile.TemporaryDirectory() as t:
            state=w.run(out=pathlib.Path(t),fault='source-once')
            self.assertEqual(state['retry_counts'],{'ingest':1})
            (EVIDENCE/'source-recovery.json').write_text((pathlib.Path(t)/'execution_log.json').read_text(encoding='utf-8'),encoding='utf-8')
    def test_html_failure_rerenders_before_publish(self):
        with tempfile.TemporaryDirectory() as t:
            state=w.run(out=pathlib.Path(t),fault='html-once')
            self.assertEqual(state['retry_counts'],{'validate_html':1})
            self.assertIn('id="next"',(pathlib.Path(t)/'slides.html').read_text(encoding='utf-8'))
            (EVIDENCE/'html-recovery.json').write_text((pathlib.Path(t)/'execution_log.json').read_text(encoding='utf-8'),encoding='utf-8')
    def test_generated_local_links(self):
        self.assertEqual(w.validate_html(ROOT)['html_files'],3)
if __name__=='__main__': unittest.main(verbosity=2)
