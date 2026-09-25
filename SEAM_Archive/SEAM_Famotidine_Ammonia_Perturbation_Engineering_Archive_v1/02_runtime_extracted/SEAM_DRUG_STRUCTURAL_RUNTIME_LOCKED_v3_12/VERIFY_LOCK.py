#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, sys
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'LOCK.json').read_text())
fail=[]
for rel,expected in manifest['files'].items():
    p=ROOT/rel
    if not p.exists(): fail.append((rel,'MISSING',expected)); continue
    got=hashlib.sha256(p.read_bytes()).hexdigest()
    if got!=expected: fail.append((rel,got,expected))
if fail:
    print('LOCK VERIFY: FAIL')
    for rel,got,exp in fail: print(rel,got,exp)
    sys.exit(1)
print(f"LOCK VERIFY: PASS ({len(manifest['files'])} locked files)")
