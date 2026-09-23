"""Portable review packets: same review store, independent of evaluation location.

An opaque request ID binds a returned result to the exporting database and exact
snapshot. It is a routing receipt, not authentication of a model or its quality.
The offline wrapper operates without connecting to or creating any database.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from .catalog import BY_ID
from .core import (Problem, REVIEW_SCHEMA, S, Store, integer, now, object_schema,
                   string, validate)

PACKET_FORMAT = 'voice-workshop.review-packet.v1'
RESULT_FORMAT = 'voice-workshop.review-result.v1'
PROVIDER_PLACEHOLDER = '<reviewer name>'
SCOPE_PLACEHOLDER = '<replace with actual coverage and assumptions>'
REQUEST_SCHEMA = object_schema({
    'id': S, 'document_id': {'type': 'integer', 'minimum': 1},
    'revision_id': {'type': 'integer', 'minimum': 1}, 'pass_name': S,
    'pass_version': S, 'input_sha256': S,
})
RESULT_SCHEMA = object_schema({
    'format': {'type': 'string', 'enum': [RESULT_FORMAT]},
    'request': REQUEST_SCHEMA, 'provider': S, 'result': REVIEW_SCHEMA,
})
CHAT_INSTRUCTION = (
    'Run only the named editing pass on the draft in this packet. '
    'Evaluate it yourself; do not launch the workbench or call another model. '
    'Do not rewrite or praise. Return a downloadable .review.json file following '
    'the packet’s result_schema and reply_template; preserve the request metadata '
    'exactly. Replace the provider and scope placeholders. The result will be '
    'imported into the existing workbench. If files cannot be created here, return '
    'only that complete JSON object, which the author can paste into the app.'
)


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode('utf-8')).hexdigest()


def input_digest(revision: dict) -> str:
    return digest({k: revision[k] for k in ('body', 'audience', 'purpose')})


def check_envelope(envelope: dict) -> None:
    validate(envelope, RESULT_SCHEMA)
    provider = string(envelope['provider'], 'provider', 150)
    if not provider.strip() or provider == PROVIDER_PLACEHOLDER:
        raise Problem('Replace the reviewer placeholder with the actual evaluator name.')
    scope = envelope['result']['scope']
    if not scope.strip() or scope == SCOPE_PLACEHOLDER:
        raise Problem('Supply actual review coverage; an unfilled reply template is not a completed pass.')


def wrap_result(packet: dict, result: dict, provider: str) -> dict:
    """Wrap inner findings without local storage access or a second model call."""
    if not isinstance(packet, dict) or packet.get('format') != PACKET_FORMAT:
        raise Problem('Use a Review externally packet, not a draft file or a legacy packet.')
    validate(packet.get('request'), REQUEST_SCHEMA)
    wrapped = {'format': RESULT_FORMAT, 'request': packet['request'],
               'provider': provider, 'result': result}
    check_envelope(wrapped)
    return wrapped


def export_packet(store: Store, rid: int, pass_name: str) -> dict:
    base = store.review_packet(rid, pass_name)  # Validates pass, draft, and snapshot.
    revision = store.one('revisions', rid)
    request = {'id': str(uuid.uuid4()), 'document_id': revision['doc_id'],
               'revision_id': rid, 'pass_name': pass_name,
               'pass_version': base['pass_version'], 'input_sha256': input_digest(revision)}
    template = {'format': RESULT_FORMAT, 'request': request, 'provider': PROVIDER_PLACEHOLDER,
                'result': {'scope': SCOPE_PLACEHOLDER, 'issues': []}}
    # The model's actual prompt asks for the outer envelope, not an ambiguous
    # bare {scope, issues} object. The same pass instructions and data are reused.
    prompt = base['prompt'].replace(
        'Return {"scope": "coverage and assumptions, not praise", "issues": [...]}.',
        'Return the complete external-result envelope. Put your coverage and assumptions '
        'in result.scope and your findings in result.issues. Copy format and request '
        'exactly from the reply template below. Set provider to your actual reviewer '
        'name (self-reported), never a claim of verified independence. Replace all '
        'placeholders; no findings is valid when this pass finds no material issue.'
    ).replace(json.dumps(REVIEW_SCHEMA), json.dumps(RESULT_SCHEMA), 1)
    prompt = prompt.replace(
        'Do not use tools, browse, read local files, or inspect any session history. Return\nonly the JSON object requested.',
        'Use file tools only to read this supplied packet and create its result JSON. '
        'Do not browse, inspect unrelated files or session history, or invoke another model. '
        'Return only the requested JSON object or its file attachment.'
    )
    prompt = ('EXTERNAL PASS — this is a packet to evaluate, not an instruction to '
              'launch software. Return JSON for the originating workbench.\n'
              'REPLY TEMPLATE (metadata must remain unchanged):\n' +
              json.dumps(template, ensure_ascii=False) + '\n\n' + prompt)
    packet = {'format': PACKET_FORMAT, 'request': request,
              'pass_title': base['pass_title'], 'catalog_version': base['catalog_version'],
              'instructions': CHAT_INSTRUCTION, 'prompt': prompt,
              'result_schema': RESULT_SCHEMA, 'reply_template': template}
    with store.db() as c:
        c.execute('''INSERT INTO external_requests
            (id,revision_id,pass_name,pass_version,input_sha256,packet_json,created)
            VALUES(?,?,?,?,?,?,?)''',
            (request['id'],rid,pass_name,base['pass_version'],request['input_sha256'],
             json.dumps(packet,ensure_ascii=False),now()))
    return packet


def get_packet(store: Store, request_id: str) -> dict:
    return json.loads(get_request(store, request_id)['packet_json'])


def get_request(store: Store, request_id: str) -> dict:
    string(request_id, 'request ID', 64)
    with store.db() as c:
        row = c.execute('SELECT * FROM external_requests WHERE id=?', (request_id,)).fetchone()
    if row is None:
        raise Problem('This packet was not exported from this workbench database. '
                      'Open the originating data directory; the app will not guess a target.', 404)
    return dict(row)


def requests(store: Store, doc_id: int) -> list[dict]:
    store.one('documents', doc_id)
    with store.db() as c:
        return [dict(r) for r in c.execute('''SELECT e.id,e.revision_id,e.pass_name,
            e.created,e.review_id FROM external_requests e JOIN revisions r
            ON e.revision_id=r.id WHERE r.doc_id=? ORDER BY e.rowid DESC''',(doc_id,))]


def prepare_import(store: Store, envelope: dict) -> tuple[dict, dict, list[dict], str]:
    check_envelope(envelope)
    request = get_request(store, envelope['request']['id'])
    original = json.loads(request['packet_json'])['request']
    if envelope['request'] != original:
        raise Problem('Returned request metadata does not match the exported packet. '
                      'Keep the entire request object unchanged; no findings were imported.',409)
    revision = store.one('revisions',request['revision_id'])
    if input_digest(revision) != request['input_sha256']:
        raise Problem('The stored snapshot no longer matches the exported input; import refused.',409)
    response_hash = digest(envelope)
    if request['review_id'] is not None:
        if request['response_sha256'] != response_hash:
            raise Problem('This packet already has a different result. Export a new packet '
                          'for another review; existing findings and statuses were kept.',409)
        return request, revision, [], response_hash
    _, anchored = store.prepare_review(request['revision_id'],request['pass_name'],
                                       envelope['result'],request['pass_version'])
    return request, revision, anchored, response_hash


def target_summary(store: Store, request: dict, revision: dict, envelope: dict) -> dict:
    document = store.one('documents',revision['doc_id'])
    return {'request_id':request['id'], 'document_id':revision['doc_id'],
            'document_title':document['title'], 'revision_id':revision['id'],
            'pass_name':request['pass_name'], 'pass_title':BY_ID[request['pass_name']]['title'],
            'provider':envelope['provider'], 'issue_count':len(envelope['result']['issues']),
            'same_working_input':input_digest(document)==request['input_sha256'],
            'already_imported':request['review_id'] is not None, 'review_id':request['review_id']}


def preview_result(store: Store, envelope: dict) -> dict:
    request, revision, _, _ = prepare_import(store,envelope)
    return target_summary(store,request,revision,envelope)


def import_result(store: Store, envelope: dict) -> dict:
    request, revision, anchored, response_hash = prepare_import(store,envelope)
    with store.db() as c:
        # Duplicate requests from two tabs/agents cannot create duplicate reviews.
        c.execute('BEGIN IMMEDIATE')
        live = c.execute('SELECT * FROM external_requests WHERE id=?',(request['id'],)).fetchone()
        if live['review_id'] is not None:
            if live['response_sha256'] != response_hash:
                raise Problem('This packet already has a different result; export a new packet.',409)
            vid, reused = live['review_id'], True
        else:
            provider = 'external: ' + envelope['provider'] + ' (self-reported)'
            vid = store.insert_review(c, request['revision_id'], request['pass_name'],
                                       envelope['result'], provider, anchored)
            c.execute('UPDATE external_requests SET review_id=?,response_sha256=? WHERE id=?',
                       (vid,response_hash,request['id']))
            reused = False
    request['review_id'] = vid
    return {'review':store.review(vid), 'already_imported':reused,
            'target':target_summary(store,request,revision,envelope)}
