"""Offline c825 compile/freeze preparation; no imports of application code or SSH."""
from pathlib import Path
import ast,base64,hashlib,json,os,subprocess

ROOT=Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
BASE=Path(__file__).resolve().parent
HEAD='a418a567abbc3c0b7c6dd8425ef31306e8e48f17'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
pin=lambda raw:{'bytes':len(raw),'sha256':sha(raw)}


def git(*args):
    env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_CONFIG_NOSYSTEM='1')
    result=subprocess.run(['git',*args],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=30)
    assert len(result.stdout)<=2097152;return result.stdout


def main():
    assert git('rev-parse','HEAD').decode().strip()==HEAD
    prepared={name:(BASE/name).read_bytes()for name in('build.py','worker.py','capsule_template.py','host_control.py')}
    for name,raw in prepared.items():ast.parse(raw,filename=name)
    manifest_raw=(ROOT/'reports/keeper-sidecar-recovery-20261126/preparation/c821/SOURCE_MANIFEST.json').read_bytes()
    assert sha(manifest_raw)=='c287aa0c4b8e4113f7ffa1459f39a704bd17b5165f23084e3a8f26995cdb0e08'
    manifest=json.loads(manifest_raw);sources={}
    for name,row in manifest['source_files'].items():
        blob=git('show',HEAD+':'+name);expected={key:row[key]for key in('bytes','sha256')};assert pin(blob)==expected;sources[name]=expected
    assert len(sources)==41
    worker=prepared['worker.py'];controller=prepared['capsule_template.py'].decode()
    controller=controller.replace('__WORKER_BASE64__',repr(base64.b64encode(worker).decode('ascii')))
    controller=controller.replace('__WORKER_SHA__',repr(sha(worker))).replace('__SOURCE_PINS__',repr(sources)).encode()
    ast.parse(controller);assert len(controller)<=65536
    for name,raw in prepared.items():assert (BASE/name).read_bytes()==raw
    with(BASE/'remote_capsule.py').open('xb')as stream:stream.write(controller)
    receipt={'schema':1,'source_head':HEAD,'worker':pin(worker),'controller':pin(controller),'host_wrapper':pin(prepared['host_control.py']),
        'reviewed_preparation':{name:pin(raw)for name,raw in prepared.items()},'original41_sources_match_current_HEAD':True,
        'source_files':sources,'source_manifest_sha256':sha(manifest_raw),'original_source13_and_19_preserved':True,
        'production_source_changes':0,'old_test_bodies_run':0,'new_test_bodies_run':0,'server_actions':0,
        'raw_kit_in_repository':False,'native_CLI_calls_planned':5,'negative_native_refusal_planned':1,
        'positive_native_verify_restore_calls_planned':4,'original_operating_age_seconds':900,
        'unsigned_review_max_age_seconds':86400,'clock_override':False,'production_approved':False,
        'new_root':'/opt/popl-keeper-reconstruction-20261127-c825','RootDirectory_rebuilt_from_desktop_kit':True,
        'original_host_opt_bound':False,'external_OS_runtime_must_be_reviewed_before_install':True,
        'limits':{'combined_stdout_stderr':65536,'compressed_wire':2097152,'expanded_wire':2097152,
            'native_tool_bytes':16777216,'native_tool_seconds':60,'worker_hard_start_seconds':180,
            'worker_soft_seconds':165,'per_native_capture_bytes':65536,'runtime_inventory_bytes':134217728,
            'runtime_inventory_entries':8192,'runtime_inventory_depth':16,'runtime_inventory_seconds':20}}
    with(BASE/'BUILD_RECEIPT.json').open('x',encoding='utf8')as stream:json.dump(receipt,stream,indent=2,sort_keys=True);stream.write('\n')
    print(json.dumps({'controller':pin(controller),'worker':pin(worker),'host_wrapper':pin(prepared['host_control.py']),
        'offline_only':True,'server_actions':0,'native_calls':0},sort_keys=True))


if __name__=='__main__':main()
