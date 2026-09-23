#!/usr/bin/env python3
"""Optionally vendor pinned HTMX locally. The app works without this enhancement.
No CDN requests occur in the browser. This developer setup step downloads once,
checks the upstream published SHA-384 digest, then writes the local asset.
"""
from __future__ import annotations
import base64
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import urllib.request

URL='https://cdn.jsdelivr.net/npm/htmx.org@2.0.10/dist/htmx.min.js'
SHA384='H5SrcfygHmAuTDZphMHqBJLc3FhssKjG7w/CeCpFReSfwBWDTKpkzPP8c+cLsK+V'

def main():
    target=Path(__file__).resolve().parents[1]/'workshop/static/htmx.min.js'
    with urllib.request.urlopen(URL,timeout=30) as response:
        body=response.read(300_001)
    if len(body)>300_000 or base64.b64encode(hashlib.sha384(body).digest()).decode()!=SHA384:
        raise RuntimeError('HTMX did not match the pinned upstream SHA-384. Nothing was installed.')
    fd,path=tempfile.mkstemp(dir=target.parent,prefix='.htmx-')
    try:
        with os.fdopen(fd,'wb') as f:f.write(body)
        os.replace(path,target)
    finally:
        if os.path.exists(path):os.unlink(path)
    print(f'Installed verified HTMX 2.0.10 locally at {target}. Restart the workbench.')

if __name__=='__main__':
    try:main()
    except Exception as exc:print(f'Asset download failed: {exc}',file=sys.stderr);sys.exit(1)
