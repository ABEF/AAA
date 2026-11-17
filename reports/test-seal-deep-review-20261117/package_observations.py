"""Archive retained task observations; never execute code or contact a service."""
import hashlib
import json
from pathlib import Path
import zipfile

OWN = Path(__file__).resolve().parent
EXTERNAL = Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/test-seal-deep-review-20261117')


def sha_file(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def excluded(relative):
    for part in relative.parts[:-1]:
        lower = part.lower()
        if (lower in ('out', 'cache', '__pycache__', 'docs-before') or
                lower.startswith(('out-', 'cache-')) or
                lower.endswith(('-out', '-cache'))):
            return True
    # Final admitted compiler bytes are already published and pinned in build/.
    return relative.as_posix() == 'normal-final-2/compiler-output.json'


def main():
    selected = []
    for path in sorted(EXTERNAL.rglob('*')):
        if not path.is_file():
            continue
        relative = path.relative_to(EXTERNAL)
        if excluded(relative):
            continue
        if path.suffix.lower() in ('.json', '.log', '.txt', '.py', '.sol', '.toml', '.gz', '.raw'):
            selected.append((path, relative.as_posix()))
    target = OWN / 'retained-observations.zip'
    rows = []
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path, relative in selected:
            rows.append({'path': relative, 'bytes': path.stat().st_size, 'sha256': sha_file(path)})
            archive.write(path, relative)
    manifest = {'schema': 1, 'scope': 'Retained success/failure/intermediate observations and drivers; not additional executions',
                'source_root': str(EXTERNAL), 'files': rows,
                'archive': target.name, 'archive_sha256': sha_file(target), 'archive_bytes': target.stat().st_size,
                'excluded': ['Unselected output/cache artifact trees', 'Original document backup copies',
                             'Accepted final compiler output duplicated by build/compiler-output.json.gz'],
                'credentials_or_private_material_intentionally_included': False}
    (OWN / 'RETAINED_OBSERVATIONS.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'files': len(rows), 'archive_bytes': target.stat().st_size, 'sha256': manifest['archive_sha256']}))


if __name__ == '__main__':
    main()
