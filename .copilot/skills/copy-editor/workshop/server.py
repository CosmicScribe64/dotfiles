"""Loopback-only HTTP interface. No framework or pip installation required."""
from __future__ import annotations
from .catalog import CATALOG, CATALOG_VERSION

import contextlib
import fcntl
import html
import http.cookies
import json
import mimetypes
import secrets
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from . import exchange
from .core import MAX_TEXT, PASS_NAMES, Problem, ROOT, Store, integer, now


class WorkshopServer(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, store: Store, port: int = 8765):
        self.store=store
        self.token=secrets.token_urlsafe(32)
        self._lock_file=(store.home/'server.lock').open('a+')
        try:
            fcntl.flock(self._lock_file,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            self._lock_file.close()
            raise Problem('A workbench is already running for this data directory. Reuse that window, or choose a different --data-dir.',409)
        try:
            super().__init__(('127.0.0.1',port),Handler)
        except Exception:
            self._lock_file.close()
            raise
        self.port=self.server_address[1]
        self.origin=f'http://127.0.0.1:{self.port}'
        with self.store.db() as c:
            c.execute('UPDATE jobs SET status="error",error="Interrupted by a previous server shutdown; no automatic retry.",updated=? WHERE status IN ("queued","running")',(now(),))

    def server_close(self):
        super().server_close()
        self._lock_file.close()


class Handler(BaseHTTPRequestHandler):
    server_version='VoiceWorkshop/4.0'
    def log_message(self, fmt, *args):
        # No draft text, query strings, session tokens or prompts in access logs.
        pass

    def send(self, data, status=200, kind='application/json; charset=utf-8', extra=None):
        if kind.startswith('application/json'):
            data=json.dumps(data,ensure_ascii=False).encode('utf-8')
        elif isinstance(data,str): data=data.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type',kind)
        self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
        for key,value in (extra or {}).items(): self.send_header(key,value)
        self.end_headers()
        with contextlib.suppress(BrokenPipeError,ConnectionResetError): self.wfile.write(data)

    def authorize(self, write=False):
        if self.headers.get('Host') != f'127.0.0.1:{self.server.port}':
            raise Problem('Use the exact loopback address printed by the launcher.',403)
        if self.headers.get('Sec-Fetch-Site') in ('cross-site','same-site'):
            raise Problem('Cross-site access is not permitted.',403)
        origin=self.headers.get('Origin')
        if origin is not None and origin != self.server.origin:
            raise Problem('Origin not permitted.',403)
        cookie=http.cookies.SimpleCookie()
        with contextlib.suppress(http.cookies.CookieError): cookie.load(self.headers.get('Cookie',''))
        session=cookie.get('voice_session')
        if not session or not secrets.compare_digest(session.value,self.server.token):
            raise Problem('Open the workbench home page first.',403)
        if write:
            csrf=self.headers.get('X-Workshop-Token','')
            if not secrets.compare_digest(csrf,self.server.token): raise Problem('Missing session token.',403)
            if self.headers.get('Content-Type','').split(';')[0] != 'application/json':
                raise Problem('JSON request body required.',415)

    def json_body(self):
        try: n=int(self.headers.get('Content-Length','0'))
        except ValueError: raise Problem('Invalid body length.')
        if not 0 < n <= 2_000_000: raise Problem('Request body is empty or too large.',413)
        self.connection.settimeout(20)
        try: data=json.loads(self.rfile.read(n).decode('utf-8'))
        except (ValueError,UnicodeError,TimeoutError) as exc: raise Problem('Invalid JSON request.') from exc
        if not isinstance(data,dict): raise Problem('JSON object required.')
        return data

    def do_GET(self):
        try: self.get()
        except Problem as exc: self.send({'error':str(exc)},exc.status)
        except (sqlite3.Error,OSError,ValueError) as exc: self.send({'error':f'Local operation failed: {exc}'},500)

    def do_POST(self):
        try:
            self.authorize(write=True)
            self.post(self.json_body())
        except Problem as exc: self.send({'error':str(exc)},exc.status)
        except (sqlite3.Error,OSError,ValueError) as exc: self.send({'error':f'Local operation failed: {exc}'},500)

    def get(self):
        url=urlsplit(self.path); path=url.path; query=parse_qs(url.query)
        store=self.server.store
        if path=='/':
            if self.headers.get('Host') != f'127.0.0.1:{self.server.port}' or self.headers.get('Sec-Fetch-Site') in ('cross-site','same-site'):
                raise Problem('Use the loopback address printed by the launcher.',403)
            page=(ROOT/'static/index.html').read_text(encoding='utf-8').replace('__TOKEN__',self.server.token)
            # htmx is loaded only from a local vendored file, when installed. Native fallback is always available.
            page=page.replace('__HTMX__','<script src="/static/htmx.min.js" defer></script>' if (ROOT/'static/htmx.min.js').is_file() else '')
            self.send(page,kind='text/html; charset=utf-8',extra={'Set-Cookie':f'voice_session={self.server.token}; HttpOnly; SameSite=Strict; Path=/'})
            return
        self.authorize()
        if path.startswith('/static/'):
            filename=path.removeprefix('/static/')
            if filename not in ('app.js','anchors.js','styles.css','htmx.min.js','public-sans.woff2'): raise Problem('Not found.',404)
            file=ROOT/'static'/filename
            if not file.exists(): raise Problem('Not found.',404)
            if file.suffix=='.woff2':
                self.send(file.read_bytes(),kind='font/woff2'); return
            kind='application/javascript' if file.suffix=='.js' else 'text/css'
            self.send(file.read_bytes(),kind=kind+'; charset=utf-8'); return
        parts=path.strip('/').split('/')
        if path=='/api/state':
            self.send({'documents':store.docs(),'passes':list(PASS_NAMES), 'catalog':CATALOG, 'catalog_version':CATALOG_VERSION, 'provider':'external',
                       'htmx':(ROOT/'static/htmx.min.js').is_file(),
                       'data_home':str(store.home),'skill_root':str(ROOT.parent.resolve()),'max_text':MAX_TEXT}); return
        if path=='/fragments/documents':
            rows=store.docs()
            markup=''.join(f'<button class="doc-item" data-doc="{r["id"]}" type="button"><span>{html.escape(r["title"])}</span><small>Draft {r["version"]}</small></button>' for r in rows)
            self.send(markup or '<p class="muted empty-small">No documents yet.</p>',kind='text/html; charset=utf-8');return
        if len(parts)==3 and parts[:2]==['api','external-packets']:
            self.send(exchange.get_packet(store,parts[2])); return
        if len(parts)==3 and parts[:2]==['api','documents']:
            ident=integer(int(parts[2]),'document id')
            d=store.one('documents',ident)
            self.send(dict(d,revisions=store.revisions(ident),reviews=store.reviews(ident),comparisons=store.comparisons(ident),jobs=store.jobs(ident),pass_progress=store.pass_progress(ident),external_requests=exchange.requests(store,ident))); return
        if len(parts)==4 and parts[:2]==['api','documents'] and parts[3]=='passes':
            target=query.get('revision',[None])[0]
            self.send(store.pass_progress(int(parts[2]),int(target) if target is not None else None)); return
        if len(parts)==3 and parts[0]=='api' and parts[1] in ('revisions','reviews','comparisons','jobs'):
            ident=int(parts[2]); table=parts[1]
            self.send(store.review(ident) if table=='reviews' else store.one(table,ident)); return
        if len(parts)==4 and parts[0]=='api' and parts[3]=='packet':
            ident=int(parts[2])
            if parts[1]=='revisions': self.send(store.review_packet(ident,query.get('pass',['triage'])[0]));return
            if parts[1]=='comparisons': self.send(store.comparison_packet(ident));return
        raise Problem('Not found.',404)

    def post(self,p):
        path=urlsplit(self.path).path
        parts=path.strip('/').split('/')
        s=self.server.store
        if path=='/api/external-results/preview':
            self.send(exchange.preview_result(s,p));return
        if path=='/api/external-results/import':
            self.send(exchange.import_result(s,p),201);return
        if path=='/api/documents':
            self.send(s.create(p.get('title','Untitled'),p.get('body',''),p.get('audience',''),p.get('purpose','')),201);return
        if len(parts)==4 and parts[:2]==['api','documents']:
            ident=int(parts[2]); action=parts[3]
            if action=='save': self.send(s.save(ident,p));return
            if action=='snapshot': self.send(s.snapshot(ident,p.get('note',''),p.get('major',False)),201);return
            if action=='current-snapshot':
                self.send(s.snapshot(ident,'Current working draft',expected_version=integer(p.get('version'),'version'),reuse_latest=True));return
            if action=='restore': self.send(s.restore(ident,integer(p.get('revision_id'),'revision_id'),integer(p.get('version'),'version')));return
            if action=='external-packet':
                rid=p.get('revision_id')
                if rid is None:
                    d=s.one('documents',ident)
                    if not d['body'].strip(): raise Problem('Write or import a draft first.')
                    if p.get('pass_name') not in PASS_NAMES: raise Problem('Unknown editing pass.')
                    rid=s.snapshot(ident,'Review externally: '+p['pass_name'])['id']
                else:
                    rid=integer(rid,'revision_id')
                    if s.one('revisions',rid)['doc_id']!=ident: raise Problem('Revision belongs to another document.')
                self.send(exchange.export_packet(s,rid,p.get('pass_name','triage')),201);return
            if action=='compare':
                c=s.make_comparison(ident,integer(p.get('first'),'first'),integer(p.get('second'),'second'),p.get('context',''),p.get('criteria',''),reuse_pending=True)
                self.send(c,201);return
        if len(parts)==4 and parts[0]=='api':
            ident=int(parts[2]); kind=parts[1]; action=parts[3]
            if kind=='revisions' and action=='flag': self.send(s.flag(ident,p.get('major',False)));return
            if kind=='revisions' and action=='import-review': self.send(s.import_review(ident,p.get('pass_name','triage'),p.get('result'),p.get('provider','agent-import'),p.get('pass_version')),201);return
            if kind=='issues' and action=='status': s.issue_status(ident,p.get('status'));self.send({'ok':True});return
            if kind=='comparisons' and action=='import':
                self.send(s.import_comparison(ident,p.get('result'),p.get('provider','external-import; evaluator isolation not verified')));return
        raise Problem('Not found.',404)
