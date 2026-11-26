"""Offline fixed c811 packager: HEAD blobs, reviewed helpers, no remote action.

No unchanged tests are executed. Dirty worktree source is never packaged.
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
C804=V/'ubuntu-supervisor-20261125/body'
C806=V/'ubuntu-supervisor-20261125/signer'
C808=V/'ubuntu-storage-20261125/c808'
OLD=V/'ubuntu-complete-20261124/keeper-lp-jobs'
HEAD='c07d5b153149f7c072ee5ff785c1cabac60197f6'
STEM='popl-ubuntu-daemon-storage-20261126-c811'
LAB='/opt/'+STEM
FROZEN={'keeper_runtime.py':'f588d01b7593d39805a4df4b836976c10e2477313c570f5ede8e53276df6b6a4',
    'keeper_jobs.py':'363265dd9e026e7667c73baf1756e1959fbbd9a29d858c996686835b672c78d4',
    'job_cases.py':'7885a56f0b63db6fc73c42febcd8e7b9ea70a1e8eb4c031d0e1ec079f40146c7'}
NEW_HELPERS={'model_service.py','storage_control.py','native_base.py'}
sha=lambda raw:hashlib.sha256(raw).hexdigest()
pin=lambda raw:{'bytes':len(raw),'sha256':sha(raw)}
enc=lambda value:(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()

def write(path,raw):
    if path.exists():
        assert path.read_bytes()==raw,'Different prepared artifact already exists: '+path.name
        return
    with path.open('xb')as stream:stream.write(raw)

def main():
    p=argparse.ArgumentParser();p.add_argument('--review-pins',type=Path,required=True);a=p.parse_args()
    review=json.loads(a.review_pins.read_bytes())
    assert set(review)=={'source_head','helpers'}and review['source_head']==HEAD and set(review['helpers'])==NEW_HELPERS
    assert all(type(value)is str and re.fullmatch('[0-9a-f]{64}',value)for value in review['helpers'].values())
    actual=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,check=True).stdout.decode().strip()
    assert actual==HEAD,'Published HEAD changed; review a new package'
    original_raw=(OLD/'c7f0.inputs.tar.gz').read_bytes()
    assert sha(original_raw)=='e1b14a9b883e3dba45e0ede5fc0ffe0efbee8e3e32ade16e6db21c0c0632694a'
    with tarfile.open(fileobj=io.BytesIO(original_raw),mode='r:gz')as archive:
        original={member.name:archive.extractfile(member).read()for member in archive if member.isfile()}
    prior=json.loads(original['MANIFEST.json'])
    for name,expected in prior['members'].items():assert pin(original[name])==expected
    members={name:raw for name,raw in original.items()if name.startswith('source/contracts/')or name.startswith('inputs/')}
    names=sorted(name for name in members if name.startswith('source/contracts/'));assert len(names)==190
    names=sorted([*names,'source/contracts/zzz_ops/read_process.py'])
    query=b''.join((HEAD+':'+name.removeprefix('source/contracts/')+'\n').encode()for name in names)
    data=subprocess.run(['git','cat-file','--batch'],input=query,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60,check=True).stdout
    offset=0;current={}
    for name in names:
        end=data.index(b'\n',offset);header=data[offset:end].split();assert len(header)==3 and header[1]==b'blob'
        size=int(header[2]);offset=end+1;raw=data[offset:offset+size];offset+=size+1;assert data[offset-1:offset]==b'\n'
        members[name]=raw;current[name.removeprefix('source/contracts/')]=pin(raw)
    assert offset==len(data)and len(current)==191
    assert current['keeper/monitor.py']['sha256']=='90e49e17ad770a9e7136e06d4dfabdcc43280815ba3540c5a5197a8cba42463f'
    source={'schema':1,'source_head':HEAD,'byte_equal_to_base_HEAD':True,'frozen_F6_Solidity_modified':False,
        'unrelated_dirty_worktree_files_excluded':True,'production_baseline_members':190,'additional_read_process_members':1,
        'approved_worktree_overrides':[],'members':current,'prior_source_manifest_sha256':sha(original['inputs/SOURCE_MANIFEST.json'])}
    members['inputs/SOURCE_MANIFEST.json']=enc(source);source_sha=sha(members['inputs/SOURCE_MANIFEST.json'])
    helpers={}
    for name in (*FROZEN,*sorted(NEW_HELPERS)):
        raw=(C804/name).read_bytes()if name in FROZEN else(BASE/name).read_bytes()
        assert sha(raw)==(FROZEN[name]if name in FROZEN else review['helpers'][name])
        ast.parse(raw,filename=name);helpers[name]=raw;members['source/helpers/'+name]=raw
    assert helpers['native_base.py']==(C806/'native_control.py').read_bytes()
    assert LAB.encode()in helpers['model_service.py']and LAB.encode()in helpers['storage_control.py']
    manifest={**{key:value for key,value in prior.items()if key!='members'},
        'scope':'NEW_full_stock_daemon_actual_hash_save_EACCES_same_journal_restart_resolution_recovery',
        'prior_source_head':prior.get('source_head'),'prior_source_manifest_sha256':prior.get('source_manifest_sha256'),
        'source_head':HEAD,'source_manifest_sha256':source_sha,'current_source_commit':HEAD,
        'approved_worktree_overrides':[],'stock_financial_jobs_enabled':True,'signed_stock_transactions_admitted':True,
        'maximum_stock_signed_transactions':1,'lab_only_controlled_fees_not_target_fee_qualification':True,
        'members':{name:pin(raw)for name,raw in members.items()}}
    manifest_raw=enc(manifest);members['MANIFEST.json']=manifest_raw;sink=io.BytesIO()
    with gzip.GzipFile(fileobj=sink,mode='wb',filename='',mtime=0)as compressed:
        with tarfile.open(fileobj=compressed,mode='w',format=tarfile.USTAR_FORMAT)as archive:
            for name,raw in sorted(members.items()):
                item=tarfile.TarInfo(name);item.size=len(raw);item.mode=0o444;item.uid=item.gid=0;item.uname=item.gname='root';item.mtime=0
                archive.addfile(item,io.BytesIO(raw))
    bundle=sink.getvalue();assert len(bundle)<=96*1024*1024;write(BASE/'c811.inputs.tar.gz',bundle)
    controller=(C808/'remote_capsule.py').read_text().split('def runtime(a):',1)[0]
    controller=controller.replace('popl-ubuntu-storage-20261125-c808',STEM)
    def constant(name,value):
        nonlocal controller
        controller,count=re.subn(r'^'+name+r'=.*$',lambda _:name+'='+repr(value),controller,flags=re.M);assert count==1,name
    constant('UNIT',STEM+'-model.service')
    for name,value in {'BUNDLE_SHA':sha(bundle),'MANIFEST_SHA':sha(manifest_raw),'SOURCE_MANIFEST_SHA':source_sha,
            'WORKER_SHA':sha(helpers['model_service.py']),'UTILITY_SHA':FROZEN['keeper_jobs.py'],'INDEXER_SHA':FROZEN['job_cases.py'],
            'ALLOWED':tuple(sorted(members))}.items():constant(name,value)
    helper_check=r"^    for name,digest in .*:require\(sha\(data\['source/helpers/'\+name\]\)==digest,'Reviewed helper differs'\)$"
    controller,count=re.subn(helper_check,lambda _:'    for name,digest in '+repr(tuple((name,sha(raw))for name,raw in helpers.items()))+
        ":require(sha(data['source/helpers/'+name])==digest,'Reviewed helper differs')",controller,flags=re.M);assert count==1
    previous="    require(properties().get('LoadState')=='not-found','Owned unit name already exists')"
    replacement=previous
    for kind in ('keeper','resolve'):
        replacement+="\n    other=run(['/usr/bin/systemctl','show',"+repr(STEM+'-'+kind+'.service')+",'--no-pager','--property=LoadState'])\n    require(other.stdout.decode('utf-8','strict').strip()=='LoadState=not-found','Owned "+kind+" unit name already exists')"
    assert controller.count(previous)==1;controller=controller.replace(previous,replacement)
    public={}
    for name in ('READY','COMPLETE','RESULT','EVENTS'):public['model-'+name+'.json']=('model','model/'+name+'.json')
    for name in ('BINDINGS','BINDING_REFUSAL','CLOCK_REPAIR','INITIAL_JOURNAL','FINANCIAL_BEFORE','HASH_SAVE_FAULT_ARMED',
            'HASHLESS_RESTART_BLOCKED','RESOLUTION_READY','POST_RESOLUTION_MINING','RECOVERED_JOURNAL','RECOVERY_REFRESH_HEALTH',
            'HEALTHY_NORMAL_CYCLE','HEALTHY_JOURNAL','HEALTHY_TIMING','FINANCIAL_AFTER',
            'FINAL_JOURNAL','SETUP','RECEIPTS','RAW_REVIEWS','RESULT'):
        public['case-'+name+'.json']=('model','model/supervisor/'+name+'.json')
    for name in ('FAULT_PROOF','REPAIR','RESOLUTION_RECEIPT','RESOLUTION_COMPLETE','RESUME','FINAL_STOP'):public['native-'+name+'.json']=('control',name+'.json')
    for kind in ('model','keeper','resolve'):
        for stream in ('stdout','stderr'):public['native-'+kind+'.'+stream+'.log']=('model','native-'+kind+'.'+stream+'.log')
    constant('PUBLIC_PATHS',public)
    native_pins={'source_manifest_sha256':source_sha,'base_sha256':FROZEN['keeper_runtime.py'],
        'jobs_sha256':FROZEN['keeper_jobs.py'],'cases_sha256':FROZEN['job_cases.py'],'model_sha256':sha(helpers['model_service.py'])}
    extension=(BASE/'capsule_extension.py').read_text().replace('__NATIVE_PINS__',repr(native_pins)).replace(
        '__BASE_SHA__',repr(sha(helpers['native_base.py']))).replace('__CONTROL_SHA__',repr(sha(helpers['storage_control.py'])))
    controller+='\n'+extension;ast.parse(controller,filename='remote_capsule.py');write(BASE/'remote_capsule.py',controller.encode())
    host=(C808/'host_control.py').read_text().replace('ubuntu-storage-20261125/c808','ubuntu-daemon-storage-20261126/c811').replace('popl-ubuntu-storage-20261125-c808',STEM)
    host=host.replace("('validate-bundle','upload','install','start','status','stop','fetch')",
        "('validate-bundle','upload','install','start','startkeeper','status','stopkeeper','prove','repair','resolve','resume','stop','fetch')")
    ast.parse(host,filename='host_control.py');write(BASE/'host_control.py',host.encode())
    receipt={'schema':1,'lab':LAB,'feature':'actual_hash_save_EACCES_full_daemon_restart_recovery','bundle':pin(bundle),
        'manifest':pin(manifest_raw),'source_manifest_sha256':source_sha,'source_base':HEAD,'production_source_members':191,
        'approved_worktree_overrides':[],'helpers':{name:pin(raw)for name,raw in helpers.items()},'controller':pin(controller.encode()),
        'host_wrapper':pin(host.encode()),'local_packaging_only':True,'tests_run':0,'remote_actions':0,
        'limits':{'RPC_requests':6000,'seconds':900,'maintenance_gas':24000000,'padding_percent':25,
            'confirmations':12,'poll_seconds':240,'harvest_seconds':3600,'restart_seconds':30,
            'watchdog_seconds':120,'stop_seconds':120,'maximum_stock_signed_sends':1}}
    write(BASE/'BUILD_RECEIPT.json',enc(receipt));write(BASE/'SOURCE_MANIFEST.json',members['inputs/SOURCE_MANIFEST.json'])
    print(json.dumps(receipt,sort_keys=True))

if __name__=='__main__':main()
