"""PREPARATION ONLY: fixed safe c811 publication-copy, no server/test actions.

Root must review this source before explicitly invoking --copy-reviewed-evidence.
Every input is validated before a fresh report directory is created. Original
bytes are copied, never reserialized. No bundles, raw logs, secrets or signatures.
"""
from pathlib import Path
import argparse
import ast
import hashlib
import json
import re
import stat

ROOT=Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
BASE=V/'ubuntu-daemon-storage-20261126/c811'
RUN=BASE/'campaign-001'
DEST=ROOT/'reports/ubuntu-daemon-storage-20261126'
FROZEN=V/'ubuntu-supervisor-20261125/body'
HEAD='c07d5b153149f7c072ee5ff785c1cabac60197f6'
FROZEN_PINS={'keeper_runtime.py':'f588d01b7593d39805a4df4b836976c10e2477313c570f5ede8e53276df6b6a4',
    'keeper_jobs.py':'363265dd9e026e7667c73baf1756e1959fbbd9a29d858c996686835b672c78d4',
    'job_cases.py':'7885a56f0b63db6fc73c42febcd8e7b9ea70a1e8eb4c031d0e1ec079f40146c7'}
AUXILIARY_PINS={'capsule_extension.py':'1a7bf7d6299a2283017aea79981c70b07d5aae6629f9838f8d85dc7bdbb39a54',
    'package_c811.py':'c70ddd1b497d7428bbe3d8fc23260bf58e95ab9bc96c3890e859addae1077c82',
    'orchestrate_c811.py':'cc590a414d4344edf5fd6b9af8ae7315bbaf3641da6837d02bc7bddb7b189b40'}
SOURCE_NAMES=('model_service.py','storage_control.py','native_base.py','capsule_extension.py',
    'package_c811.py','remote_capsule.py','host_control.py','orchestrate_c811.py','curate_public.py')
ACTION_NAMES={'upload','install','start','startkeeper','status','stopkeeper','prove','repair','resolve','resume','stop','fetch'}
FORBIDDEN_KEYS={'privatekey','private_key','secretkey','secret_key','mnemonic','seed_phrase',
    'password','raw_transaction','rawtransaction','raw_signed_transaction','signed_transaction','signed_envelope'}
MAX_FILE=2*1024*1024
MAX_TOTAL=128*1024*1024
sha=lambda raw:hashlib.sha256(raw).hexdigest()
pin=lambda raw:{'bytes':len(raw),'sha256':sha(raw)}

def need(value,message):
    if not value:raise ValueError(message)

def checked(path,maximum=MAX_FILE):
    need(path.is_absolute()and not path.is_symlink(),'Fixed regular file required')
    item=path.stat();need(stat.S_ISREG(item.st_mode)and 0<item.st_size<=maximum,'Fixed input exceeds type/size bound')
    raw=path.read_bytes();again=path.stat()
    need((item.st_size,item.st_mtime_ns,item.st_ino)==(again.st_size,again.st_mtime_ns,again.st_ino)and len(raw)==item.st_size,'Fixed input changed during copy review')
    return raw

def pairs(values):
    result={}
    for key,value in values:
        need(key not in result,'Duplicate JSON key');result[key]=value
    return result

def public_json(raw):
    def constant(_):raise ValueError('Non-finite JSON value')
    value=json.loads(raw,object_pairs_hook=pairs,parse_constant=constant)
    def visit(node):
        if isinstance(node,dict):
            for key,child in node.items():
                need(key.lower()not in FORBIDDEN_KEYS,'Secret/signature field is not publishable');visit(child)
        elif isinstance(node,list):
            for child in node:visit(child)
        elif isinstance(node,str):
            need(not re.search(r'https?://[^/\s]+:[^/@\s]+@',node),'Credentialed endpoint is not publishable')
    visit(value);return value

