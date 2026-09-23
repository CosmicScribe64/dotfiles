"""v3 catalog, revision-aware progress, migration and API regression tests.
All model results here are deterministic fixtures, not live evaluations.
"""
from __future__ import annotations
import contextlib
import http.cookiejar
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from workshop.catalog import CATALOG, BY_ID, CHECKLIST_NAMES, PASS_NAMES
from workshop.core import Store, Problem
from workshop.server import WorkshopServer

BODY='The robot is really ready.\n\nThe operator checked the route.'
PASS='sand-filler-words'
EMPTY={'scope':'Test fixture: no live model evaluation.','issues':[]}
def issue():
    return {'paragraph':1,'quote':'really','occurrence':1,'priority':'low','category':'Fixture',
      'problem':'Test fixture.','reader_effect':'Not an evaluation.','revision_task':'Test the interface only.',
      'tradeoff':'','confidence':'low'}

class ProgressTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.home=Path(self.tmp.name);self.s=Store(self.home)
        self.d=self.s.create('Fixture draft',BODY,'Engineers','Explain a workflow')
        self.r=self.s.revisions(self.d['id'])[0]['id']
    def tearDown(self):self.tmp.cleanup()
    def progress(self,rid=None):return self.s.pass_progress(self.d['id'],rid)
    def item(self,name=PASS,rid=None):return next(x for x in self.progress(rid)['items'] if x['id']==name)
    def import_pass(self,name=PASS,issues=None,rid=None,provider='test-fixture'):
        return self.s.import_review(rid or self.r,name,{'scope':'Fixture only.','issues':issues or []},provider)
    def save(self,**kw):
        d=self.s.one('documents',self.d['id']);return self.s.save(d['id'],dict(d,**kw))
    def test_catalog_has_30_individual_and_seven_compatible_broad_modes(self):
        self.assertEqual(len(CHECKLIST_NAMES),30);self.assertEqual(len(PASS_NAMES),37)
        self.assertEqual(set(PASS_NAMES)-set(CHECKLIST_NAMES),{'triage','structure','clarity','economy','diction','mechanics','full'})
        self.assertEqual(len(set(p['version'] for p in CATALOG)),37)
    def test_every_pass_has_distinct_focus_and_explicit_exceptions(self):
        self.assertEqual(len({p['focus'] for p in CATALOG}),37)
        for p in CATALOG:
            packet=self.s.review_packet(self.r,p['id'])
            self.assertIn(p['focus'],packet['prompt']);self.assertIn(p['exceptions'],packet['prompt'])
            self.assertIn('Do not praise',packet['prompt']);self.assertIn('replacement',packet['prompt'])
            self.assertEqual(packet['pass_version'],p['version'])
            if p['checklist']:self.assertIn('Do not report off-pass problems',packet['prompt'])
    def test_readable_catalog_matches_runtime_instructions(self):
        reference=(ROOT/'references/pass-catalog.md').read_text(encoding='utf-8')
        for entry in CATALOG:
            with self.subTest(pass_name=entry['id']):
                marker=f"**ID:** `{entry['id']}`"
                self.assertEqual(reference.count(marker),1)
                section=reference.split(marker,1)[1].split('\n### ',1)[0]
                self.assertIn(entry['summary'],section)
                self.assertIn('**Focus:** '+entry['focus'],section)
                self.assertIn('**Exceptions:** '+entry['exceptions'],section)
                self.assertIn('**Author task:** '+entry['task'],section)
    def test_new_draft_has_no_completed_checks(self):
        p=self.progress();self.assertEqual(p['summary']['current'],0);self.assertEqual(p['summary']['total'],30)
        self.assertTrue(all(x['status']=='not-run' for x in p['items']))
    def test_zero_findings_still_counts_as_a_run(self):
        self.import_pass();self.assertEqual(self.item()['status'],'current')
        self.assertEqual(self.item()['counts']['total'],0);self.assertEqual(self.progress()['summary']['current'],1)
    def test_broad_reviews_do_not_fill_individual_checks(self):
        for name in ['full','clarity','mechanics']:self.import_pass(name)
        self.assertEqual(self.progress()['summary']['current'],0);self.assertTrue(self.item('full')['current'])
    def test_status_counts_are_independent_of_pass_completion(self):
        v=self.import_pass(issues=[issue(),issue(),issue(),issue()])
        for finding,status in zip(v['issues'],['open','resolved','declined','superseded']):self.s.issue_status(finding['id'],status)
        self.assertEqual(self.item()['counts'],{'total':4,'open':1,'resolved':1,'declined':1,'superseded':1})
        self.assertTrue(self.item()['current']);self.assertEqual(self.s.one('documents',self.d['id'])['body'],BODY)
    def test_latest_matching_review_counts_replace_not_accumulate(self):
        self.import_pass(issues=[issue()]);last=self.import_pass()
        self.assertEqual(self.item()['review_id'],last['id']);self.assertEqual(self.item()['counts']['total'],0)
        self.assertEqual(self.item()['run_count'],2)
    def test_body_change_invalidates_checks_but_preserves_history(self):
        v=self.import_pass(issues=[issue()]);self.save(body=BODY+'\n\nLater.')
        self.assertEqual(self.item()['status'],'needs-rerun');self.assertEqual(self.item()['counts']['open'],1)
        self.assertEqual(self.s.review(v['id'])['revision']['body'],BODY)
        self.assertEqual(self.progress()['summary']['current'],0)
    def test_audience_and_purpose_changes_invalidate(self):
        self.import_pass()
        for key in ['audience','purpose']:
            original=self.s.one('documents',self.d['id'])[key];self.save(**{key:'Different context'})
            self.assertFalse(self.item()['current']);self.save(**{key:original});self.assertTrue(self.item()['current'])
    def test_title_and_snapshot_notes_do_not_invalidate(self):
        self.import_pass();self.save(title='A different title')
        r=self.s.snapshot(self.d['id'],'Major milestone',True)
        self.assertTrue(self.item()['current']);self.assertTrue(self.item(rid=r['id'])['current'])
    def test_restoring_exact_text_restores_its_check(self):
        self.import_pass();d=self.save(body='Different')
        self.s.restore(self.d['id'],self.r,d['version'])
        self.assertTrue(self.item()['current']);self.assertEqual(len(self.s.reviews(self.d['id'])),1)
    def test_new_snapshot_with_same_input_shares_progress(self):
        self.import_pass();r=self.s.snapshot(self.d['id'])
        self.assertTrue(self.item(rid=r['id'])['current'])
    def test_each_snapshot_reports_its_own_matching_input(self):
        self.import_pass();self.save(body='A different draft.')
        new=self.s.snapshot(self.d['id']);self.import_pass('find-real-actors',rid=new['id'])
        self.assertTrue(self.item(PASS,self.r)['current']);self.assertFalse(self.item(PASS,new['id'])['current'])
        self.assertFalse(self.item('find-real-actors',self.r)['current']);self.assertTrue(self.item('find-real-actors',new['id'])['current'])
    def test_rerun_earlier_input_does_not_mark_new_draft_current(self):
        self.save(body='Changed');self.import_pass(rid=self.r)
        self.assertFalse(self.item()['current'])
    def test_progress_does_not_leak_other_documents(self):
        other=self.s.create('Other',BODY,'Engineers','Explain a workflow')
        rid=self.s.revisions(other['id'])[0]['id'];self.s.import_review(rid,PASS,EMPTY)
        self.assertEqual(self.item()['run_count'],0)
        with self.assertRaises(Problem):self.s.pass_progress(self.d['id'],rid)
    def test_demo_is_visible_but_not_a_completed_check(self):
        self.import_pass(provider='demo-fixture')
        self.assertEqual(self.item()['status'],'demo');self.assertEqual(self.progress()['summary']['current'],0)
        self.assertEqual(self.progress()['summary']['demo'],1)
    def test_legacy_jobs_have_no_new_writer(self):
        self.assertFalse(hasattr(self.s,'new_job'))
        self.assertFalse(hasattr(self.s,'job_update'))
        self.assertEqual(self.s.jobs(self.d['id']),[])
    def test_changed_prompt_invalidates_saved_pass(self):
        v=self.import_pass()
        with self.s.db() as c:c.execute("UPDATE reviews SET pass_version='old-prompt' WHERE id=?",(v['id'],))
        self.assertFalse(self.item()['current']);self.assertEqual(self.item()['reason'],'pass-changed')
    def test_import_of_old_packet_version_is_rejected_atomically(self):
        with self.assertRaisesRegex(Problem,'instructions changed'):
            self.s.import_review(self.r,PASS,EMPTY,expected_pass_version='old-prompt')
        self.assertEqual(self.s.reviews(self.d['id']),[])
    def test_cli_catalog_progress_and_targeted_packet(self):
        command=[sys.executable,str(ROOT/'scripts/workshop.py'),'--data-dir',str(self.home)]
        catalog=json.loads(subprocess.check_output(command+['passes'],text=True));self.assertEqual(len(catalog),37)
        self.import_pass()
        progress=json.loads(subprocess.check_output(command+['progress',str(self.d['id'])],text=True))
        self.assertEqual(progress['summary']['current'],1)
        packet=json.loads(subprocess.check_output(command+['review-packet',str(self.r),'--pass',PASS],text=True))
        self.assertEqual(packet['pass_name'],PASS);self.assertIn('pass_version',packet)
    def test_additive_migration_preserves_v2_data_and_makes_backup(self):
        self.import_pass('clarity',issues=[issue()])
        # Recreate exactly the old review table; IDs and child issue rows stay intact.
        with contextlib.closing(sqlite3.connect(self.s.path)) as c:
            c.execute('PRAGMA foreign_keys=OFF')
            c.executescript('''CREATE TABLE old_reviews (id INTEGER PRIMARY KEY,revision_id INTEGER NOT NULL,
              pass_name TEXT NOT NULL,provider TEXT NOT NULL,scope TEXT NOT NULL,created TEXT NOT NULL);
              INSERT INTO old_reviews SELECT id,revision_id,pass_name,provider,scope,created FROM reviews;
              DROP TABLE reviews; ALTER TABLE old_reviews RENAME TO reviews; PRAGMA user_version=1;''')
        upgraded=Store(self.home)
        self.assertEqual(upgraded.one('documents',self.d['id'])['body'],BODY)
        self.assertEqual(upgraded.review(1)['issues'][0]['quote'],'really')
        self.assertEqual(upgraded.review(1)['pass_version'],'legacy-v2')
        self.assertEqual(upgraded.pass_progress(self.d['id'])['summary']['current'],0)
        backups=list(self.home.glob('workshop-before-v3-*.sqlite3'));self.assertEqual(len(backups),1)
        with contextlib.closing(sqlite3.connect(backups[0])) as c:
            self.assertNotIn('pass_version',[x[1] for x in c.execute('PRAGMA table_info(reviews)')])
        Store(self.home);self.assertEqual(len(list(self.home.glob('workshop-before-v3-*.sqlite3'))),1)
    def test_newer_database_version_is_not_silently_downgraded(self):
        with self.s.db() as c:c.execute('PRAGMA user_version=99')
        with self.assertRaisesRegex(Problem,'newer workbench'):Store(self.home)

class PassApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.s=Store(Path(self.tmp.name))
        self.server=WorkshopServer(self.s,0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.client.open(self.server.origin).read()
        self.d=self.s.create('Fixture',BODY);self.r=self.s.revisions(self.d['id'])[0]['id']
    def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.tmp.cleanup()
    def request(self,path,payload=None):
        req=urllib.request.Request(self.server.origin+path,data=json.dumps(payload).encode() if payload is not None else None,
            headers={'Content-Type':'application/json','X-Workshop-Token':self.server.token})
        return json.load(self.client.open(req))
    def test_state_serves_catalog_from_single_source(self):
        data=self.request('/api/state');self.assertEqual(len(data['catalog']),37);self.assertEqual(data['catalog_version'],'3.0.0')
    def test_progress_endpoint_and_zero_finding_import(self):
        self.request(f'/api/revisions/{self.r}/import-review',{'pass_name':PASS,'pass_version':BY_ID[PASS]['version'],'result':EMPTY,'provider':'test-fixture'})
        p=self.request(f'/api/documents/{self.d["id"]}/passes');self.assertEqual(p['summary']['current'],1)
        doc=self.request(f'/api/documents/{self.d["id"]}');self.assertEqual(doc['pass_progress']['summary']['current'],1)
    def test_snapshot_progress_route_validates_ownership(self):
        other=self.s.create('Other','Different');rid=self.s.revisions(other['id'])[0]['id']
        with self.assertRaises(urllib.error.HTTPError) as error:self.request(f'/api/documents/{self.d["id"]}/passes?revision={rid}')
        self.assertEqual(error.exception.code,400)
    def test_api_rejects_outdated_packet_version(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request(f'/api/revisions/{self.r}/import-review',{'pass_name':PASS,'pass_version':'stale','result':EMPTY})
        self.assertEqual(error.exception.code,409)
    def test_catalog_and_anchor_assets_have_no_external_requests(self):
        req=urllib.request.Request(self.server.origin+'/static/anchors.js')
        data=self.client.open(req).read().decode();self.assertIn('Never fuzzy-match',data)
        self.assertNotIn('fetch(',data)

if __name__=='__main__':unittest.main()
