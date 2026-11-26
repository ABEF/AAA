"""Offline c823 review freeze; no payload, application import or remote action."""
from pathlib import Path
import ast,base64,hashlib,json,os,subprocess

ROOT=Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
BASE=Path(__file__).resolve().parent
HEAD='a1b1a5ab4f3f334305b34a4761952d5c215a3a96'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
pin=lambda raw:{'bytes':len(raw),'sha256':sha(raw)}


def git(*args):
    env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_CONFIG_NOSYSTEM='1')
    answer=subprocess.run(['git',*args],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=30)
    assert len(answer.stdout)<=8*1024*1024;return answer.stdout


def main():
    assert git('rev-parse','HEAD').decode().strip()==HEAD
    prepared={name:(BASE/name).read_bytes()for name in('build.py','worker.py','capsule_template.py','host_control.py')}
    for name,raw in prepared.items():ast.parse(raw,filename=name)
    legacy=ROOT/'reports/keeper-sidecar-recovery-20261126/preparation/c821/SOURCE_MANIFEST.json'
    raw=legacy.read_bytes();legacy_pin=sha(raw);assert legacy_pin=='c287aa0c4b8e4113f7ffa1459f39a704bd17b5165f23084e3a8f26995cdb0e08'
    source=json.loads(raw);verified={}
    for name,row in source['source_files'].items():
        data=git('show',HEAD+':'+name);assert pin(data)=={key:row[key]for key in('bytes','sha256')};verified[name]=sha(data)
    assert len(verified)==41
    for command in('scripts/keeper-recovery.py','scripts/keeper-sidecar-recovery.py','scripts/keeper-schedule.py'):
        assert command in verified
    assert len(source['dynamic_source_groups']['keeper/scheduling.py:SOURCE_FILES'])==19
    worker=prepared['worker.py'];controller=prepared['capsule_template.py'].decode()
    controller=controller.replace('__WORKER_BASE64__',repr(base64.b64encode(worker).decode('ascii')))
    controller=controller.replace('__WORKER_SHA__',repr(sha(worker))).encode()
    ast.parse(controller);assert len(controller)<=65536
    assert all((BASE/name).read_bytes()==raw for name,raw in prepared.items())
    with(BASE/'remote_capsule.py').open('xb')as stream:stream.write(controller)
    receipt={'schema':1,'source_head':HEAD,'worker':pin(worker),'controller':pin(controller),
        'host_wrapper':pin(prepared['host_control.py']),'reviewed_preparation':{name:pin(raw)for name,raw in prepared.items()},
        'original41_sources_match_current_HEAD':True,'source_files_sha256':verified,
        'original_source_manifest_sha256':legacy_pin,
        'original_source19_and_13_preserved':True,'production_source_changes':0,'old_test_bodies_run':0,
        'new_test_bodies_run':0,'server_actions':0,'raw_package_in_repository':False,
        'new_unit':'popl-keeper-offhost-20261126-c823.service',
        'actual_original_CLI_commands_planned':4,'original_operating_age_seconds':900,
        'new_unsigned_review_caller_max_age_seconds':86400,'clock_override':False,
        'limits':{'combined_stdout_stderr':65536,'import_wire_bytes':65536,'export_wire_bytes':65536,
            'worker_hard_start_seconds':180,'worker_soft_seconds':165,'per_original_tool_bytes':16777216,
            'per_original_tool_seconds':60,'public_result_bytes':32768,'desktop_proof_bytes':8192},
        'existing_environment_adoption':False,'production_approved':False}
    with(BASE/'BUILD_RECEIPT.json').open('x',encoding='utf8')as stream:json.dump(receipt,stream,indent=2,sort_keys=True);stream.write('\n')
    print(json.dumps({key:value for key,value in receipt.items()if key not in('source_files_sha256','reviewed_preparation')},sort_keys=True))


if __name__=='__main__':main()
