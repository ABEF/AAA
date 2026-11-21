"""Offline independent byte/source/network/cleanup check of the new fee archive."""
from pathlib import Path
import argparse,hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[3]
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);a=p.parse_args();assert not a.output.exists()
    folder=ROOT/'reports/pool-fees-20261121/run';manifest=json.loads((folder/'EVIDENCE_MANIFEST.json').read_bytes());raw=(folder/'evidence.zip').read_bytes()
    assert len(raw)==manifest['bytes']==10411086 and sha(raw)==manifest['sha256']=='13aa22d3dd99108d06d58a6aa96505a08b6a16c74e633e90b142bde826edb22b'
    sources={};network=[];cleanup=[]
    with zipfile.ZipFile(folder/'evidence.zip')as archive:
        names=archive.namelist();assert len(names)==len(set(names))==len(manifest['members'])==114 and set(names)==set(manifest['members'])
        for name,pin in manifest['members'].items():
            member=archive.read(name);assert len(member)==pin['bytes']and sha(member)==pin['sha256'],name
        for name in('run_fees.py','driver_base.py','warm_cache.py','eager_oracle.py'):
            source=(folder/name).read_bytes();assert source==archive.read('attempt2/source-'+name)==archive.read('tools/'+name);sources[name]=sha(source)
        name,=[n for n in names if n.endswith('/ORACLE_CONTROL.json')]
        control=json.loads(archive.read(name));assert control['passed']and control['source_sha256']==sources['eager_oracle.py']
        for part in('attempt1','attempt2'):
            summary=json.loads(archive.read(part+'/relay/summary.json'));rows=[json.loads(s)for s in archive.read(part+'/upstream-wire.jsonl').decode().splitlines()]
            for row in rows:
                assert row['http_status']==200
                assert sha(row['request_bytes_utf8'].encode())==row['request_sha256']and sha(row['response_bytes_utf8'].encode())==row['response_sha256']
            assert summary['upstream_attempts']==len(rows)and summary['retries']==0
            network.append({'stage':part,'public_reads':len(rows),'cache_hits':summary['cache_hits'],'local_rejections':summary['rejected_requests'],'all_public_HTTP200':True,'retries':0})
            closed=json.loads(archive.read(part+'/cleanup.json'));assert closed['owned_node_stopped']and closed['pending']is None
            cleanup.append({'stage':part,'pid':closed['pid'],'stopped':True,'pending':None})
    result={'schema':1,'passed':True,'source_sha256':sha(Path(__file__).read_bytes()),'archive_sha256':manifest['sha256'],'archive_bytes':len(raw),'unique_members_verified':114,'current_sources_match_successful_stage':sources,'oracle_counterexample_source_pin_matches':True,'network':network,'closed_nodes':cleanup,'EVM_or_network_calls':0,'production_approved':False}
    with a.output.open('x',encoding='utf8',newline='\n')as out:json.dump(result,out,indent=2);out.write('\n')
    print(json.dumps({'passed':True,'members':114,'public_reads':sum(x['public_reads']for x in network),'stopped_nodes':len(cleanup)}))
if __name__=='__main__':main()
