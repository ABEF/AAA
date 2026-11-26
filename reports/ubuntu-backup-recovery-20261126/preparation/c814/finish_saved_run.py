"""Collect the completed c814 after client interruption; no start/send actions."""
from pathlib import Path
import hashlib,json,re,subprocess,sys,time

BASE=Path(__file__).resolve().parent
HOST=BASE/'host_control.py'
sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    assert sha(HOST.read_bytes())=='60ba859d5b62df2b5b67e8759e25a71100c7ac71d4dc7553f632b3cb39168cb9'
    final=json.loads((BASE/'reconnect-final-status/PUBLIC_RESULT.json').read_bytes())
    stop=json.loads((BASE/'reconnect-stop-003/PUBLIC_RESULT.json').read_bytes())
    assert stop['all_owned_units_stopped'] is True
    assert all(not r['cgroup']['pids'] and r['properties']['MainPID']=='0'
        for r in stop['native_status']['units'].values())
    expected={'model-RESULT.json','model-COMPLETE.json','model-INDEPENDENT.json','case-FINANCIAL_FINAL.json'}
    assert expected<=set(final['public_files'])
    out=BASE/'reconnect-exports';out.mkdir(exist_ok=False)
    results={};actions=[];deadline=time.monotonic()+180
    for number,name in enumerate(sorted(final['public_files'])):
        if not name.endswith('.json'):continue
        assert re.fullmatch(r'[A-Za-z0-9_.-]+\.json',name)
        assert time.monotonic()+55<deadline
        folder=out/f'fetch-{number:03d}'
        stdout=out/f'{number:03d}.stdout';stderr=out/f'{number:03d}.stderr'
        argv=[sys.executable,'-B','-X','utf8',str(HOST),'fetch','--artifact',name,'--output',str(folder)]
        with stdout.open('xb')as o,stderr.open('xb')as e:
            process=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=o,stderr=e)
            start=time.monotonic()
            try:
                while process.poll()is None:
                    assert time.monotonic()-start<50
                    assert stdout.stat().st_size+stderr.stat().st_size<=65536
                    time.sleep(.1)
                process.wait(timeout=2)
            finally:
                if process.poll()is None:process.kill();process.wait(timeout=2)
        assert process.returncode==0
        receipt=json.loads((folder/'EXECUTION.json').read_bytes())
        assert receipt['exit_code']==0 and receipt['failed_capture_reason']is None
        raw=(folder/name).read_bytes();assert sha(raw)==receipt['artifact_sha256']
        results[name]=json.loads(raw)
        actions.append({'artifact':name,'sha256':sha(raw),'bytes':len(raw)})
    model=results['model-RESULT.json'];independent=results['model-INDEPENDENT.json']
    assert model['success']is True and model['final_financial_capture_complete']is True
    assert model['post_inclusion_financial_unchanged']is True and model['independent_private_review_passed']is True
    assert model['raw_attempts']==model['raw_forwarded']==1 and model['shared_RPC_requests']<=6000
    assert independent['success']is True and len(independent['checks'])==7
    assert all(row['passed']is True for row in independent['checks'])
    result={'schema':1,'success':True,'continuation_only':True,
        'original_client_orchestration_result_absent_after_session_interruption':True,
        'original_orchestration_files_rewritten':False,'original_server_scenario_restarted':False,
        'source_transactions_resubmitted':0,'new_server_tests_or_scenarios':0,
        'seven_independent_private_checks':True,'final_financial_vectors_saved_before_stop':True,
        'all_three_owned_groups_stopped':True,'actions':actions,
        'original_host_preservation_review_required':True,'production_approved':False,
        'shared_RPC_requests':model['shared_RPC_requests'],'checker_source_sha256':independent['verifier_sha256']}
    with(BASE/'CONTINUATION_RESULT.json').open('x',encoding='utf8')as f:
        json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps({'success':True,'saved_artifacts':len(actions),'shared_RPC_requests':model['shared_RPC_requests'],
        'private_checks':7,'all_owned_groups_stopped':True,'new_submissions':0}))


if __name__=='__main__':main()
