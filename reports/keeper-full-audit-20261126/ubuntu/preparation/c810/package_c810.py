"""Closed local c810 packager. No network, service, helper import or test execution.

Requires independently reviewed explicit worktree/helper hashes. HEAD blobs are
read directly; unrelated dirty/untracked files cannot enter the bundle.
"""
from pathlib import Path
import argparse
import ast
import gzip
import hashlib
import io
import json
import re
import subprocess
import tarfile

ROOT=Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
BASE=Path(__file__).resolve().parent
OLD=V/'ubuntu-complete-20261124/keeper-lp-jobs'
C804=V/'ubuntu-supervisor-20261125/body'
C808=V/'ubuntu-storage-20261125/c808'
HEAD='5331d3a5d051aad3da61d85aa43fafb870487f35'
STEM='popl-keeper-full-audit-20261126-c810'
LAB='/opt/'+STEM
FROZEN={'keeper_runtime.py':'f588d01b7593d39805a4df4b836976c10e2477313c570f5ede8e53276df6b6a4',
    'keeper_jobs.py':'363265dd9e026e7667c73baf1756e1959fbbd9a29d858c996686835b672c78d4',
    'job_cases.py':'7885a56f0b63db6fc73c42febcd8e7b9ea70a1e8eb4c031d0e1ec079f40146c7'}
APPROVED_OVERRIDE_PATHS={'keeper/monitor.py','keeper/staging.py','scripts/check-staging-monitor.py',
    'scripts/run-keeper-tests.py','scripts/verify.sh','zzz_ops/read_process.py','tests_python/test_read_process.py'}
