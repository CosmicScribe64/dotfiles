"""External-run receipts, exact snapshot routing, idempotency, HTTP and CLI exchange.
All results below are synthetic test fixtures, not model evaluations.
"""
from __future__ import annotations
import concurrent.futures
import contextlib
import copy
from http.cookiejar import CookieJar
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from urllib import request as http, error as http_error

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from workshop.core import Store, Problem
from workshop.server import WorkshopServer
from workshop.catalog import BY_ID
from workshop import exchange as x

BODY='👩🏽‍💻 I really wanted the comments beside the words.\n\nI really kept the original draft.'
PASS='sand-filler-words'
EMPTY={'scope':'TEST FIXTURE — zero findings for transport testing, not a real review.','issues':[]}
ISSUE={'paragraph':1,'quote':'really','occurrence':1,'priority':'low','category':'Test fixture',
       'problem':'Synthetic finding for integration testing.', 'reader_effect':'No model evaluation was performed.',
       'revision_task':'Test the controls, not the prose.','tradeoff':'','confidence':'low'}

class ExchangeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.home=Path(self.tmp.name);self.s=Store(self.home/'db')
        self.d=self.s.create('Author document',BODY);self.r=self.s.revisions(self.d['id'])[0]['id']
        self.packet=x.export_packet(self.s,self.r,PASS)
    def tearDown(self):self.tmp.cleanup()
    def envelope(self,issues=None):
        return x.wrap_result(self.packet,dict(EMPTY,issues=issues or []),'test-agent (fixture)')
    def test_export_is_pending_not_completed_and_has_complete_instructions(self):
        self.assertEqual(self.s.pass_progress(self.d['id'])['summary']['current'],0)
        self.assertEqual(len(x.requests(self.s,self.d['id'])),1)
        self.assertEqual(x.get_packet(self.s,self.packet['request']['id']),self.packet)
        self.assertIn('external-result envelope',self.packet['prompt'])
        self.assertIn('Do not report off-pass problems',self.packet['prompt'])
        self.assertIn('UNTRUSTED DRAFT DATA',self.packet['prompt'])
    def test_result_routes_to_same_reviews_and_completes_exact_pass(self):
        v=x.import_result(self.s,self.envelope([ISSUE]))['review']
        self.assertEqual(v['revision_id'],self.r);self.assertEqual(v['pass_name'],PASS)
        self.assertEqual(v['issues'][0]['quote'],'really')
        self.assertEqual(self.s.pass_progress(self.d['id'])['summary']['current'],1)
        self.assertEqual(self.s.one('documents',self.d['id'])['body'],BODY)
        self.assertIn('self-reported',v['provider'])
    def test_preview_does_not_import(self):
        p=x.preview_result(self.s,self.envelope([ISSUE]))
        self.assertTrue(p['same_working_input']);self.assertEqual(p['issue_count'],1)
        self.assertEqual(len(self.s.reviews(self.d['id'])),0)
    def test_zero_findings_complete_a_pass(self):
        x.import_result(self.s,self.envelope())
        self.assertEqual(self.s.pass_progress(self.d['id'])['summary']['current'],1)
    def test_changed_working_draft_keeps_old_review_without_current_check(self):
        self.s.save(self.d['id'],dict(self.d,body=BODY+' Author change.'))
        self.assertFalse(x.preview_result(self.s,self.envelope())['same_working_input'])
        v=x.import_result(self.s,self.envelope([ISSUE]))['review']
        self.assertEqual(v['revision']['body'],BODY)
        self.assertEqual(self.s.pass_progress(self.d['id'])['summary']['current'],0)
        self.assertEqual(self.s.pass_progress(self.d['id'],self.r)['summary']['current'],1)
    def test_changed_context_is_stale_but_title_is_not(self):
        self.s.save(self.d['id'],dict(self.d,title='Renamed'))
        self.assertTrue(x.preview_result(self.s,self.envelope())['same_working_input'])
        d=self.s.one('documents',self.d['id']);self.s.save(d['id'],dict(d,audience='New audience'))
        self.assertFalse(x.preview_result(self.s,self.envelope())['same_working_input'])
    def test_metadata_changes_all_rejected(self):
        for key in self.packet['request']:
            e=self.envelope();e['request']=dict(e['request'])
            e['request'][key]=999 if key.endswith('_id') else 'tampered'
            with self.subTest(key=key),self.assertRaises(Problem):x.import_result(self.s,e)
        self.assertEqual(self.s.reviews(self.d['id']),[])
    def test_other_database_with_same_integer_ids_cannot_import(self):
        other=Store(self.home/'other');other.create('Different document',BODY)
        with self.assertRaisesRegex(Problem,'originating data directory'):x.import_result(other,self.envelope())
        self.assertEqual(other.reviews(1),[])
    def test_invalid_evidence_atomic_no_partial_receipt_or_findings(self):
        with self.assertRaises(Problem):x.import_result(self.s,self.envelope([ISSUE,dict(ISSUE,quote='not in draft')]))
        self.assertEqual(self.s.reviews(self.d['id']),[])
        self.assertIsNone(x.requests(self.s,self.d['id'])[0]['review_id'])
    def test_unfilled_template_does_not_count_as_zero_issue_review(self):
        with self.assertRaises(Problem):x.import_result(self.s,self.packet['reply_template'])
        self.assertEqual(self.s.reviews(self.d['id']),[])
    def test_schema_rejects_rewrites_extra_fields_and_bad_types(self):
        for bad in [dict(ISSUE,replacement='rewritten'),dict(ISSUE,paragraph=True)]:
            with self.assertRaises(Problem):x.wrap_result(self.packet,dict(EMPTY,issues=[bad]),'test')
        e=self.envelope();e['rewritten_draft']='not allowed'
        with self.assertRaises(Problem):x.import_result(self.s,e)
    def test_repeated_import_preserves_status_and_ids(self):
        e=self.envelope([ISSUE]);a=x.import_result(self.s,e)
        self.s.issue_status(a['review']['issues'][0]['id'],'declined')
        b=x.import_result(self.s,copy.deepcopy(e))
        self.assertTrue(b['already_imported']);self.assertEqual(a['review']['id'],b['review']['id'])
        self.assertEqual(b['review']['issues'][0]['status'],'declined')
        self.assertEqual(len(self.s.reviews(self.d['id'])),1)
    def test_different_second_result_cannot_replace_old(self):
        x.import_result(self.s,self.envelope())
        with self.assertRaisesRegex(Problem,'different result'):x.import_result(self.s,self.envelope([ISSUE]))
        self.assertEqual(len(self.s.reviews(self.d['id'])),1)
    def test_concurrent_import_is_idempotent(self):
        e=self.envelope([ISSUE])
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            results=list(pool.map(lambda _:x.import_result(self.s,e),range(3)))
        self.assertEqual(len({r['review']['id'] for r in results}),1)
        self.assertEqual(sum(not r['already_imported'] for r in results),1)
    def test_stale_pass_version_rejected_without_mutation(self):
        old=BY_ID[PASS]['version']
        try:
            BY_ID[PASS]['version']='changed'
            with self.assertRaisesRegex(Problem,'instructions changed'):x.import_result(self.s,self.envelope())
        finally:BY_ID[PASS]['version']=old
        self.assertEqual(self.s.reviews(self.d['id']),[])
    def test_tampered_stored_snapshot_rejected(self):
        with self.s.db() as c:c.execute('UPDATE revisions SET body=? WHERE id=?',('Changed behind app',self.r))
        with self.assertRaisesRegex(Problem,'stored snapshot'):x.import_result(self.s,self.envelope())
    def test_oversize_or_missing_provider_rejected(self):
        for provider in ['', 'x'*151, x.PROVIDER_PLACEHOLDER]:
            with self.assertRaises(Problem):x.wrap_result(self.packet,EMPTY,provider)
    def test_broad_pass_import_does_not_tick_narrow_checks(self):
        p=x.export_packet(self.s,self.r,'clarity');e=x.wrap_result(p,EMPTY,'test-agent')
        x.import_result(self.s,e)
        self.assertEqual(self.s.pass_progress(self.d['id'])['summary']['current'],0)
    def test_saved_request_survives_restart(self):
        other=Store(self.home/'db');self.assertEqual(x.get_packet(other,self.packet['request']['id']),self.packet)
        x.import_result(other,self.envelope());self.assertEqual(len(self.s.reviews(self.d['id'])),1)
    def test_v3_migration_backs_up_before_adding_exchange_table(self):
        # Simulate the v3 schema; preserve all existing drafts/reviews.
        with self.s.db() as c:
            c.execute('DROP TABLE external_requests');c.execute('PRAGMA user_version=2')
        upgraded=Store(self.home/'db')
        self.assertEqual(upgraded.one('documents',self.d['id'])['body'],BODY)
        backups=list((self.home/'db').glob('workshop-before-v4-*.sqlite3'));self.assertEqual(len(backups),1)
        with contextlib.closing(sqlite3.connect(backups[0])) as c:
            self.assertEqual(c.execute('PRAGMA user_version').fetchone()[0],2)
            self.assertFalse(c.execute("SELECT name FROM sqlite_master WHERE name='external_requests'").fetchone())
        Store(self.home/'db');self.assertEqual(len(list((self.home/'db').glob('workshop-before-v4-*'))),1)
    def test_cli_full_round_trip_and_offline_wrapper_no_db(self):
        cli=[sys.executable,str(ROOT/'scripts/workshop.py')]
        def run(args):
            return subprocess.run(cli+args,check=True,capture_output=True,text=True).stdout
        packet_path=self.home/'packet.json'
        run(['--data-dir',str(self.s.home),'external-packet',str(self.d['id']),'--pass',PASS,'--out',str(packet_path)])
        inner=self.home/'findings.json';inner.write_text(json.dumps(dict(EMPTY,issues=[ISSUE])))
        offline_home=self.home/'should-not-exist';output=self.home/'returned.review.json'
        run(['--data-dir',str(offline_home),'wrap-result',str(packet_path),str(inner),'--provider','test-agent','--out',str(output)])
        self.assertFalse(offline_home.exists())
        preview=json.loads(run(['--data-dir',str(self.s.home),'import-result',str(output),'--check']))
        self.assertEqual(preview['pass_name'],PASS);self.assertEqual(len(self.s.reviews(self.d['id'])),0)
        result=json.loads(run(['--data-dir',str(self.s.home),'import-result',str(output)]))
        self.assertFalse(result['already_imported'])
        self.assertEqual(result['review']['issues'][0]['quote'],'really')

class ExchangeHTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.s=Store(Path(self.tmp.name));self.d=self.s.create('HTTP fixture',BODY)
        self.server=WorkshopServer(self.s,0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.opener=http.build_opener(http.HTTPCookieProcessor(CookieJar()))
        self.opener.open(self.server.origin).read()
    def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.tmp.cleanup()
    def call(self,path,data=None,token=True):
        headers={'Content-Type':'application/json'}
        if token:headers['X-Workshop-Token']=self.server.token
        req=http.Request(self.server.origin+path,data=None if data is None else json.dumps(data).encode(),headers=headers)
        return json.loads(self.opener.open(req).read())
    def test_http_export_preview_import_and_progress(self):
        p=self.call(f'/api/documents/{self.d["id"]}/external-packet',{'pass_name':PASS})
        self.assertEqual(self.call('/api/external-packets/'+p['request']['id']),p)
        e=x.wrap_result(p,dict(EMPTY,issues=[ISSUE]),'http-fixture')
        target=self.call('/api/external-results/preview',e);self.assertEqual(target['issue_count'],1)
        v=self.call('/api/external-results/import',e)['review'];self.assertEqual(v['pass_name'],PASS)
        d=self.call('/api/documents/'+str(self.d['id']))
        self.assertEqual(d['pass_progress']['summary']['current'],1)
        self.assertEqual(d['external_requests'][0]['review_id'],v['id'])
        self.assertFalse(d['jobs'])
    def test_external_routes_require_mutation_token(self):
        with self.assertRaises(http_error.HTTPError) as e:
            self.call(f'/api/documents/{self.d["id"]}/external-packet',{'pass_name':PASS},token=False)
        self.assertEqual(e.exception.code,403)
    def test_http_rejects_unknown_receipt_without_guessing(self):
        p=x.export_packet(self.s,self.s.revisions(self.d['id'])[0]['id'],PASS)
        e=x.wrap_result(p,EMPTY,'fixture');e['request']['id']='other-request'
        with self.assertRaises(http_error.HTTPError) as error:self.call('/api/external-results/import',e)
        self.assertEqual(error.exception.code,404)
    def test_http_rejects_cross_document_snapshot(self):
        other=self.s.create('Other',BODY);rid=self.s.revisions(other['id'])[0]['id']
        with self.assertRaises(http_error.HTTPError):
            self.call(f'/api/documents/{self.d["id"]}/external-packet',{'revision_id':rid,'pass_name':PASS})

if __name__=='__main__':unittest.main()
