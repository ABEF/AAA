"""Preserve unchanged manual line endings without changing its generated text."""
from difflib import SequenceMatcher
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
path = ROOT / 'docs/OPERATOR_MANUAL.md'
old = subprocess.run(['git', 'show', '003c8d8dc88b60cbfbcc8caf61fa864c6487b40f:docs/OPERATOR_MANUAL.md'],
                     cwd=ROOT, check=True, capture_output=True).stdout.splitlines(keepends=True)
current = path.read_bytes().splitlines(keepends=True)
clean = lambda lines: [line.rstrip(b'\r\n') for line in lines]
result = []
for kind, a, b, c, d in SequenceMatcher(a=clean(old), b=clean(current), autojunk=True).get_opcodes():
    result.extend(old[a:b] if kind == 'equal' else current[c:d])
assert clean(result) == clean(current)
path.write_bytes(b''.join(result))
print('Unchanged manual line endings preserved; generated text is identical.')
