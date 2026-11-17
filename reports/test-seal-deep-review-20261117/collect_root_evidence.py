"""Reconcile existing observations only; no tests, compilation, RPC or signing."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OWN = Path(__file__).resolve().parent
EXTERNAL = Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/test-seal-deep-review-20261117')
sys.path.insert(0, str(ROOT))
from zzz_ops.abi import keccak256


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main():
    cache = read(EXTERNAL / 'corpus-source-keccak-cache.json')
    def kh(raw):
        key = digest(raw)
        if key not in cache:
            cache[key] = '0x' + keccak256(raw).hex()
        return cache[key]

    artifact_path = EXTERNAL / 'opensea-out/SeaDropArtworkBoundary20261117.t.sol/SeaDropArtworkBoundary20261117Test.json'
    raw = artifact_path.read_bytes()
    artifact = json.loads(raw)
    meta = artifact['metadata']
    if isinstance(meta, str):
        meta = json.loads(meta)
    scope = {}
    historical = {}
    baseline = read(OWN / 'BASELINE.json')['baseline_commit']
    for name, record in meta['sources'].items():
        source = (ROOT / name).read_bytes()
        expected = record['keccak256']
        if expected in (kh(source), kh(source.replace(b'\r\n', b'\n'))):
            stage = 'current exact source (compiler may normalize CRLF only)'
        else:
            # Match the actual retained bytes, including rejected intermediate
            # reservation implementations. Never label those as final code.
            candidates = []
            for folder in ('normal-1', 'normal-final', 'reservation-size-probe1', 'reservation-size-probe2'):
                input_path = EXTERNAL / folder / 'compiler-input.json'
                if input_path.exists():
                    item = read(input_path).get('sources', {}).get(name)
                    if item and 'content' in item:
                        candidates.append((str(input_path), item['content'].encode('utf-8')))
            old = subprocess.run(['git', 'show', baseline + ':' + name], cwd=ROOT,
                                 capture_output=True)
            if old.returncode == 0:
                candidates.append(('Git baseline ' + baseline, old.stdout))
            matched = [(where, candidate) for where, candidate in candidates
                       if expected in (kh(candidate), kh(candidate.replace(b'\r\n', b'\n')))]
            assert matched, name
            origin, source = matched[0]
            stage = 'explicit intermediate/baseline source before final reservation guard; not final-bytecode qualification'
            historical[name] = {'sha256': digest(source), 'origin': origin, 'source': source.decode('utf-8')}
        scope[name] = {'raw_sha256': digest(source), 'compiler_keccak256': expected, 'scope': stage}
    target = OWN / 'OPENSEA_ARTWORK_ARTIFACT.json.gz'
    target.write_bytes(gzip.compress(raw, mtime=0))
    proof = {'artifact_sha256': digest(raw), 'compressed_sha256': digest(target.read_bytes()),
             'compiler': meta['compiler'], 'settings': meta['settings'], 'sources': scope,
             'explicit_historical_sources': historical,
             'scope': 'one ephemeral test with enlarged harness code limit; production size acceptance is the separate closed normal build',
             'public_rpc_or_signing': False}
    (OWN / 'OPENSEA_ARTWORK_SOURCE_PROOF.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
    (EXTERNAL / 'corpus-source-keccak-cache.json').write_text(json.dumps(cache), encoding='utf-8')
    print(json.dumps({'sources_proved': len(scope), 'historical_stage_sources': list(historical),
                      'artifact_sha256': digest(raw)}))


if __name__ == '__main__':
    main()