def assignment(raw,name):
    values=[ast.literal_eval(node.value)for node in ast.parse(raw).body
        if isinstance(node,ast.Assign)and any(isinstance(target,ast.Name)and target.id==name for target in node.targets)]
    need(len(values)==1,'Expected one frozen source constant');return values[0]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--copy-reviewed-evidence',action='store_true',required=True)
    args=parser.parse_args();need(args.copy_reviewed_evidence,'Explicit root copy review required')
    need(BASE.resolve()==BASE and RUN.resolve()==RUN and DEST.parent.resolve()==ROOT/'reports','Fixed publication paths differ')
    need(not DEST.exists()and not DEST.is_symlink(),'Report destination must be new and unused')
    orchestration_raw=checked(RUN/'ORCHESTRATION_RESULT.json');run=public_json(orchestration_raw)
    need(run.get('success')is True and run.get('completed')is True and run.get('cleanup')is True and run.get('failure')is None,
        'Only a completed successful and fully stopped campaign may be curated')
    need(run.get('public_transactions')==run.get('new_seals')==run.get('old_test_bodies_run')==run.get('new_test_bodies_run')==0
        and run.get('new_composed_scenarios')==1,'Campaign permissions or scope differ')
    final=run.get('final_status',{});units=final.get('native',{}).get('units',{})
    need(set(units)=={'popl-ubuntu-daemon-storage-20261126-c811-'+kind+'.service'for kind in ('model','keeper','resolve')},'Final owned unit set differs')
    need(all(row['properties'].get('MainPID','0')=='0'and not row['cgroup']['pids']for row in units.values()),'Owned final groups are not empty')
    buildraw=checked(BASE/'BUILD_RECEIPT.json');build=public_json(buildraw)
    need(build.get('source_base')==HEAD and build.get('production_source_members')==191 and build.get('approved_worktree_overrides')==[],
        'Exact reviewed HEAD source required')
    parentraw=checked(BASE/'PARENT_REVIEW_PINS.json');parent=public_json(parentraw)
    need(set(parent)=={'c811.inputs.tar.gz','remote_capsule.py','host_control.py'},'Parent pin inventory differs')
    for name,digest in parent.items():need(sha(checked(BASE/name,96*1024*1024 if name.endswith('.tar.gz')else MAX_FILE))==digest,'Parent approved bytes changed')
    need(pin(checked(BASE/'remote_capsule.py'))==build['controller']and pin(checked(BASE/'host_control.py'))==build['host_wrapper'],'Build controller pins differ')
    source_raw=checked(BASE/'SOURCE_MANIFEST.json');source=public_json(source_raw)
    need(source['source_head']==HEAD and source['byte_equal_to_base_HEAD']is True and sha(source_raw)==build['source_manifest_sha256'],
        'Source manifest identity differs')
    candidate=public_json(checked(BASE/'CANDIDATE_REVIEW_PINS.json'))
    need(candidate.get('source_head')==HEAD and set(candidate.get('helpers',{}))=={'model_service.py','storage_control.py','native_base.py'},'Candidate helper review inventory differs')
    for name,digest in {**candidate['helpers'],**AUXILIARY_PINS}.items():
        need(sha(checked(BASE/name))==digest,'Reviewed helper or parent/preparation source changed')
    capsule_raw=checked(BASE/'remote_capsule.py');allowed=assignment(capsule_raw,'PUBLIC_PATHS')
    need(type(allowed)is dict and all(type(name)is str and '/'not in name and '\\'not in name for name in allowed),'Public artifact allowlist differs')
    files={};origins={}
    def add(relative,path,raw=None):
        need(type(relative)is str and not relative.startswith('/')and '..'not in Path(relative).parts,'Unsafe publication relative path')
        raw=checked(path)if raw is None else raw
        if relative.endswith('.json'):public_json(raw)
        if relative.endswith('.py'):ast.parse(raw,filename=relative)
        if relative in files:need(files[relative]==raw,'Duplicate publication filename has different content')
        else:files[relative]=raw;origins[relative]=str(path.relative_to(V))
        need(sum(len(value)for value in files.values())<=MAX_TOTAL,'Total publication copy bound exceeded')
    for name in ('BUILD_RECEIPT.json','SOURCE_MANIFEST.json','CANDIDATE_REVIEW_PINS.json','PARENT_REVIEW_PINS.json'):
        add('evidence/'+name,BASE/name)
    add('evidence/ORCHESTRATION_RESULT.json',RUN/'ORCHESTRATION_RESULT.json',orchestration_raw)
    add('evidence/PARENT_PREEXECUTION_APPROVAL.json',RUN/'PARENT_PREEXECUTION_APPROVAL.json')
    fetched={};seen_actions=set();statuses=[]
    for row in run['actions']:
        name=row.get('action')
        if name=='cleanup_observation':continue
        attempt=row.get('attempt');need(name in ACTION_NAMES and type(attempt)is int and 1<=attempt<=256,'Recorded action inventory differs')
        label=f'{name}-{attempt:03d}';need(label not in seen_actions,'Duplicate recorded action');seen_actions.add(label)
        folder=RUN/label;execution_raw=checked(folder/'EXECUTION.json');execution=public_json(execution_raw)
        need(execution.get('action')==name and execution.get('exit_code')==0 and execution.get('failed_capture_reason')is None,'Recorded bounded action failed')
        if name=='fetch':
            artifact=row.get('artifact');need(artifact in allowed and artifact.endswith('.json'),'Only allowlisted JSON artifacts may be published')
            raw=checked(folder/artifact);need(sha(raw)==execution.get('artifact_sha256'),'Fetched artifact capture hash differs')
            if artifact in fetched:need(fetched[artifact]==raw,'Repeated fetched filename content differs')
            else:fetched[artifact]=raw;add('evidence/fetched/'+artifact,folder/artifact,raw)
        elif name=='status':
            raw=checked(folder/'PUBLIC_RESULT.json');value=public_json(raw)
            statuses.append((folder/'PUBLIC_RESULT.json',raw,value))
        else:
            add('evidence/actions/'+label+'/EXECUTION.json',folder/'EXECUTION.json',execution_raw)
            add('evidence/actions/'+label+'/PUBLIC_RESULT.json',folder/'PUBLIC_RESULT.json')
    need(set(run['exports'])==set(fetched),'Final export inventory differs from exact captured files')
    model=public_json(fetched['model-RESULT.json'])
    need(model.get('success')is True and model.get('raw_attempts')==model.get('raw_forwarded')==1
        and model.get('shared_RPC_requests',6001)<=6000,'Completed model accounting or send count differs')
    # Retain every action's statistics above, but publish only semantic status
    # boundaries. The complete unchanged polling/capture stream stays private.
    keeper='popl-ubuntu-daemon-storage-20261126-c811-keeper.service'
    def active(value):return int(value['native']['units'][keeper]['properties'].get('MainPID','0'))>1
    def empty(value):
        row=value['native']['units'][keeper]
        return row['properties'].get('MainPID','0')=='0'and not row['cgroup']['pids']
    rules={
        '01-model-ready':lambda v:'model-READY.json'in v['public_files'],
        '02-original-natural-EACCES-exit':lambda v:v.get('original_failure_complete')is True and empty(v),
        '03-hashless-restart-blocked-active':lambda v:'case-HASHLESS_RESTART_BLOCKED.json'in v['public_files']and active(v),
        '04-hashless-restart-fenced':lambda v:'case-HASHLESS_RESTART_BLOCKED.json'in v['public_files']and empty(v),
        '05-original-confirmations-ready':lambda v:'case-RESOLUTION_READY.json'in v['public_files'],
        '06-fresh-healthy-complete-active':lambda v:'model-COMPLETE.json'in v['public_files']and active(v),
    }
    for name,predicate in rules.items():
        candidates=[row for row in statuses if predicate(row[2])]
        need(candidates,'Required semantic status boundary absent: '+name)
        path,raw,_=candidates[0];add('evidence/semantic-status/'+name+'.json',path,raw)
    need(statuses,'Final status capture absent')
    path,raw,value=statuses[-1]
    need(all(row['properties'].get('MainPID','0')=='0'and not row['cgroup']['pids']for row in value['native']['units'].values()),'Last captured status has a live owned group')
    add('evidence/semantic-status/07-final-all-groups-empty.json',path,raw)
    for name in SOURCE_NAMES:add('preparation/c811/'+name,BASE/name)
    for name,digest in FROZEN_PINS.items():
        raw=checked(FROZEN/name);need(sha(raw)==digest,'Frozen original helper changed');add('preparation/shared/'+name,FROZEN/name,raw)
    for name in ('model_service.py','storage_control.py','native_base.py'):
        need(pin(files['preparation/c811/'+name])==build['helpers'][name],'Curated executed helper differs')
    review=BASE.parent/'review'
    for name in ('verify_saved_vectors.py','SEMANTIC_REVIEW.md','INDEPENDENT_C811.json'):
        path=review/name
        if path.exists():add('independent/'+name,path)
    manifest={'schema':1,'scope':'Exact-byte safe c811 evidence and preparation source publication only',
        'source_head':HEAD,'campaign_success':True,'all_three_owned_groups_empty':True,
        'public_transactions':0,'new_seals':0,'unchanged_test_bodies_run':0,
        'bundle_retained_privately_not_published':True,'raw_logs_credentials_and_signed_envelopes_excluded':True,
        'host_baseline_and_independent_release_approval_not_inferred':True,
        'files':{name:{**pin(raw),'original_private_relative_path':origins[name]}for name,raw in sorted(files.items())}}
    manifest_raw=(json.dumps(manifest,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
    # All validation finished. Never replace/delete an existing destination.
    DEST.mkdir(mode=0o755)
    for relative,raw in sorted(files.items()):
        path=DEST/relative;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb')as stream:stream.write(raw)
        need(path.read_bytes()==raw,'Published copy differs from original bytes')
    with (DEST/'CURATION_MANIFEST.json').open('xb')as stream:stream.write(manifest_raw)
    print(json.dumps({'success':True,'destination':str(DEST),'files':len(files)+1,
        'source_artifacts_exact':True,'network_actions':0,'tests_run':0,'existing_files_replaced':0},sort_keys=True))

if __name__=='__main__':main()
