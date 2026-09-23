"""Exercise v3 pass selection, checks per draft, author editing and packet exchange.
The optional DOM bridge never makes browser network requests. Fixtures, not models.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import threading
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from workshop.core import Store,Problem
from workshop.server import WorkshopServer,Handler

BODY=('👩🏽‍💻 I really wanted the comments next to the words.\n\n'
      'The creation of a separate editing window added another step.\n\n'
      'I opened another tab in order to find the feedback.\n\n'
      'The next revision belongs to the author, not the tool.')
PASS='sand-filler-words'

def finding(paragraph,quote):
    return {'paragraph':paragraph,'quote':quote,'occurrence':1,'priority':'low','category':'Interface test fixture',
            'problem':'Synthetic finding; no model evaluation was performed.',
            'reader_effect':'This fixture exercises the editor interface only.',
            'revision_task':'Test the controls. Do not treat this as writing advice.',
            'tradeoff':'','confidence':'low'}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--dom-bridge',action='store_true')
    parser.add_argument('--chromium',default=shutil.which('chromium') or shutil.which('google-chrome'))
    parser.add_argument('--screenshot-dir',type=Path)
    args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='workshop-v3-ui-test-') as tmp:
        home=Path(tmp);store=Store(home/'db');server=WorkshopServer(store,0)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with sync_playwright() as pw:
                browser=pw.chromium.launch(executable_path=args.chromium,headless=True,args=['--no-sandbox'])
                page=browser.new_page(viewport={'width':1440,'height':1100})
                errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:d.accept())
                def mount():
                    markup=(ROOT/'workshop/static/index.html').read_text().replace('__TOKEN__',server.token).replace('__HTMX__','')
                    markup=re.sub(r'<link[^>]*>|<script src="/static/(?:app|anchors).js" defer></script>','',markup)
                    page.set_content(markup);page.add_style_tag(content=(ROOT/'workshop/static/styles.css').read_text())
                    page.add_script_tag(content='''window.fetch=async function(path,opts={}) {
                        const r=await window.testBackend(String(path),opts.body||null);
                        return new Response(r.text,{status:r.status,headers:{'Content-Type':r.kind}});
                    };''')
                    for file in ['anchors.js','app.js']:page.add_script_tag(content=(ROOT/'workshop/static'/file).read_text())
                if args.dom_bridge:
                    def backend(source,path,body):
                        if not path.startswith(('/api/','/fragments/')):raise RuntimeError('Not a local generated-app route')
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
                    page.expose_binding('testBackend',backend);mount()
                else:page.goto(server.origin)
                expect(page.locator('#empty-state')).to_be_visible()
                if not args.dom_bridge:
                    page.evaluate('document.fonts.ready')
                    assert page.evaluate('document.fonts.check(\'14px "Public Sans"\')')
                page.locator('#new-doc').click();page.locator('#title').fill('v3 integration fixture')
                expect(page.locator('.editor-toolbar #title')).to_be_visible()
                expect(page.locator('.document-heading')).to_have_count(0)
                title_box=page.locator('#title').bounding_box()
                controls_box=page.locator('.editor-controls').bounding_box()
                assert abs(title_box['y']+title_box['height']/2-controls_box['y']-controls_box['height']/2)<=1
                brand=page.locator('.brand-mark').bounding_box()
                documents=page.locator('#toggle-library').bounding_box()
                assert abs(documents['x']-brand['x'])<=1
                assert page.locator('#toggle-library').evaluate('(element)=>getComputedStyle(element).fontSize')=='14px'
                expect(page.locator('.review-pane>.context-details:first-child')).not_to_have_attribute('open','')
                expect(page.get_by_role('heading',name='Writing context',exact=True)).to_be_visible()
                expect(page.locator('.context-details summary .context-optional')).to_have_text('optional')
                expect(page.locator('.context-grid .context-optional')).to_have_count(0)
                expect(page.locator('#audience')).not_to_be_visible()
                expect(page.locator('#purpose')).not_to_be_visible()
                assert page.locator('#audience').input_value()=='' and page.locator('#purpose').input_value()==''
                assert page.locator('.context-grid textarea').evaluate_all('(elements)=>elements.every(element=>!element.required)')
                assert page.evaluate('''() => {
                    const context=getComputedStyle(document.querySelector('.context-title'));
                    const pass=getComputedStyle(document.getElementById('selected-pass-title'));
                    return context.fontSize===pass.fontSize && context.fontWeight===pass.fontWeight && context.color===pass.color;
                }''')
                page.locator('#editor').fill(BODY);expect(page.locator('#save-status')).to_have_text('Saved locally')
                long_draft='\n'.join(f'Synthetic paragraph {index}: text for a layout check.' for index in range(80))
                page.locator('#editor').fill(long_draft)
                expect(page.locator('#save-status')).to_have_text('Saved locally')
                assert page.locator('#editor').evaluate('(element)=>element.scrollHeight<=element.clientHeight+1')
                assert page.locator('#editor').evaluate('(element)=>getComputedStyle(element).resize')=='none'
                page.locator('#editor').fill(BODY)
                expect(page.locator('#save-status')).to_have_text('Saved locally')
                page.locator('#editor').focus()
                page.locator('#editor').evaluate('(element)=>element.select()')
                page.locator('#editor').click(button='right',position={'x':30,'y':12})
                assert page.locator('#editor').input_value()==BODY
                assert page.locator('#editor').evaluate('(element)=>element.value.slice(element.selectionStart,element.selectionEnd)')==BODY
                page.keyboard.press('Escape')
                total_words=len(BODY.split())
                page.locator('#editor').focus()
                page.locator('#editor').evaluate("element=>{const start=element.value.indexOf('really');element.setSelectionRange(start,start+'really wanted'.length)}")
                expect(page.locator('#word-count')).to_have_text(f'{total_words} words · 2 selected')
                page.locator('#editor').press('ArrowRight')
                expect(page.locator('#word-count')).to_have_text(f'{total_words} words')
                page.locator('#title').focus()
                page.locator('#title').evaluate('(element)=>element.select()')
                expect(page.locator('#word-count')).to_have_text(f'{total_words} words')
                assert page.locator('.paper-footer').bounding_box()['height']<=32
                ident=store.docs()[0]['id'];baseline=store.snapshot(ident,'Original test input')['id']
                expect(page.locator('#pass optgroup').first).to_have_attribute('label','Broad reviews')
                expect(page.locator('#pass optgroup').first.locator('option')).to_have_count(7)
                expect(page.locator('#pass')).to_have_value('triage')
                for opener,dialog in [('#help-btn','#help-dialog'),('#passes-btn','#passes-dialog'),('#run-review','#external-dialog'),('#snapshot-btn','#snapshot-dialog'),('#history-btn','#history-dialog')]:
                    for dismissal in ['escape','backdrop']:
                        if opener in ['#snapshot-btn','#history-btn']:page.locator('[aria-label="Document actions"]').click()
                        page.locator(opener).click()
                        expect(page.locator(dialog)).to_be_visible()
                        page.locator(dialog+' h2').first.click()
                        expect(page.locator(dialog)).to_be_visible()
                        if dismissal=='escape':page.keyboard.press('Escape')
                        else:page.mouse.click(2,2)
                        expect(page.locator(dialog)).not_to_be_visible()
                        expect(page.locator('#editor')).to_be_focused()
                        assert page.locator('#editor').input_value()==BODY
                page.locator('[aria-label="Document actions"]').click()
                page.locator('.app-header strong').click()
                expect(page.locator('.actions-menu[open]')).to_have_count(0)
                expect(page.locator('#editor')).to_be_focused()
                page.locator('[aria-label="Document actions"]').click()
                page.locator('#title').click()
                expect(page.locator('#title')).to_be_focused()
                page.locator('.paper-footer').click()
                expect(page.locator('#editor')).to_be_focused()
                page.locator('#passes-btn').click()
                expect(page.locator('#passes-dialog')).to_be_visible()
                expect(page.locator('#pass-list [data-pass]')).to_have_count(37)
                expect(page.locator('#pass-list .pass-group h3').first).to_have_text('Broad reviews')
                expect(page.locator('#pass-list [data-pass]').first).to_have_attribute('data-pass','triage')
                assert page.locator('#pass-list').evaluate('(element)=>element.scrollTop')==0
                expect(page.locator('#checklist-count')).to_have_text('0 of 30 run')
                page.locator('#pass-search').fill('verbs')
                expect(page.locator('[data-pass="restore-actions-to-verbs"]')).to_be_visible()
                page.locator('[data-pass="restore-actions-to-verbs"]').click()
                expect(page.locator('#pass')).to_have_value('restore-actions-to-verbs')
                expect(page.locator('#selected-pass-title')).to_have_text('Restore actions to verbs')
                expect(page.locator('#findings .finding')).to_have_count(0)
                page.locator('[aria-label="Review actions"]').click()
                page.locator('#next-pass').click();expect(page.locator('#pass')).to_have_value('delete-empty-verbs')
                page.locator('[aria-label="Review actions"]').click()
                page.locator('#prev-pass').click();expect(page.locator('#pass')).to_have_value('restore-actions-to-verbs')
                # Simply selecting checks creates no model jobs.
                assert not store.jobs(ident)
                page.locator('#run-review').click()
                expect(page.locator('#external-dialog')).to_be_visible()
                assert not store.jobs(ident)
                page.locator('[data-close="external-dialog"]').click()
                store.import_review(baseline,'restore-actions-to-verbs',{'scope':'DEMO FIXTURE: interface test only.','issues':[finding(2,'The creation')]},'demo-fixture')
                expect(page.locator('.finding')).to_have_count(1,timeout=10000)
                expect(page.locator('#draft-highlights')).to_be_visible()
                expect(page.locator('#pass-progress')).to_have_text('0 / 30 run')
                page.locator('#passes-btn').click()
                expect(page.locator('[data-pass="restore-actions-to-verbs"]')).to_contain_text('Demo only')
                page.locator('[data-close="passes-dialog"]').click()
                # Non-demo imports exercise successful-check accounting. These are still TEST fixtures.
                v=store.import_review(baseline,PASS,{'scope':'TEST FIXTURES — not a live model evaluation.',
                    'issues':[finding(1,'really'),finding(3,'in order to')]},'test-fixture')
                store.import_review(baseline,'full',{'scope':'TEST FIXTURE: broad reviews do not count.','issues':[]},'test-fixture')
                page.locator('#passes-btn').click()
                expect(page.locator('#checklist-count')).to_have_text('1 of 30 run')
                expect(page.locator('[data-pass="sand-filler-words"]')).to_contain_text('2 open')
                page.locator('#pass-filter').select_option('current')
                expect(page.locator('#pass-list [data-pass]')).to_have_count(2) # one individual + broad full review
                page.locator('[data-pass="sand-filler-words"]').click()
                expect(page.locator('.finding')).to_have_count(2)
                expect(page.locator('.finding:visible')).to_have_count(1)
                expect(page.locator('#finding-count')).to_have_text('1 of 2')
                expect(page.locator('#review-note')).not_to_be_visible()
                expect(page.locator('#review-select')).not_to_be_visible()
                page.locator('.finding:visible summary').click()
                expect(page.locator('.finding:visible .reader-effect')).to_be_visible()
                page.locator('#next-issue').click()
                expect(page.locator('#finding-count')).to_have_text('2 of 2')
                expect(page.locator('.finding:visible blockquote')).to_have_text('in order to')
                page.locator('#prev-issue').click()
                expect(page.locator('#finding-count')).to_have_text('1 of 2')
                page.locator('[aria-label="Review actions"]').click()
                page.keyboard.press('Escape')
                expect(page.locator('.actions-menu[open]')).to_have_count(0)
                expect(page.locator('#editor')).to_be_focused()
                expect(page.locator('#draft-highlights')).to_be_visible()
                # Mirror geometry must agree with the textarea, including scrollbar reservation.
                geometry=page.evaluate('''() => {const a=document.getElementById('editor'),b=document.getElementById('draft-highlights');
                    const x=getComputedStyle(a),y=getComputedStyle(b);return {a:a.clientWidth,b:b.clientWidth,fonts:x.font===y.font,spacing:x.letterSpacing===y.letterSpacing};}''')
                assert geometry['a']==geometry['b'] and geometry['fonts'] and geometry['spacing'],geometry
                before=page.locator('#editor').input_value()
                page.locator('[data-source-issue]').first.click();expect(page.locator('#annotated')).to_be_visible()
                page.locator('#annotated').evaluate('''element=>{
                    const range=document.createRange();range.selectNodeContents(element);
                    const selection=window.getSelection();selection.removeAllRanges();selection.addRange(range);
                }''')
                expect(page.locator('#word-count')).to_have_text(f'{total_words} words · {total_words} selected')
                page.evaluate('window.getSelection().removeAllRanges()')
                expect(page.locator('#word-count')).to_have_text(f'{total_words} words')
                page.locator('[data-edit-issue]').first.click();expect(page.locator('#editor')).to_be_visible()
                assert page.locator('#editor').input_value()==before
                selected=page.locator('#editor').evaluate('(e)=>e.value.slice(e.selectionStart,e.selectionEnd)')
                assert selected=='really',selected
                expect(page.locator('#word-count')).to_have_text(f'{total_words} words · 1 selected')
                # Finding status is independent of draft content or whether a pass ran.
                page.locator('[data-status]').first.select_option('resolved')
                expect(page.locator('.finding')).to_have_count(1)
                assert page.locator('#editor').input_value()==before
                page.locator('#passes-btn').click()
                expect(page.locator('[data-pass="sand-filler-words"]')).to_contain_text('1 open · 1 resolved')
                page.locator('[data-close="passes-dialog"]').click()
                # Make an author edit while source evidence remains immutable.
                changed=BODY.replace('in order to','to')
                page.locator('#editor').fill(changed)
                expect(page.locator('#draft-highlights')).to_be_hidden()
                expect(page.locator('#save-status')).to_have_text('Saved locally')
                expect(page.locator('#pass-progress')).to_have_text('0 / 30 run')
                page.locator('[data-edit-issue]').first.click()
                expect(page.locator('#notice')).to_contain_text('Source paragraph changed or is ambiguous')
                page.locator('[data-source-issue]').first.click()
                expect(page.locator('#annotated')).to_contain_text('in order to')
                page.locator('#passes-btn').click()
                expect(page.locator('[data-pass="sand-filler-words"]')).to_contain_text('Draft or context changed')
                expect(page.locator('#checklist-count')).to_have_text('0 of 30 run')
                page.locator('#checklist-scope').select_option(str(baseline))
                expect(page.locator('#checklist-count')).to_have_text('1 of 30 run')
                expect(page.locator('#checklist-scope-label')).to_have_text(f'Snapshot #{baseline}')
                page.locator('#pass-filter').select_option('current')
                expect(page.locator('[data-pass="sand-filler-words"]')).to_be_visible()
                page.locator('[data-close="passes-dialog"]').click()
                # Restore exact input without creating a new model result; checks become reusable.
                page.locator('#write-mode').click();page.locator('#editor').fill(BODY)
                expect(page.locator('#save-status')).to_have_text('Saved locally')
                expect(page.locator('#pass-progress')).to_have_text('1 / 30 run')
                page.locator('#title').fill('Renamed, same reviewed inputs')
                expect(page.locator('#save-status')).to_have_text('Saved locally')
                expect(page).to_have_title('Renamed, same reviewed inputs — Voice Workshop')
                expect(page.locator('#pass-progress')).to_have_text('1 / 30 run')
                expect(page.locator('.review-pane .context-details')).to_have_count(1)
                expect(page.locator('.review-pane>.context-details:first-child')).to_have_count(1)
                expect(page.locator('.context-details')).not_to_have_attribute('open','')
                expect(page.locator('.document-heading .context-details')).to_have_count(0)
                draft_offset=page.locator('#editor').evaluate('(element)=>element.getBoundingClientRect().top+window.scrollY')
                page.locator('.context-details summary').click()
                expect(page.locator('#audience')).to_be_visible()
                assert page.locator('#editor').evaluate('(element)=>element.getBoundingClientRect().top+window.scrollY')==draft_offset
                page.locator('#audience').fill('A different audience')
                expect(page.locator('#draft-highlights')).to_be_hidden()
                expect(page.locator('#save-status')).to_have_text('Saved locally')
                expect(page.locator('#pass-progress')).to_have_text('0 / 30 run')
                page.locator('#audience').fill('');expect(page.locator('#save-status')).to_have_text('Saved locally')
                expect(page.locator('#pass-progress')).to_have_text('1 / 30 run')
                context='Explain the incident timeline, customer impact, and next steps.\nKeep uncertainty visible so readers can distinguish evidence from assumptions.'
                page.locator('#purpose').fill(context)
                expect(page.locator('#save-status')).to_have_text('Saved locally')
                expect(page.locator('#pass-progress')).to_have_text('0 / 30 run')
                assert page.locator('#purpose').evaluate('(element)=>element.scrollHeight<=element.clientHeight+1')
                assert page.locator('#purpose').bounding_box()['height']>=88
                assert store.one('documents',ident)['purpose']==context
                page.locator('#purpose').fill('')
                expect(page.locator('#save-status')).to_have_text('Saved locally')
                expect(page.locator('#pass-progress')).to_have_text('1 / 30 run')
                page.locator('.context-details summary').click()
                # Export an exact targeted packet. No model call is made by export.
                page.locator('#help-btn').click()
                page.locator('.exchange summary').click()
                with page.expect_download() as info:page.locator('#packet-btn').click()
                target=home/'packet.json';info.value.save_as(target);packet=json.loads(target.read_text())
                assert packet['pass_name']==PASS and packet['pass_version']
                assert 'Do not report off-pass problems' in packet['prompt']
                # Zero findings imported through the UI still complete a check, not a false error.
                output=home/'result.json';output.write_text(json.dumps({'scope':'TEST FIXTURE — no material issue in this test.','issues':[]}))
                page.locator('#review-json').set_input_files(str(output))
                expect(page.locator('#findings')).to_contain_text('No material issue found')
                expect(page.locator('#pass-progress')).to_have_text('1 / 30 run')
                assert store.one('documents',ident)['body']==BODY
                page.locator('.exchange summary').click()
                page.locator('[data-close="help-dialog"]').click()
                # Switch to a pass without reviews; do not show the previous pass's findings.
                page.locator('#pass').select_option('find-real-actors')
                expect(page.locator('#selected-pass-title')).to_have_text('Find the real actors')
                expect(page.locator('#findings .finding')).to_have_count(0)
                assert not errors,errors
                # Screenshots use native DEMO providers only; they never fake completed checks.
                if args.screenshot_dir:
                    out=args.screenshot_dir;out.mkdir(parents=True,exist_ok=True)
                    sample=('I really wanted to keep the comments beside the words. The first version opened feedback in a second window, which sounded tidy until I started using it. Every small change sent me back through the same loop: find the comment, find the paragraph, remember what I had meant to do.\n\n'
                      'The creation of a separate editing view made the process feel more complicated than it needed to be. I could see the draft or I could see the feedback. I could not easily keep both in view while deciding what to change.\n\n'
                      'Now I choose one narrow check. Sometimes I look for the person doing the action. Sometimes I look for an explanation that arrives three paragraphs too late. The question is small enough that I can keep it in mind while I read.\n\n'
                      'I used to switch tabs in order to work through each finding. The workbench keeps the original quotation and the comment together. A button takes me to my own text; it does not insert a sentence that somebody else wrote.\n\n'
                      'The checklist is not a certificate. A check says that I ran a particular pass on this draft. It does not mean I accepted every finding, or that the next version must keep the same structure. When the text changes, the old review stays with the version it actually examined.\n\n'
                      'That distinction matters to me. I want a tool that remembers the bookkeeping while I pay attention to the writing. I still have to decide whether a phrase earns its place. I still have to write the revision.')
                    d=store.create('Keeping the words in my own hands',sample)
                    rid=store.revisions(d['id'])[0]['id']
                    v=store.import_review(rid,PASS,{'scope':'DEMO FIXTURES — sample annotations for interface demonstration; not live model feedback.','issues':[finding(1,'really'),finding(4,'in order to')]},'demo-fixture')
                    store.issue_status(v['issues'][1]['id'],'declined')
                    store.import_review(rid,'find-real-actors',{'scope':'DEMO FIXTURE — no real review.','issues':[]},'demo-fixture')
                    store.import_review(rid,'restore-actions-to-verbs',{'scope':'DEMO FIXTURE — sample only.','issues':[finding(2,'The creation of a separate editing view')]},'demo-fixture')
                    page.locator('#toggle-library').click()
                    # Refresh document list through a real app control / local metadata polling.
                    if args.dom_bridge:page.evaluate('refreshDocuments()')
                    else:page.reload()
                    if not args.dom_bridge:page.locator('#toggle-library').click()
                    page.locator(f'[data-doc="{d["id"]}"]').click()
                    page.locator('#pass').select_option(PASS)
                    expect(page.locator('.finding')).to_have_count(1)
                    expect(page.locator('#draft-highlights')).to_be_visible()
                    page.evaluate("document.getElementById('notice').hidden=true")
                    page.screenshot(path=str(out/'voice-workshop-v3-editor.png'),full_page=True)
                    page.locator('#passes-btn').click()
                    expect(page.locator('#pass-list [data-pass]')).to_have_count(37)
                    page.screenshot(path=str(out/'voice-workshop-v3-passes.png'),full_page=False)
                    page.locator('[data-close="passes-dialog"]').click()
                # Phone width: drawer and main workspace must not overflow horizontally.
                page.locator('#toggle-library').click()
                left=page.locator('#document-library').bounding_box()
                handle=page.locator('#library-resize').bounding_box()
                page.mouse.move(handle['x']+5,handle['y']+45);page.mouse.down()
                page.mouse.move(handle['x']+65,handle['y']+45,steps=8);page.mouse.up()
                assert page.locator('#document-library').bounding_box()['width']>left['width']+40
                right=page.locator('#review-sidebar').bounding_box()
                page.locator('#review-resize').focus();page.keyboard.press('ArrowLeft')
                assert page.locator('#review-sidebar').bounding_box()['width']>right['width']
                assert page.locator('.writing-pane').bounding_box()['width']>=360
                if not args.dom_bridge:
                    remembered=page.evaluate("localStorage.getItem('voice-workshop-sidebar-widths')")
                    page.reload();expect(page.locator('#editor')).to_be_visible()
                    assert page.evaluate("localStorage.getItem('voice-workshop-sidebar-widths')")==remembered
                    expected_width=json.loads(remembered)['review']
                    assert abs(page.locator('#review-sidebar').bounding_box()['width']-expected_width)<=1
                page.set_viewport_size({'width':390,'height':844})
                expect(page.locator('#library-resize')).not_to_be_visible()
                expect(page.locator('#review-resize')).not_to_be_visible()
                assert page.locator('#editor').evaluate('(element)=>element.scrollHeight<=element.clientHeight+1')
                assert page.locator('.paper-footer').bounding_box()['height']<=32
                page.locator('#title').fill('A longer synthetic document title that must wrap without clipping on a phone')
                expect(page.locator('#save-status')).to_have_text('Saved locally')
                assert page.locator('#title').evaluate('(element)=>element.scrollHeight<=element.clientHeight+1')
                expect(page.locator('.editor-toolbar #title')).to_be_visible()
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
                header=page.locator('.app-header').bounding_box()
                navigation=page.locator('#toggle-library').bounding_box()
                assert navigation['y']>=header['y']+header['height']
                expect(page.locator('#toggle-library span')).to_be_visible()
                page.locator('#passes-btn').click()
                expect(page.locator('#passes-dialog')).to_be_visible()
                assert page.locator('#passes-dialog').bounding_box()['width']<=390
                page.locator('#pass-search').fill('passive')
                expect(page.locator('[data-pass="control-passive-voice"]')).to_be_visible()
                assert not errors,errors
                print(('DOM-BRIDGE (not browser HTTP)' if args.dom_bridge else 'DIRECT HTTP')+
                    ': PASS — catalog, search/filter, selection without calls, pass navigation, demo exclusion, imported checks, counts, visible mirror, Unicode selection, no prose mutation, stale-input invalidation, snapshot scope, exact-input reuse, context/title rules, packet export/import, zero findings, mobile drawer; zero page errors.')
                browser.close()
        finally:server.shutdown();server.server_close();thread.join()

if __name__=='__main__':main()
