"""Single source of truth for named editing checks and their prompt fingerprints."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

raw = json.loads((Path(__file__).parent / 'passes.json').read_text(encoding='utf-8'))
if raw.get('format_version') != 1:
    raise ValueError('Unsupported editing-pass catalog format.')
CATALOG_VERSION = raw['catalog_version']
CATALOG = raw['passes']
ids = set()
for entry in CATALOG:
    if not re.fullmatch(r'[a-z][a-z0-9-]*', entry['id']) or entry['id'] in ids:
        raise ValueError('Every editing pass needs a unique stable slug.')
    ids.add(entry['id'])
    for key in ('title', 'group', 'summary', 'focus', 'exceptions', 'task'):
        if not isinstance(entry[key], str) or not entry[key].strip():
            raise ValueError(f"Missing {key} in pass {entry['id']}.")
    # Changes to any prompt-facing content invalidate previous pass completion.
    semantic = {k: entry[k] for k in ('id', 'title', 'summary', 'focus', 'exceptions', 'task', 'checklist')}
    entry['version'] = hashlib.sha256(json.dumps(semantic, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:20]
BY_ID = {p['id']: p for p in CATALOG}
PASS_NAMES = tuple(BY_ID)
CHECKLIST_NAMES = tuple(p['id'] for p in CATALOG if p['checklist'])

def focus_prompt(name: str) -> str:
    p = BY_ID[name]
    scope = ('Review only this named check. Do not widen it into a general clarity or style review. '
             'Do not report off-pass problems, even if you notice them. ' if p['checklist'] else '')
    return (f"{p['title']}\n" + scope + p['focus'] + '\nExceptions: ' + p['exceptions'] +
            '\nAuthor task: ' + p['task'] + '\nAt most 30 findings; this is a limit, not a quota. ' +
            ('Triage is further limited to five findings. ' if name == 'triage' else '') +
            'State coverage limits in scope. If none are supported, return zero findings.')

PASS_FOCUS = {name: focus_prompt(name) for name in PASS_NAMES}
