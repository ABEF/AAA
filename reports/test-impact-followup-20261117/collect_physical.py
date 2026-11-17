"""Reconcile the three already executed actual-v4 checks; runs nothing."""
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
OWN=Path(__file__).resolve().parent
V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
DEST=V/'test-impact-followup-20261117/physical'
sys.path.insert(0,str(ROOT))
from zzz_ops.abi import keccak256


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    execution=json.loads((DEST/'EXECUTION.json').read_text())
    assert execution['exit_code']==0 and len(execution['methods'])==3
    assert all(row['status']=='Success' for row in execution['methods'])
    artifact=DEST/'out/OptionalPortfolioCore.t.sol/OptionalPortfolioCoreTest.json'
    raw=artifact.read_bytes();obj=json.loads(raw);meta=obj['metadata']
    if isinstance(meta,str):meta=json.loads(meta)
    cache=json.loads((V/'test-seal-deep-review-20261117/corpus-source-keccak-cache.json').read_text())
    def kh(value):
        key=sha(value)
        if key not in cache:cache[key]='0x'+keccak256(value).hex()
        return cache[key]
    sources={}
    for name,row in meta['sources'].items():
        content=(ROOT/name).read_bytes();expected=row['keccak256']
        assert expected in (kh(content),kh(content.replace(b'\r\n',b'\n'))),name
        bracketed=name in execution['source_before']
        if bracketed:
            assert execution['source_before'][name]==execution['source_after'][name]==sha(content),name
        sources[name]={'raw_sha256':sha(content),'compiler_keccak256':expected,
                       'before_after_bracketed':bracketed}
    differences=[name for name in execution['source_before'] if execution['source_before'][name]!=execution['source_after'].get(name)]
    additions=sorted(set(execution['source_after'])-set(execution['source_before']))
    assert not(set(differences+additions)&set(sources))
    (OWN/'PHYSICAL_RAW.json').write_bytes((DEST/'RESULT.json').read_bytes())
    compressed=gzip.compress(raw,mtime=0);(OWN/'PHYSICAL_ARTIFACT.json.gz').write_bytes(compressed)
    result={'schema':1,'selected_methods':execution['methods'],'distinct_selected_passes':3,
            'source_scope':'Actual selected compiler graph stable; unrelated test-tree edits are not relabelled global stability',
            'global_test_source_unchanged':execution['global_test_source_unchanged'],
            'unrelated_modified_sources':differences,'unrelated_added_sources':additions,
            'compiler':meta['compiler'],'settings':meta['settings'],'sources':sources,
            'artifact_sha256':sha(raw),'compressed_artifact_sha256':sha(compressed),
            'execution':execution,
            'scope_limits':['Controlled admission/controller/feeds/VRF/Permit2; real v4 core/periphery except explicit failure seam',
                            'Direct raw ETH/fixed-ZZZ ledger claims; not qualification of ETH-only converter/UI',
                            'Enlarged test harness size only; no production compiler/size/gas/default changes',
                            'No provider/market/complete gas/host/independent approval or existing chain work']}
    (OWN/'PHYSICAL_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    (V/'test-impact-followup-20261117/physical-keccak-cache.json').write_text(json.dumps(cache),encoding='utf-8')
    print(json.dumps({'distinct_passes':3,'compiler_source_dependencies':len(sources),'unrelated_source_changes':len(differences)+len(additions)}))


if __name__=='__main__':main()
