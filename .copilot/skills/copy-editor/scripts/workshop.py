#!/usr/bin/env python3
"""Start the writing workbench or exchange structured review packets with an agent."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import webbrowser

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from workshop.core import PASS_NAMES, Problem, Store
from workshop.server import WorkshopServer
from workshop.catalog import CATALOG
from workshop import exchange


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,default=None,help='Persistent data directory; defaults to personal app data, outside the skill.')
    sub=parser.add_subparsers(dest='command',required=True)
    serve=sub.add_parser('serve',help='Start loopback web UI. Ctrl-C stops it.')
    serve.add_argument('--port',type=int,default=8765)
    serve.add_argument('--open',action='store_true',help='Open the local URL in the browser.')
    serve.add_argument('--file',type=Path,help='Import a copy of a UTF-8 text/Markdown file on launch.')
    imp=sub.add_parser('import',help='Copy a UTF-8 source into the workbench; never edit the source.')
    imp.add_argument('file',type=Path);imp.add_argument('--title',default='')
    sub.add_parser('list',help='List document IDs.')
    sub.add_parser('passes',help='List individually runnable checks, stable IDs, prompts and versions.')
    progress=sub.add_parser('progress',help='Show pass completion and finding counts for this exact draft or snapshot.')
    progress.add_argument('doc_id',type=int);progress.add_argument('--revision',type=int)

    snap=sub.add_parser('snapshot');snap.add_argument('doc_id',type=int);snap.add_argument('--note',default='');snap.add_argument('--major',action='store_true')
    packet=sub.add_parser('review-packet');packet.add_argument('revision_id',type=int);packet.add_argument('--pass',dest='pass_name',choices=PASS_NAMES,default='triage');packet.add_argument('--out',type=Path)
    result=sub.add_parser('import-review');result.add_argument('revision_id',type=int);result.add_argument('json_file',type=Path);result.add_argument('--pass',dest='pass_name',choices=PASS_NAMES,default='triage');result.add_argument('--provider',default='agent-import');result.add_argument('--pass-version',help='Use the pass_version from the exported packet; reject an outdated prompt.')
    ext=sub.add_parser('external-packet',help='Export a portable pass for another chat/agent; no model invocation.')
    ext.add_argument('doc_id',type=int);ext.add_argument('--revision',type=int)
    ext.add_argument('--pass',dest='pass_name',choices=PASS_NAMES,required=True);ext.add_argument('--out',type=Path)
    wrapped=sub.add_parser('wrap-result',help='Wrap inner findings with a packet receipt; no database access.')
    wrapped.add_argument('packet_file',type=Path);wrapped.add_argument('findings_file',type=Path)
    wrapped.add_argument('--provider',required=True);wrapped.add_argument('--out',type=Path)
    incoming=sub.add_parser('import-result',help='Store an external result in its exact pass/snapshot automatically.')
    incoming.add_argument('json_file',type=Path);incoming.add_argument('--check',action='store_true',help='Validate and preview only; do not import.')
    compare=sub.add_parser('compare-packet');compare.add_argument('doc_id',type=int);compare.add_argument('first',type=int);compare.add_argument('second',type=int);compare.add_argument('--context',default='');compare.add_argument('--criteria',default='');compare.add_argument('--out',type=Path,required=True)
    cin=sub.add_parser('import-comparison');cin.add_argument('comparison_id',type=int);cin.add_argument('json_file',type=Path);cin.add_argument('--provider',default='external-import; evaluator isolation not verified')
    backup=sub.add_parser('backup');backup.add_argument('out',type=Path)
    args=parser.parse_args()
    def emit(value,out=None):
        text=json.dumps(value,ensure_ascii=False,indent=2)
        if out:
            # Never silently overwrite source prose or an existing exchange file.
            with out.expanduser().open('x',encoding='utf-8') as f:f.write(text+'\n')
            print(str(out.expanduser().resolve()))
        else:print(text)
    def read_json(path):
        if path.stat().st_size>2_000_000:raise Problem('Exchange file exceeds the 2 MB limit.')
        return json.loads(path.read_text(encoding='utf-8-sig'))
    if args.command=='wrap-result':
        emit(exchange.wrap_result(read_json(args.packet_file),read_json(args.findings_file),args.provider),args.out)
        return
    s=Store(args.data_dir)
    if args.command=='serve':
        if args.file:
            s.create(args.file.stem,args.file.read_text(encoding='utf-8'))
        with WorkshopServer(s,args.port) as server:
            print(f'Copy Editor — {server.origin}',flush=True)
            print(f'Data: {s.home}\nStop with Ctrl-C. Reviews and comparisons use external packet exchange only.',flush=True)
            if args.open:webbrowser.open(server.origin)
            try:server.serve_forever(poll_interval=.2)
            except KeyboardInterrupt:print('\nStopped.')
    elif args.command=='import':emit(s.create(args.title or args.file.stem,args.file.read_text(encoding='utf-8')))
    elif args.command=='list':emit(s.docs())
    elif args.command=='passes':emit(CATALOG)
    elif args.command=='progress':emit(s.pass_progress(args.doc_id,args.revision))
    elif args.command=='snapshot':emit(s.snapshot(args.doc_id,args.note,args.major))
    elif args.command=='review-packet':emit(s.review_packet(args.revision_id,args.pass_name),args.out)
    elif args.command=='import-review':emit(s.import_review(args.revision_id,args.pass_name,json.loads(args.json_file.read_text(encoding='utf-8')),args.provider,args.pass_version))
    elif args.command=='external-packet':
        if args.revision is not None:
            r=s.one('revisions',args.revision)
            if r['doc_id']!=args.doc_id:raise Problem('Revision belongs to another document.')
        else:
            d=s.one('documents',args.doc_id)
            if not d['body'].strip():raise Problem('Write or import a draft first.')
            r=s.snapshot(args.doc_id,'Review externally: '+args.pass_name)
        emit(exchange.export_packet(s,r['id'],args.pass_name),args.out)
    elif args.command=='import-result':
        result=read_json(args.json_file)
        emit(exchange.preview_result(s,result) if args.check else exchange.import_result(s,result))
    elif args.command=='compare-packet':
        c=s.make_comparison(args.doc_id,args.first,args.second,args.context,args.criteria)
        # Mapping stays in SQLite. The file contains only the schema and neutral prompt.
        emit(s.comparison_packet(c['id']),args.out)
        print(f'Comparison ID for later import: {c["id"]}',file=sys.stderr)
    elif args.command=='import-comparison':emit(s.import_comparison(args.comparison_id,json.loads(args.json_file.read_text(encoding='utf-8')),args.provider))
    elif args.command=='backup':s.backup(args.out);print(str(args.out.resolve()))

if __name__=='__main__':
    try:main()
    except (Problem,OSError,ValueError) as exc:
        print(f'Error: {exc}',file=sys.stderr);sys.exit(1)
