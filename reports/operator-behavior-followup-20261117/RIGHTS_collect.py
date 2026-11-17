"""Collect exact isolated operator-rights evidence; no compilation/RPC/signing."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
DEST=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from zzz_ops.abi import keccak256

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--evidence-directory',type=Path,required=True)
args=parser.parse_args()
evidence=args.evidence_directory.resolve()
BASELINE='6945eeeba24304b8ddf27ac4c08fe55dc553554e'


def read(path):
    with path.open('rb') as stream:
        raw=stream.read(16*1024*1024+1)
    if len(raw)>16*1024*1024:raise ValueError('oversized bounded evidence input')
    return raw


def save(name,raw):
    with (DEST/name).open('xb') as stream:stream.write(raw)
    return {'path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


expected={
    'postfix-seal.json':3,
    'postfix-recovery-fuzz.json':1,
    'postfix-operator-fixture.json':1,
    'postfix-canonical-native.json':7,
}
final=[];identities=set();metadata_checks=[]
for filename,count in expected.items():
    raw=read(evidence/filename);obj=json.loads(raw.decode('utf-8-sig'))
    if not isinstance(obj,dict) or not obj:raise ValueError('missing selected test results')
    methods=[]
    for suite,result in obj.items():
        path,contract=suite.split(':',1)
        artifact=json.loads(read(evidence/'out'/Path(path).name/(contract+'.json')).decode('utf-8-sig'))
        metadata=artifact['metadata']
        hashes={};compiler_hashes={}
        for source,sourceinfo in metadata['sources'].items():
            location=(ROOT/source).resolve()
            if not location.is_relative_to(ROOT):raise ValueError('compiler source outside exact checkout')
            body=read(location)
            # Forge's Windows loader normalizes CRLF source text before passing
            # it to solc. Preserve raw bytes separately; only this explicit text
            # normalization may match the compiler's source-content commitment.
            compiler_body=body.decode('utf-8').replace('\r\n','\n').encode('utf-8')
            if '0x'+keccak256(compiler_body).hex()!=sourceinfo['keccak256']:
                raise ValueError('compiler metadata/source drift: '+source)
            hashes[source]=hashlib.sha256(body).hexdigest()
            compiler_hashes[source]=hashlib.sha256(compiler_body).hexdigest()
        metadata_checks.append({'suite':suite,'compiler':metadata['compiler'],
            'compiler_settings':metadata['settings'],
            'current_compiler_text_matches_metadata':True,'compiler_text_normalization':'UTF-8, CRLF replaced by LF',
            'raw_source_sha256':hashes,'compiler_source_content_sha256':compiler_hashes})
        for name,method in result['test_results'].items():
            identity=suite+'.'+name
            if method['status']!='Success' or identity in identities:raise ValueError('failed or duplicate final method')
            identities.add(identity)
            methods.append({'id':identity,'status':method['status'],'kind':method['kind']})
    if len(methods)!=count:raise ValueError('selected count differs')
    final.append({'original_name':filename,'artifact':save('RIGHTS-'+filename,raw),'methods':methods})

failures=[]
for filename,kind in (
    ('baseline.log','Actual missing-revert reproduction:2passes/1failure, overlap with final seal methods.'),
    ('postfix.json','Zero selected tests from attempted combined selector; no verification credit.'),
    ('postfix-canonical-fixture.json','Initial affected CanonicalPreparation setUp failed before its selected test body.'),
    ('canonical-fixture-failure-trace.log','Diagnostic rerun of the same setup failure, not another distinct finding.'),
):
    raw=read(evidence/filename)
    failures.append({'original_name':filename,'meaning':kind,'raw_bytes':len(raw),
        'raw_sha256':hashlib.sha256(raw).hexdigest(),
        'artifact':save('RIGHTS-'+filename.replace('.json','.log')+'.gz',gzip.compress(raw,mtime=0))})

original=subprocess.run(['git','show',BASELINE+':test/RoyaltyRecovery.t.sol'],cwd=ROOT,check=True,capture_output=True).stdout
begin=original.index(b'    function testFuzzRecoveredSourceClaimsNeverExceedFundedUnits')
end=original.find(b'    function ',begin+10)
weak=original[begin:end if end!=-1 else len(original)]
old_assertion=save('RIGHTS-original-recovery-method.txt',weak)
source={name:hashlib.sha256(read(ROOT/name)).hexdigest() for name in (
    'src/ZZZAccessController.sol','src/ZZZNFT.sol','src/ZZZRoyaltyRewards.sol',
    'src/ZZZCanonicalHandoff.sol','src/ZZZMigration.sol','src/base/ZZZCanonicalLedger.sol',
    'test/OperatorSealArtwork20261117.t.sol','test/RoyaltyRecovery.t.sol',
    'test/CanonicalPreparation.t.sol','test/OperatorControls.t.sol','test/mocks/Mocks.sol')}
manifest={'schema':1,'baseline_git':BASELINE,'release_approval':False,
    'production_change':'Access.seal rejects empty artworkBaseURI before erasing bootstrap; no ABI/storage/economic/permission changes',
    'final_unique_methods':len(identities),'new_seal_methods':3,'adapted_recovery_fuzz_methods':1,
    'adapted_fixture_methods':8,'fuzz_inputs':1000,
    'final_results':final,'failures_and_nonverification':failures,
    'original_weak_method':old_assertion,'source_sha256':source,
    'compiled_source_metadata_checks':metadata_checks,
    'limits':[
        'Final source bytes are reconciled to each selected contract compiler metadata; this is not compromised-host attestation.',
        'Baseline trace has real Access/NFT/Policy/factories and typed unused-module/VRF fixtures; no actual market/provider/operating qualification.',
        'Test-body seal gas includes graph construction and is not the public seal transaction gas.',
        'Canonical native venue is deterministic with explicit read-only execution identity; economic/rights modules stay real, but no actual Uniswap/market execution is established.',
        'Three new methods and nine affected methods were selected; no unchanged suite was rerun.',
        'Current-source normal size/static/default evidence is produced separately by the parent audit.',
        'No public RPC/transaction, existing deployment/seal, service/site/journal/heartbeat action.'
    ]}
save('RIGHTS_VERIFICATION.json',(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps({'unique_methods':len(identities),'fuzz_inputs':1000,'metadata_source_checks':len(metadata_checks),'release_approval':False}))
