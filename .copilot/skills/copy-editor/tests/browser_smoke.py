"""Real Chromium UI smoke test against labelled demo fixtures, not a live model.
Run: python tests/browser_smoke.py --screenshot /tmp/workshop.png
Requires playwright and a Chromium executable (test dependencies only).
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import threading

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from workshop.core import Store
from test_workshop import finding
from workshop.server import WorkshopServer, Handler
from workshop.core import Problem
from playwright.sync_api import sync_playwright, expect


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--screenshot',type=Path);parser.add_argument('--dom-bridge',action='store_true',help='Exercise the DOM without browser networking; route mocked fetch calls directly to local handlers.');parser.add_argument('--chromium',default=shutil.which('chromium') or shutil.which('google-chrome'));args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='voice-workshop-browser-test-') as tmp:
        store=Store(Path(tmp)/'db')
        server=WorkshopServer(store,0)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=args.chromium,headless=True,args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1440,'height':1000})
            errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
            page.on('dialog',lambda dialog:dialog.accept())
            def mount_dom():
                # No browser network requests, no policy changes. DOM integration only.
                import re
                markup=(ROOT/'workshop/static/index.html').read_text().replace('__TOKEN__',server.token).replace('__HTMX__','')
                markup=re.sub(r'<link[^>]*>|<script src="/static/(?:app|anchors).js" defer></script>','',markup)
                page.set_content(markup)
                page.add_style_tag(content=(ROOT/'workshop/static/styles.css').read_text())
                page.add_script_tag(content="""
                window.fetch = async function(path, opts={}) {
                  const r = await window.testBackend(String(path), opts.body || null);
                  return new Response(r.text, {status:r.status,headers:{'Content-Type':r.kind}});
                };
                """)
                page.add_script_tag(content=(ROOT/'workshop/static/anchors.js').read_text())
                page.add_script_tag(content=(ROOT/'workshop/static/app.js').read_text())
            if args.dom_bridge:
                def backend(source,path,body):
                    if not path.startswith(('/api/','/fragments/')):
                        raise RuntimeError('Only generated local app routes are allowed in this DOM harness.')
                    request=object.__new__(Handler)
                    request.server=server;request.path=path
                    request.headers={'Host':f'127.0.0.1:{server.port}'}
                    request.authorize=lambda *a,**k:None  # Authorization has its own HTTP tests.
                    captured={}
                    def capture(data,status=200,kind='application/json; charset=utf-8',extra=None):
                        captured.update(status=status,kind=kind,text=json.dumps(data) if kind.startswith('application/json') else data)
                    request.send=capture
                    try:
                        if body is None: Handler.get(request)
                        else: Handler.post(request,json.loads(body))
                    except Problem as e:capture({'error':str(e)},e.status)
                    return captured
                page.expose_binding('testBackend',backend)
                mount_dom()
            else:
                page.goto(server.origin)
            expect(page.locator('#empty-state')).to_be_visible()
            page.locator('#new-doc').click()
            page.locator('#title').fill('A quieter writing workflow')
            body=('I wanted the comments next to the words, not in another tab.\n\n'
                  '🚲 The first version kept the draft in one window and the feedback in another. '
                  'By the time I found the sentence again, I had lost track of the problem.\n\n'
                  'Now I save a snapshot, read one finding, and decide what to change. '
                  'The model does not get to write the sentence for me.')
            page.locator('#editor').fill(body)
            expect(page.locator('#save-status')).to_have_text('Saved locally',timeout=10000)
            page.locator('[aria-label="Document actions"]').click()
            page.locator('#snapshot-btn').click()
            page.locator('#snapshot-note').fill('Baseline draft')
            page.locator('#snapshot-major').check()
            page.locator('#snapshot-form button[type=submit]').click()
            expect(page.locator('#notice')).to_contain_text('saved')
            page.locator('#run-review').click()
            expect(page.locator('#external-dialog')).to_be_visible()
            ident=store.docs()[0]['id']
            assert store.jobs(ident)==[]
            page.locator('[data-close="external-dialog"]').click()
            store.import_review(store.revisions(ident)[0]['id'],page.locator('#pass').input_value(),{'scope':'DEMO FIXTURE: interface test only.','issues':[finding(paragraph=1,quote='I wanted the comments next to the words')]},'demo-fixture')
            expect(page.locator('.finding')).to_have_count(1,timeout=10000)
            page.locator('#review-mode').click()
            expect(page.locator('#annotated mark')).to_have_count(1)
            expect(page.locator('#annotated')).to_be_visible()
            expect(page.locator('#review-scope')).to_contain_text('DEMO FIXTURE')
            page.locator('.finding').click()
            expect(page.locator('#annotated mark.selected')).to_have_count(1)
            page.locator('#write-mode').click()
            revised=body+'\n\nOne window is enough.'
            page.locator('#editor').fill(revised)
            expect(page.locator('#save-status')).to_have_text('Saved locally')
            page.locator('#review-mode').click()
            expect(page.locator('#review-note')).to_contain_text('working draft differs')
            expect(page.locator('#annotated')).not_to_contain_text('One window is enough.')
            page.locator('[data-status]').select_option('declined')
            expect(page.locator('.finding')).to_have_count(0)
            page.locator('#open-only').uncheck()
            expect(page.locator('[data-status]')).to_have_value('declined')
            page.locator('#write-mode').click()
            current_text=page.locator('#editor').input_value()+'\nThe author made another revision.'
            snapshot_count=len(store.revisions(ident))
            page.locator('#editor').fill(current_text)
            page.locator('#compare-versions').click()
            expect(page.locator('#history-dialog')).to_be_visible()
            expect(page.locator('#history-heading')).to_have_text('Compare versions')
            expect(page.locator('#history-view-switch')).to_have_text('View snapshots')
            expect(page.locator('.comparison-builder')).to_have_attribute('open','')
            expect(page.locator('.history-layout')).not_to_be_visible()
            expect(page.locator('#compare-first')).to_be_focused()
            expect(page.locator('#compare-second')).to_have_value('current')
            expect(page.locator('#compare-criteria')).to_have_value('')
            expect(page.locator('#compare-context')).not_to_be_visible()
            expect(page.locator('#compare-criteria')).not_to_be_visible()
            page.locator('#comparison-context summary').click()
            expect(page.locator('#compare-context')).to_be_visible()
            expect(page.locator('#compare-criteria')).to_be_visible()
            page.locator('#comparison-context summary').click()
            expect(page.locator('#compare-criteria')).to_have_attribute('placeholder','e.g. Clarity and coherence for the stated audience')
            expect(page.locator('#compare-packet')).to_be_enabled()
            assert len(store.revisions(ident))==snapshot_count
            page.locator('#history-view-switch').click()
            expect(page.locator('#history-heading')).to_have_text('Saved snapshots')
            expect(page.locator('#history-list article')).to_have_count(len(store.revisions(ident))+1)
            reviewed_snapshot=store.reviews(ident)[0]['revision_id']
            expect(page.locator('#review-select option').first).to_contain_text(f'Review #1 ·')
            expect(page.locator('#review-select option').first).to_contain_text(f'snapshot #{reviewed_snapshot}')
            reviewed_row=page.locator('#history-list article').filter(has=page.locator(f'[data-preview="{reviewed_snapshot}"]'))
            expect(reviewed_row).to_contain_text('Pass reviewed:')
            for revision in store.revisions(ident):
                if revision['id']!=reviewed_snapshot:
                    row=page.locator('#history-list article').filter(has=page.locator(f'[data-preview="{revision["id"]}"]'))
                    expect(row).to_contain_text('No pass review')
            expect(page.locator('#revision-preview')).to_be_visible()
            expect(page.locator('#revision-preview')).to_have_text(store.one('revisions',store.revisions(ident)[0]['id'])['body'])
            expect(page.locator('.comparison-builder')).not_to_be_visible()
            expect(page.locator('#comparison-results')).not_to_be_visible()
            expect(page.locator('#history-view-switch')).to_be_focused()
            page.locator('#history-list [data-preview="current"]').click()
            expect(page.locator('#revision-preview')).to_have_text(current_text)
            page.locator('#history-view-switch').click()
            expect(page.locator('#history-heading')).to_have_text('Compare versions')
            expect(page.locator('#compare-first')).to_be_focused()
            page.locator('[data-close=history-dialog]').click()
            page.locator('[aria-label="Document actions"]').click()
            page.locator('#history-btn').click()
            expect(page.locator('#history-dialog')).to_be_visible()
            expect(page.locator('#history-heading')).to_have_text('Saved snapshots')
            expect(page.locator('#compare-first')).not_to_be_visible()
            page.locator('#history-view-switch').click()
            expect(page.locator('#history-heading')).to_have_text('Compare versions')
            expect(page.locator('#compare-run')).to_have_count(0)
            page.locator('#compare-copy-agent').click()
            expect(page.locator('#compare-copy-ready')).to_be_visible()
            handoff=page.locator('#compare-copy-text').input_value()
            assert 'Use the copy-editor skill' in handoff
            assert 'fresh, history-isolated subagent' in handoff
            assert 'Assume a fresh subagent is isolated' in handoff
            assert 'Do not stop to demand proof of isolation.' in handoff
            assert 'If fresh subagent isolation cannot be established, stop' not in handoff
            target=json.loads(handoff.split('TARGET_JSON:\n')[1].split('\n\nEVALUATOR_PACKET_JSON:')[0])
            assert target['document_id']==ident
            assert target['import_argv'][-2]==str(target['comparison_id'])
            copied_packet=json.loads(handoff.split('EVALUATOR_PACKET_JSON:\n')[1])
            assert set(copied_packet)=={'schema','prompt'}
            with page.expect_response(lambda response: response.url.endswith(f'/api/documents/{ident}/compare') and response.request.method=='POST') as repeated_copy:
                page.locator('#compare-copy-agent').click()
            assert repeated_copy.value.json()['id']==target['comparison_id']
            expect(page.locator('#compare-copy-text')).to_have_value(handoff)
            with page.expect_download() as comparison_download:page.locator('#compare-packet').click()
            comparison_path=Path(tmp)/'comparison.packet.json';comparison_download.value.save_as(comparison_path)
            comparison=json.loads(comparison_path.read_text())
            assert set(comparison)=={'schema','prompt'}
            assert comparison==copied_packet
            candidates=json.loads(comparison['prompt'].split('UNTRUSTED CANDIDATE DATA:\n')[1])
            assert current_text in (candidates['A'],candidates['B'])
            assert candidates['criteria']==''
            assert len(store.revisions(ident))==snapshot_count+1
            comparison_result=Path(tmp)/'comparison.result.json'
            comparison_result.write_text(json.dumps({'verdict':'tie','reason':'DEMO FIXTURE: interface test only.','tradeoffs':'','evidence':[]}))
            page.locator('#compare-json').set_input_files(str(comparison_result))
            expect(page.locator('.comparison-result')).to_have_count(1,timeout=10000)
            expect(page.locator('.comparison-result')).to_contain_text('DEMO FIXTURE')
            expect(page.locator('.comparison-result')).to_contain_text('No material difference found')
            expect(page.locator('.comparison-result')).to_contain_text('A = #')
            expect(page.locator('.comparison-result blockquote')).to_have_count(0)
            page.locator('.comparison-result summary').click()
            expect(page.locator('.comparison-result')).to_contain_text('Evaluator:')
            compared=store.comparisons(ident)[0]
            page.locator('#history-view-switch').click()
            for revision_id,other_id in [(compared['a_revision'],compared['b_revision']),(compared['b_revision'],compared['a_revision'])]:
                row=page.locator('#history-list article').filter(has=page.locator(f'[data-preview="{revision_id}"]'))
                expect(row).to_contain_text(f'Compared with #{other_id} in A/B #{compared["id"]}')
            page.locator('[data-close=history-dialog]').click()
            # Export is browser-mediated, never an overwrite of the imported source.
            page.locator('[aria-label="Document actions"]').click()
            with page.expect_download() as info:page.locator('#export-btn').click()
            saved=Path(tmp)/'export.md';info.value.save_as(saved)
            assert saved.read_text()==revised
            # Reload exercises persistence; content must survive and demo reviews remain attached.
            page.reload()
            if args.dom_bridge:mount_dom()
            expect(page.locator('#editor')).to_have_value(revised)
            page.locator('#open-only').uncheck()
            page.locator('#review-mode').click()
            expect(page.locator('#annotated mark')).to_have_count(1)
            expect(page.locator('#annotated')).to_be_visible()
            # New review after an existing one covers the fast-completion polling race.
            page.locator('#write-mode').click()
            revision=store.snapshot(ident,'Repeated external fixture')
            store.import_review(revision['id'],page.locator('#pass').input_value(),{'scope':'DEMO FIXTURE: interface test only.','issues':[finding(paragraph=1,quote='I wanted the comments next to the words')]},'demo-fixture')
            expect(page.locator('#review-select option')).to_have_count(2,timeout=10000)
            expect(page.locator('[data-status]')).to_have_value('open',timeout=10000)
            page.locator('#review-mode').click()
            if args.screenshot:
                args.screenshot.parent.mkdir(parents=True,exist_ok=True)
                page.screenshot(path=str(args.screenshot),full_page=True)
            # Verify the single-column responsive layout does not horizontally overflow.
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
            assert not errors,errors
            print(('DOM-BRIDGE (not browser HTTP): ' if args.dom_bridge else 'DIRECT HTTP: ')+'PASS: create, autosave, major snapshot, demo pass, exact highlight, stale-snapshot warning, decline, history, randomized comparison, export, reload, repeat review, mobile layout; zero page errors.')
            browser.close()
        server.shutdown();server.server_close();thread.join()

if __name__=='__main__':main()
