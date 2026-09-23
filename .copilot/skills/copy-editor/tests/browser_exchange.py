"""Chromium external-review round trip; labelled fixtures only, no live models.
Use --dom-bridge when browser networking is restricted. This never changes policy.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from workshop.core import Store,Problem
from workshop.server import WorkshopServer,Handler
from workshop import exchange as x
from test_exchange import BODY,PASS,ISSUE,EMPTY


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--dom-bridge',action='store_true')
    parser.add_argument('--chromium',default=shutil.which('chromium'))
    parser.add_argument('--screenshot',type=Path)
    args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='workshop-v4-exchange-') as tmp:
        home=Path(tmp);store=Store(home/'db')
        d=store.create('External review — interface fixture',BODY)
        server=WorkshopServer(store,0)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with sync_playwright() as pw:
                browser=pw.chromium.launch(executable_path=args.chromium,headless=True,args=['--no-sandbox'])
                page=browser.new_page(viewport={'width':1440,'height':1100})
                errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:d.accept())
                if args.dom_bridge:
                    def backend(source,path,body):
                        if not path.startswith(('/api/','/fragments/')):raise RuntimeError('Only local generated-app routes allowed')
                        request=object.__new__(Handler);request.server=server;request.path=path
                        request.headers={'Host':f'127.0.0.1:{server.port}'};request.authorize=lambda *a,**k:None
                        captured={}
                        def capture(data,status=200,kind='application/json; charset=utf-8',extra=None):
                            captured.update(text=json.dumps(data) if kind.startswith('application/json') else data,status=status,kind=kind)
                        request.send=capture
                        try:
                            if body is None:Handler.get(request)
                            else:Handler.post(request,json.loads(body))
                        except Problem as e:capture({'error':str(e)},e.status)
                        return captured
                    page.expose_binding('testBackend',backend)
                    markup=(ROOT/'workshop/static/index.html').read_text().replace('__TOKEN__',server.token).replace('__HTMX__','')
                    markup=re.sub(r'<link[^>]*>|<script src="/static/(?:app|anchors).js" defer></script>','',markup)
                    page.set_content(markup);page.add_style_tag(content=(ROOT/'workshop/static/styles.css').read_text())
                    page.add_script_tag(content='''window.fetch=async function(path,opts={}) {
                        const r=await window.testBackend(String(path),opts.body||null);
                        return new Response(r.text,{status:r.status,headers:{'Content-Type':r.kind}});
                    };''')
                    for name in ['anchors.js','app.js']:page.add_script_tag(content=(ROOT/'workshop/static'/name).read_text())
                else:page.goto(server.origin)
                expect(page.locator('#editor')).to_have_value(BODY)
                page.locator('#pass').select_option(PASS)
                page.locator('[aria-label="Review actions"]').click()
                expect(page.locator('#external-btn')).to_have_count(0)
                expect(page.locator('#external-import-open')).to_be_visible()
                page.locator('#run-review').click()
                expect(page.locator('#external-dialog')).to_be_visible()
                expect(page.locator('#external-heading')).to_have_text('Review externally')
                if not args.dom_bridge:page.context.grant_permissions(['clipboard-read','clipboard-write'],origin=server.origin)
                page.locator('#external-copy-agent').click()
                expect(page.locator('#external-copy-ready')).to_be_visible()
                expect(page.locator('#external-copy-agent')).to_be_enabled()
                local_prompt=page.locator('#external-copy-text').input_value()
                target=json.loads(local_prompt.split('TARGET_JSON:\n',1)[1])
                assert target['skill_file']==str(ROOT/'SKILL.md')
                assert target['data_dir']==str(store.home)
                assert target['document_id']==d['id'] and target['pass_name']==PASS
                assert store.one('revisions',target['revision_id'])['body']==BODY
                assert BODY not in local_prompt and server.token not in local_prompt
                assert 'Do not ask me to download, upload, or paste files' in local_prompt
                if not args.dom_bridge:
                    expect(page.locator('#external-status')).to_contain_text('Agent prompt copied')
                    assert page.evaluate('navigator.clipboard.readText()')==local_prompt
                exported=json.loads(subprocess.check_output(target['export_argv'],text=True))
                assert exported['request']['revision_id']==target['revision_id']
                assert exported['request']['pass_version']==target['pass_version']
                assert store.jobs(d['id'])==[] and store.reviews(d['id'])==[]
                page.locator('[data-close="external-dialog"]').click()
                page.locator('#run-review').click()
                expect(page.locator('#external-dialog')).to_be_visible()
                page.locator('#external-snapshot').select_option(str(target['revision_id']))
                expect(page.locator('#external-copy-ready')).to_be_hidden()
                page.locator('#external-copy-packet').click()
                expect(page.locator('#external-copy-ready')).to_be_visible()
                expect(page.locator('#external-copy-packet')).to_be_enabled()
                copied=json.loads(page.locator('#external-copy-text').input_value())
                assert copied['request']['revision_id']==target['revision_id']
                assert x.get_packet(store,copied['request']['id'])==copied
                assert server.token not in json.dumps(copied)
                if not args.dom_bridge:
                    expect(page.locator('#external-status')).to_contain_text('Packet copied')
                    assert json.loads(page.evaluate('navigator.clipboard.readText()'))==copied
                    page.evaluate("Object.defineProperty(navigator.clipboard,'writeText',{configurable:true,value:async()=>{throw new DOMException('Denied','NotAllowedError')}})")
                    page.locator('#external-copy-agent').click()
                    expect(page.locator('#external-status')).to_contain_text('Clipboard unavailable')
                    fallback=page.locator('#external-copy-text')
                    assert fallback.evaluate('(element)=>element.value.slice(element.selectionStart,element.selectionEnd)')==fallback.input_value()
                    page.evaluate('delete navigator.clipboard.writeText')
                assert store.pass_progress(d['id'])['summary']['current']==0
                page.locator('#external-snapshot').select_option('')
                with page.expect_download() as download:page.locator('#external-export').click()
                packet_path=home/'first.packet.json';download.value.save_as(packet_path)
                packet=json.loads(packet_path.read_text());assert packet['request']['pass_name']==PASS
                expect(page.locator('#external-request-list')).to_contain_text('Awaiting result')
                expect(page.locator('#external-chat-instruction')).to_have_value(x.CHAT_INSTRUCTION)
                assert store.pass_progress(d['id'])['summary']['current']==0
                assert store.jobs(d['id'])==[]
                if args.screenshot:
                    args.screenshot.parent.mkdir(parents=True,exist_ok=True)
                    page.locator('#external-dialog').evaluate('(el)=>el.scrollTop=0')
                    page.screenshot(path=str(args.screenshot),full_page=False)
                page.locator('[data-close="external-dialog"]').click()
                # Selecting another pass must not accidentally route the returned findings there.
                page.locator('#pass').select_option('find-real-actors')
                page.locator('[aria-label="Review actions"]').click()
                page.locator('#external-import-open').click()
                page.locator('#external-paste-details summary').click()
                page.locator('#external-result-text').fill('{"scope":"bare result","issues":[]}')
                page.locator('#external-preview-text').click()
                expect(page.locator('#external-status')).to_contain_text('complete result envelope')
                expect(page.locator('#external-confirm-import')).to_be_hidden()
                envelope=x.wrap_result(packet,dict(EMPTY,issues=[ISSUE]),'UI test fixture — not a live review')
                page.locator('#external-result-text').fill('```json\n'+json.dumps(envelope)+'\n```')
                page.locator('#external-preview-text').click()
                expect(page.locator('#external-preview')).to_contain_text('Sand off filler words')
                assert store.reviews(d['id'])==[]
                page.locator('#external-confirm-import').click()
                expect(page.locator('#external-dialog')).not_to_be_visible()
                expect(page.locator('#pass')).to_have_value(PASS)
                expect(page.locator('#findings .finding')).to_have_count(1)
                expect(page.locator('#draft-highlights')).to_be_visible()
                expect(page.locator('#pass-progress')).to_have_text('1 / 30 run')
                expect(page.locator('#review-provider')).to_contain_text('self-reported')
                assert page.locator('#editor').input_value()==BODY
                # Reimport must preserve the author's declined status and avoid duplicates.
                page.locator('[data-status]').select_option('declined')
                result_path=home/'result.review.json';result_path.write_text(json.dumps(envelope))
                page.locator('[aria-label="Review actions"]').click()
                page.locator('#external-import-open').click()
                expect(page.locator('#external-dialog')).to_be_visible()
                page.locator('#external-result-file').set_input_files(str(result_path))
                expect(page.locator('#external-preview')).to_contain_text('Already imported')
                page.locator('#external-confirm-import').click()
                expect(page.locator('#notice')).to_contain_text('Opened existing')
                assert len(store.reviews(d['id']))==1
                assert store.review(store.reviews(d['id'])[0]['id'])['issues'][0]['status']=='declined'
                # Changed text remains the author's text. Feedback binds to the old snapshot.
                page.locator('#pass').select_option('find-real-actors')
                page.locator('#run-review').click()
                with page.expect_download() as download:page.locator('#external-export').click()
                old_path=home/'old.packet.json';download.value.save_as(old_path)
                old_packet=json.loads(old_path.read_text())
                page.locator('[data-close="external-dialog"]').click()
                changed=BODY+'\n\nThis is an author-written change in a test fixture.'
                page.locator('#editor').fill(changed);expect(page.locator('#save-status')).to_have_text('Saved locally')
                old_result=x.wrap_result(old_packet,dict(EMPTY,issues=[ISSUE]),'stale-input fixture')
                result_path.write_text(json.dumps(old_result))
                page.locator('[aria-label="Review actions"]').click()
                page.locator('#external-import-open').click()
                expect(page.locator('#external-dialog')).to_be_visible()
                page.locator('#external-result-file').set_input_files(str(result_path))
                expect(page.locator('#external-preview')).to_contain_text('Earlier draft or context')
                page.locator('#external-confirm-import').click()
                expect(page.locator('#pass-progress')).to_have_text('0 / 30 run')
                expect(page.locator('#draft-highlights')).to_be_hidden()
                assert page.locator('#editor').input_value()==changed
                # Import through a separate local CLI process. Browser polls shared metadata.
                page.locator('#pass').select_option('restore-actions-to-verbs')
                page.locator('#run-review').click()
                with page.expect_download() as download:page.locator('#external-export').click()
                local_path=home/'local.packet.json';download.value.save_as(local_path)
                local_packet=json.loads(local_path.read_text())
                page.locator('[data-close="external-dialog"]').click()
                local_result=x.wrap_result(local_packet,dict(EMPTY,issues=[ISSUE]),'local CLI test fixture')
                result_path.write_text(json.dumps(local_result))
                subprocess.run([sys.executable,str(ROOT/'scripts/workshop.py'),'--data-dir',str(store.home),
                                'import-result',str(result_path)],capture_output=True,text=True,check=True)
                expect(page.locator('#review-provider')).to_contain_text('local CLI test fixture',timeout=12000)
                expect(page.locator('#pass-progress')).to_have_text('1 / 30 run')
                assert page.locator('#editor').input_value()==changed
                assert store.jobs(d['id'])==[]
                # The receipt selects its own document, even while another document is open.
                other=store.create('Other document fixture','Keep this other draft unchanged.')
                page.evaluate('refreshDocuments()');page.locator('#toggle-library').click()
                page.locator(f'[data-doc="{other["id"]}"]').click()
                expect(page.locator('#editor')).to_have_value('Keep this other draft unchanged.')
                page.locator('[aria-label="Review actions"]').click()
                page.locator('#external-import-open').click()
                expect(page.locator('#external-dialog')).to_be_visible()
                page.locator('#external-result-file').set_input_files(str(result_path))
                expect(page.locator('#external-preview')).to_contain_text(d['title'])
                page.locator('#external-confirm-import').click()
                expect(page.locator('#title')).to_have_value(d['title'])
                expect(page.locator('#editor')).to_have_value(changed)
                assert store.one('documents',other['id'])['body']=='Keep this other draft unchanged.'
                if not args.dom_bridge:
                    server.token='synthetic-restarted-session'
                    page.locator('#title').fill('Unsaved rename during a restarted session')
                    expect(page.locator('#reconnect-btn')).to_be_visible()
                    expect(page.locator('#save-status')).to_contain_text('Not saved')
                    assert page.locator('#editor').input_value()==changed
                    page.locator('#reconnect-btn').click()
                    expect(page.locator('#reconnect-btn')).to_be_hidden()
                    expect(page.locator('#save-status')).to_have_text('Saved locally')
                    assert store.one('documents',d['id'])['title']=='Unsaved rename during a restarted session'
                    assert store.one('documents',d['id'])['body']==changed
                # Responsive dialog and keyboard-visible controls.
                page.set_viewport_size({'width':390,'height':844})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
                page.locator('#run-review').click()
                expect(page.locator('#external-dialog')).to_be_visible()
                assert page.locator('#external-dialog').bounding_box()['width']<=390
                assert page.locator('#external-confirm-import').is_hidden()
                page.locator('#external-snapshot').select_option(str(target['revision_id']))
                page.locator('#external-copy-agent').click()
                expect(page.locator('#external-copy-ready')).to_be_visible()
                expect(page.locator('#external-copy-agent')).to_be_enabled()
                pinned=json.loads(page.locator('#external-copy-text').input_value().split('TARGET_JSON:\n',1)[1])
                pinned_packet=json.loads(subprocess.check_output(pinned['export_argv'],text=True))
                assert pinned_packet['request']['revision_id']==target['revision_id']
                assert store.one('revisions',pinned_packet['request']['revision_id'])['body']==BODY
                assert page.locator('#editor').input_value()==changed
                if not args.dom_bridge:
                    page.locator('[data-close="external-dialog"]').click()
                    page.context.set_offline(True)
                    page.locator('#title').fill('Text held locally during outage')
                    expect(page.locator('#reconnect-btn')).to_be_visible()
                    expect(page.locator('#notice')).to_contain_text('Connection lost')
                    saved=store.one('documents',d['id'])
                    store.save(d['id'],dict(saved,body='Concurrent edit that must not be overwritten.'))
                    page.context.set_offline(False)
                    page.locator('#reconnect-btn').click()
                    expect(page.locator('#notice')).to_contain_text('saved draft changed elsewhere')
                    assert page.locator('#editor').input_value()==changed
                    assert page.locator('#title').input_value()=='Text held locally during outage'
                    assert store.one('documents',d['id'])['body']=='Concurrent edit that must not be overwritten.'
                assert not errors,errors
                print(('DOM-BRIDGE (not browser HTTP)' if args.dom_bridge else 'DIRECT HTTP')+
                      ': PASS — export, exact pass routing, paste/file import, preview before commit, invalid envelope errors, zero paid jobs, duplicate status preservation, stale-snapshot handling, local CLI auto-refresh, cross-document routing, author text preservation, mobile dialog; zero page errors.')
                browser.close()
        finally:server.shutdown();server.server_close();thread.join()

if __name__=='__main__':main()
