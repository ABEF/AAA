"""Explain saved creation-bytecode differences using known compiler metadata only.

Creation objects can contain child creation/runtime data and its own CBOR trailer.
Terminal stripping alone leaves that metadata. This read-only comparison masks
only complete metadata trailers already present in the saved compiler outputs;
it never executes bytecode, recompiles or changes production code.
"""
import datetime as dt
import hashlib
import json
from pathlib import Path

EXTERNAL=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
HERE=Path(__file__).resolve().parent


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    destination=HERE/'embedded-metadata-comparison.json'
    if destination.exists():raise ValueError('Preserve earlier comparison evidence')
    paths=[EXTERNAL/name/'solidity/source-build.json' for name in ('architecture-pruning-20261025','auditability-refactor-20261025')]
    outputs=[json.loads(path.read_text()) for path in paths]
    known={}
    for index,output in enumerate(outputs):
        for source,contracts in output['contracts'].items():
            for name,artifact in contracts.items():
                for kind in ('bytecode','deployedBytecode'):
                    text=artifact.get('evm',{}).get(kind,{}).get('object','')
                    if not text:continue
                    raw=bytes.fromhex(text);length=int.from_bytes(raw[-2:],'big')
                    if length and length+2<=len(raw) and 0xa0<=raw[-length-2]<=0xbf and b'solc' in raw[-length-2:-2]:
                        known.setdefault(raw[-length-2:],[]).append({'campaign':index,'source':source,'contract':name,'kind':kind})
    def mask(raw):
        result=bytearray(raw);regions=[];occupied=set()
        for metadata,origins in sorted(known.items(),key=lambda entry:len(entry[0]),reverse=True):
            start=0
            while True:
                offset=raw.find(metadata,start)
                if offset<0:break
                indices=set(range(offset,offset+len(metadata)))
                if not occupied.intersection(indices):
                    result[offset:offset+len(metadata)]=bytes(len(metadata));occupied.update(indices)
                    regions.append({'offset':offset,'length':len(metadata),'metadata_sha256':sha(metadata),'known_compiler_origins':origins})
                start=offset+len(metadata)
        return bytes(result),sorted(regions,key=lambda item:item['offset'])
    rows=[]
    for name in ('ZZZVault','ZZZMigration','ZZZCanonicalHandoff'):
        before,after=[bytes.fromhex(output['contracts']['src/'+name+'.sol'][name]['evm']['bytecode']['object']) for output in outputs]
        x,a=mask(before);y,b=mask(after)
        rows.append({'contract':name,'raw_creation_equal':before==after,'creation_equal_after_only_known_metadata_mask':x==y,
            'bytes_before':len(before),'bytes_after':len(after),'masked_sha256_before':sha(x),'masked_sha256_after':sha(y),
            'baseline_metadata_regions':a,'candidate_metadata_regions':b})
    report={'scope':'Read-only explanation of archived compiler creation-data differences; no compiler/test rerun, chain or service operation.',
        'observed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'script_sha256':sha(Path(__file__).read_bytes()),
        'artifact_sha256':{str(path):sha(path.read_bytes()) for path in paths},'comparisons':rows,
        'limits':['Only complete Solidity CBOR trailers independently extracted from saved compiler objects are masked; positions, lengths and provenance are recorded.',
            'The first compiler comparison removes terminal CBOR only. Vault/Migration creation each contains a second child metadata region; raw equality must not be claimed.',
            'Handoff remains different after metadata masking. Named constants changed its generated executable bytes; ABI/storage and static body correspondence alone are not a formal behavior proof.',
            'No immutable runtime addresses are populated by this comparison and no existing deployment is upgraded.']}
    destination.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps([{'contract':row['contract'],'creation_equal_after_only_known_metadata_mask':row['creation_equal_after_only_known_metadata_mask'],
                      'metadata_regions_before':len(row['baseline_metadata_regions']),'metadata_regions_after':len(row['candidate_metadata_regions'])} for row in rows],indent=2))


if __name__=='__main__':main()