ADDITIONS={'zzz_ops/read_process.py','tests_python/test_read_process.py'}
NEW_HELPERS={'model_service.py','restart_control.py','native_base.py'}
sha=lambda raw:hashlib.sha256(raw).hexdigest()
pin=lambda raw:{'bytes':len(raw),'sha256':sha(raw)}
enc=lambda value:(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()

def write(path,raw):
    if path.exists():
        assert path.read_bytes()==raw,'Refuse to overwrite a different prepared artifact: '+path.name
        return
    with path.open('xb')as stream:stream.write(raw)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--review-pins',type=Path,required=True);a=parser.parse_args()
    review=json.loads(a.review_pins.read_bytes())
    assert set(review)=={'source_head','source_overrides','helpers'}and review['source_head']==HEAD
    assert type(review['source_overrides'])is dict and ADDITIONS<=set(review['source_overrides'])<=APPROVED_OVERRIDE_PATHS
    assert set(review['helpers'])==NEW_HELPERS
    assert all(type(value)is str and re.fullmatch('[0-9a-f]{64}',value)
        for value in [*review['source_overrides'].values(),*review['helpers'].values()])
    actual=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,check=True).stdout.decode().strip()
    assert actual==HEAD,'Published base HEAD changed; explicitly review a new package'
    original_raw=(OLD/'c7f0.inputs.tar.gz').read_bytes()
    assert sha(original_raw)=='e1b14a9b883e3dba45e0ede5fc0ffe0efbee8e3e32ade16e6db21c0c0632694a'
    with tarfile.open(fileobj=io.BytesIO(original_raw),mode='r:gz')as archive:
        original={member.name:archive.extractfile(member).read()for member in archive if member.isfile()}
    prior=json.loads(original['MANIFEST.json'])
    for name,expected in prior['members'].items():assert pin(original[name])==expected
    members={name:raw for name,raw in original.items()if name.startswith('source/contracts/')or name.startswith('inputs/')}
    names=sorted(name for name in members if name.startswith('source/contracts/'));assert len(names)==190
    query=b''.join((HEAD+':'+name.removeprefix('source/contracts/')+'\n').encode()for name in names)
    data=subprocess.run(['git','cat-file','--batch'],input=query,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60,check=True).stdout
    offset=0;published={}
    for name in names:
        end=data.index(b'\n',offset);header=data[offset:end].split();assert len(header)==3 and header[1]==b'blob'
        size=int(header[2]);offset=end+1;published[name]=data[offset:offset+size];offset+=size+1;assert data[offset-1:offset]==b'\n'
    assert offset==len(data)
    current={};overrides=[]
    for name in names:
        relative=name.removeprefix('source/contracts/');baseline=published[name];raw=(ROOT/relative).read_bytes()
        if relative in review['source_overrides']:
            assert sha(raw)==review['source_overrides'][relative]and raw!=baseline,'Reviewed existing override differs'
            overrides.append({'path':relative,'published':pin(baseline),'current':pin(raw),'explicit_working_override':True})
        elif relative=='scripts/run-fork-checks.py':raw=baseline
        else:assert raw==baseline,'Unreviewed production worktree difference: '+relative
        members[name]=raw;current[relative]=pin(raw)
    for relative in sorted(ADDITIONS):
        assert relative not in current
        path=ROOT/relative;assert path.is_file()and not path.is_symlink()
        raw=path.read_bytes();assert sha(raw)==review['source_overrides'][relative]
        ast.parse(raw,filename=relative)
        members['source/contracts/'+relative]=raw;current[relative]=pin(raw)
        overrides.append({'path':relative,'published':None,'current':pin(raw),'explicit_working_addition':True})
    assert {row['path']for row in overrides}==set(review['source_overrides'])
    source={'schema':1,'source_head':HEAD,'byte_equal_to_base_HEAD':False,
        'frozen_F6_Solidity_modified':False,'unrelated_dirty_worktree_files_excluded':True,
        'production_baseline_members':190,'additional_read_process_and_selected_test_members':2,
        'approved_worktree_overrides':overrides,'members':current,
        'prior_source_manifest_sha256':sha(original['inputs/SOURCE_MANIFEST.json'])}
    members['inputs/SOURCE_MANIFEST.json']=enc(source);source_sha=sha(members['inputs/SOURCE_MANIFEST.json'])
    helpers={}
    for name in (*FROZEN,*sorted(NEW_HELPERS)):
        raw=(C804/name).read_bytes()if name in FROZEN else(BASE/name).read_bytes()
        assert sha(raw)==(FROZEN[name]if name in FROZEN else review['helpers'][name])
        ast.parse(raw,filename=name);helpers[name]=raw;members['source/helpers/'+name]=raw
    assert helpers['native_base.py']==(C804/'native_control.py').read_bytes()
    assert LAB.encode()in helpers['model_service.py']and LAB.encode()in helpers['restart_control.py']
    reused=(BASE/'C809_SELECTED_LINUX_TEST.json').read_bytes()
    assert len(reused)==610 and sha(reused)=='c577c2c51cb903cebbbf86fde5114f69d99b4c430c9575a90a2b493cab120645'
    members['inputs/C809_SELECTED_LINUX_TEST.json']=reused
    manifest={**{key:value for key,value in prior.items()if key!='members'},
        'scope':'NEW_native_restart_limit_and_idle_recovery_REUSE_prior_c809_Linux_pass_NO_test_bodies',
        'prior_source_head':prior.get('source_head'),'prior_source_manifest_sha256':prior.get('source_manifest_sha256'),
        'source_head':HEAD,'source_manifest_sha256':source_sha,
        'current_source_commit':HEAD,'approved_worktree_overrides':overrides,
        'stock_financial_jobs_enabled':False,'signed_stock_transactions_admitted':False,
        'lab_only_controlled_fees_not_target_fee_qualification':True,
        'members':{name:pin(raw)for name,raw in members.items()}}
    manifest_raw=enc(manifest);members['MANIFEST.json']=manifest_raw
    sink=io.BytesIO()
    with gzip.GzipFile(fileobj=sink,mode='wb',filename='',mtime=0)as compressed:
        with tarfile.open(fileobj=compressed,mode='w',format=tarfile.USTAR_FORMAT)as archive:
            for name,raw in sorted(members.items()):
                item=tarfile.TarInfo(name);item.size=len(raw);item.mode=0o444;item.uid=item.gid=0
                item.uname=item.gname='root';item.mtime=0;archive.addfile(item,io.BytesIO(raw))
    bundle=sink.getvalue();assert len(bundle)<=96*1024*1024
    write(BASE/'c810.inputs.tar.gz',bundle)
    # Reuse only the reviewed c808 fixed installer prefix, not its old worker,
    # standalone-unit actions, storage extension or command runner.
    controller=(C808/'remote_capsule.py').read_text().split('def runtime(a):',1)[0]
    controller=controller.replace('popl-ubuntu-storage-20261125-c808',STEM)
    def constant(name,value):
        nonlocal controller
        controller,count=re.subn(r'^'+name+r'=.*$',lambda _:name+'='+repr(value),controller,flags=re.M);assert count==1,name
    constant('UNIT',STEM+'-model.service')
    for name,value in {'BUNDLE_SHA':sha(bundle),'MANIFEST_SHA':sha(manifest_raw),
            'SOURCE_MANIFEST_SHA':source_sha,'WORKER_SHA':sha(helpers['model_service.py']),
            'UTILITY_SHA':FROZEN['keeper_jobs.py'],'INDEXER_SHA':FROZEN['job_cases.py'],
            'ALLOWED':tuple(sorted(members))}.items():constant(name,value)
    helper_check=r"^    for name,digest in .*:require\(sha\(data\['source/helpers/'\+name\]\)==digest,'Reviewed helper differs'\)$"
    controller,count=re.subn(helper_check,lambda _:'    for name,digest in '+repr(tuple((name,sha(raw))for name,raw in helpers.items()))+
        ":require(sha(data['source/helpers/'+name])==digest,'Reviewed helper differs')",controller,flags=re.M);assert count==1
    previous="    require(properties().get('LoadState')=='not-found','Owned unit name already exists')"
    replacement=previous+"\n    other=run(['/usr/bin/systemctl','show',"+repr(STEM+'-keeper.service')+",'--no-pager','--property=LoadState'])\n    require(other.stdout.decode('utf-8','strict').strip()=='LoadState=not-found','Owned keeper unit name already exists')"
    assert controller.count(previous)==1;controller=controller.replace(previous,replacement)
    public={}
    for name in ('READY','COMPLETE','RESULT','EVENTS','REUSED_LINUX_TEST'):
        public['model-'+name+'.json']=('model','model/'+name+'.json')
    for name in ('BINDINGS','BINDING_REFUSAL','CLOCK_REPAIR','INITIAL_JOURNAL','FINANCIAL_BEFORE',
            'HEALTHY_IDLE_CYCLE','FINANCIAL_AFTER','FINAL_JOURNAL','SETUP','RECEIPTS','RAW_REVIEWS','RESULT'):
        public['case-'+name+'.json']=('model','model/supervisor/'+name+'.json')
    for name in ('RATE_LIMIT_PROOF','REPAIR','FINAL_STOP'):public['native-'+name+'.json']=('control',name+'.json')
    for kind in ('model','keeper'):
        for stream in ('stdout','stderr'):public['native-'+kind+'.'+stream+'.log']=('model','native-'+kind+'.'+stream+'.log')
    constant('PUBLIC_PATHS',public)
    native_pins={'source_manifest_sha256':source_sha,'base_sha256':FROZEN['keeper_runtime.py'],
        'jobs_sha256':FROZEN['keeper_jobs.py'],'cases_sha256':FROZEN['job_cases.py'],
        'model_sha256':sha(helpers['model_service.py'])}
    extension=(BASE/'capsule_extension.py').read_text().replace('__NATIVE_PINS__',repr(native_pins)).replace(
        '__BASE_SHA__',repr(sha(helpers['native_base.py']))).replace('__CONTROL_SHA__',repr(sha(helpers['restart_control.py'])))
    controller+='\n'+extension;ast.parse(controller,filename='remote_capsule.py')
    write(BASE/'remote_capsule.py',controller.encode())
    host=(C808/'host_control.py').read_text().replace('ubuntu-storage-20261125/c808','keeper-full-audit-20261126/ubuntu/c810').replace('popl-ubuntu-storage-20261125-c808',STEM)
    host=host.replace("('validate-bundle','upload','install','start','status','stop','fetch')",
        "('validate-bundle','upload','install','start','startkeeper','status','prove','repair','stop','fetch')")
    # The host wrapper remains closed; only the fixed generated capsule is sent.
    ast.parse(host,filename='host_control.py');write(BASE/'host_control.py',host.encode())
    receipt={'schema':1,'lab':LAB,'feature':'native_restart_limit_recovery','bundle':pin(bundle),
        'manifest':pin(manifest_raw),'source_manifest_sha256':source_sha,'source_base':HEAD,
        'production_baseline_members':190,'additional_members':2,'approved_worktree_overrides':overrides,
        'helpers':{name:pin(raw)for name,raw in helpers.items()},'controller':pin(controller.encode()),
        'host_wrapper':pin(host.encode()),'local_packaging_only':True,'tests_run':0,'remote_actions':0,
        'limits':{'RPC_requests':6000,'seconds':900,'maintenance_gas':24000000,'padding_percent':25,
            'confirmations':12,'restart_seconds':30,'start_limit_burst':5,'start_limit_window_seconds':600,
            'watchdog_seconds':120,'stop_seconds':120,'maximum_stock_signed_sends':0}}
    write(BASE/'BUILD_RECEIPT.json',enc(receipt));write(BASE/'SOURCE_MANIFEST.json',members['inputs/SOURCE_MANIFEST.json'])
    print(json.dumps(receipt,sort_keys=True))

if __name__=='__main__':main()
