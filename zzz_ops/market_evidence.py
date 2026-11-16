"""Offline semantic closure for the dated 2026-11-16 market capture.

This is deliberately a single historical evidence schema, not a live-market
admission tool. It never loads code from the archive, calls RPC, or approves a
feed, route, provider, price policy, deployment, or operating budget. Manifest
hashes establish internal integrity; provider truth is outside this checker.
"""
from __future__ import annotations

import datetime as dt
from decimal import Decimal, localcontext
from fractions import Fraction
import gzip
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile
import zlib

from zzz_ops.abi import keccak256


SCHEMA = 'real-market-refresh-20261116/v2-semantic-closure'
ZERO = '0x'+'0'*40
ZZZ = '0x7dbf38976f6d3b9c529e7d9484a71898b409ee6a'
SELECTED = '0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b'
ENDPOINT = 'https://robinhood.rpc.pinax.network'
GENESIS = '0xaad15f3d702aaea00caf3e9bb56395efe9127bc3b31b24921abf1eee3409305c'
SLOT = '0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc'
ETH_ID = '0xff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace'
MAX_MEMBER = 2*1024*1024
MAX_TOTAL = 20*1024*1024
SAFEGUARDS = {'additional_loss_bps':100,'contribution_total_bps':300,
    'conversion_total_bps':100,'maintenance_bps':300,
    'minimum_marginal_lp_bps':9700,'source_agreement_bps':300}
PROVENANCE = {
    'provenance/Nov13-CAPTURE.json.gz':'18963b05858fec8195101999ba56d40557d82a0448e06973d7bc10a72bb8f987',
    'provenance/known95-Nov9.json':'35e990f33b83c00cf37e0d6da8c586ce5aed73f89d94281fa83b74a5c320caf8',
    'provenance/Nov9-discovery.json':'af98d09c604bdf09a97445b5410e0025d32e0aadc2f84727e2e897a478cbd04d'}
ANALYTICAL_SCOPE = 'Owninitialspot only; not two-sourceUSD, configuredvenue/userfloor, LPdeployment or finalsourceagreement.'
LIMITS = [
    'No PoPL deployment: no wholeactivation/growth/maintenance/claim operation simulated.',
    'Nominal100/5USD ETH quotes are fullinput diagnostics, not assumed protocol swap fractions.',
    'Positive quoter responses provide output/gas only, not postspot/fullstate.',
    'ActiveL0 does not prove emptyticks; rawL ranking does not proveTVL/depth/sourceindependence.',
    'API3 current base/subscription not read. No Pyth publication/update/funding performed.',
    'Oracle sourceage/depth/reviewIDs/routes/operating fees remain unapproved.']
BLOCKERS = ['No twoqualifiedindependentETH/ZZZsources',
    'SelectedactiveL0; largestknownreferencepricebandincompatiblewithselecteddestination',
    'No testedcomplete1000ZZZreverse/default1%conversion',
    'Route/source/depth/ages/operations mustbe reviewed; no generated values adopted']


def require(ok, message):
    if not ok:
        raise ValueError(message)


def same(actual, expected, label):
    """Canonical JSON comparison keeps booleans distinct from integer aliases."""
    require(json.dumps(actual,sort_keys=True,separators=(',',':'),allow_nan=False)
        == json.dumps(expected,sort_keys=True,separators=(',',':'),allow_nan=False),label)


def number(value, lo=0, hi=(1<<256)-1):
    require(type(value) is int and lo <= value <= hi,'Invalid bounded evidence integer')
    return value


def elapsed(value):
    require(type(value) in (int,float) and math.isfinite(value) and 0 <= value <= 90,
        'Invalid elapsed time')
    return value


def strict_json(raw):
    require(type(raw) is bytes and len(raw)<=MAX_MEMBER,'Oversized JSON member')
    def pairs(items):
        out={}
        for key,value in items:
            require(key not in out,'Duplicate JSON field')
            out[key]=value
        return out
    def constant(_):
        raise ValueError('Nonfinite JSON value')
    def integer(value):
        require(len(value.lstrip('-'))<=78,'Oversized JSON integer')
        return int(value)
    def floating(value):
        out=float(value)
        require(math.isfinite(out),'Nonfinite JSON value')
        return out
    try:
        return json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,
            parse_constant=constant,parse_int=integer,parse_float=floating)
    except (UnicodeError,json.JSONDecodeError,RecursionError) as exc:
        raise ValueError('Invalid evidence JSON') from exc


def safe_name(name):
    require(type(name) is str and 0<len(name)<=240 and name.isascii()
        and '\\' not in name and ':' not in name and '\x00' not in name
        and not PurePosixPath(name).is_absolute()
        and all(part not in ('','.', '..') for part in name.split('/')),
        'Unsafe evidence member path')
    return name


class Archive:
    """Read only a bounded ZIP; never extract paths or execute archived code."""
    def __init__(self, path):
        self.path=Path(path)
        require(self.path.is_file() and self.path.stat().st_size<=MAX_TOTAL,
            'Evidence must be a bounded ZIP file')
        try:
            with zipfile.ZipFile(self.path) as archive:
                entries=archive.infolist()
                require(0<len(entries)<=512,'Unbounded ZIP inventory')
                names=[safe_name(row.filename) for row in entries]
                require(len(set(names))==len(names),'Duplicate ZIP member')
                require(sum(row.file_size for row in entries)<=MAX_TOTAL,
                    'Unbounded ZIP contents')
                self.files={}
                for row in entries:
                    mode=row.external_attr>>16
                    require(not row.is_dir() and not stat.S_ISLNK(mode)
                        and not row.flag_bits&1 and 0<=row.file_size<=MAX_MEMBER,
                        'Unsafe or oversized ZIP member')
                    with archive.open(row) as stream:
                        raw=stream.read(MAX_MEMBER+1)
                    require(len(raw)==row.file_size<=MAX_MEMBER,'ZIP size mismatch')
                    self.files[row.filename]=raw
        except (zipfile.BadZipFile,RuntimeError,NotImplementedError,OSError,zlib.error) as exc:
            raise ValueError('Invalid evidence ZIP') from exc
        manifest=self.obj('manifest.json')
        require(type(manifest) is dict and type(manifest.get('files')) is list,
            'Missing evidence manifest')
        same({k:v for k,v in manifest.items() if k!='files'},
            {'schema':1,'revision':2,'source_baseline':'0b31f3300d85d1a8ea86e958759a97a006c5b67f',
             'production_approved':False,
             'supersedes_zip_sha256':'bd226ed658c67aa169985e5bde45ad5ad1363b2cc4ff8169196bed6005b651d0'},
            'Wrong dated manifest schema')
        paths=[]
        for row in manifest['files']:
            require(type(row) is dict and set(row)=={'path','bytes','sha256'},
                'Invalid manifest row')
            name=safe_name(row['path']);paths.append(name);raw=self.raw(name)
            require(number(row['bytes'],0,MAX_MEMBER)==len(raw)
                and type(row['sha256']) is str and re.fullmatch('[0-9a-f]{64}',row['sha256'])
                and hashlib.sha256(raw).hexdigest()==row['sha256'],'Evidence hash mismatch')
        require(len(paths)==len(set(paths)) and set(paths)==set(self.files)-{'manifest.json'},
            'Detached or duplicate manifest inventory')
        self.member_count=len(paths)

    def raw(self,name):
        require(safe_name(name) in self.files,'Missing evidence member')
        return self.files[name]

    def obj(self,name):
        return strict_json(self.raw(name))


def words(raw, count=None):
    require(type(raw) is str and len(raw)<=2+64*512
        and re.fullmatch(r'0x(?:[0-9a-f]{64})*',raw),'Invalid static ABI')
    out=[int(raw[i:i+64],16) for i in range(2,len(raw),64)]
    require(count is None or len(out)==count,'Unexpected static ABI length')
    return out


def word(value):
    if type(value) is str:
        require(re.fullmatch(r'0x[0-9a-f]{1,64}',value),'Invalid ABI identity')
        value=int(value,16)
    require(type(value) is int and -(1<<255)<=value<1<<256,'Invalid ABI integer')
    return (value%(1<<256)).to_bytes(32,'big')


def digest(raw):
    return '0x'+keccak256(raw).hex()


def ratio(value):
    with localcontext() as ctx:
        ctx.prec=90
        decimal=format(Decimal(value.numerator)/Decimal(value.denominator),'.24f')
    return {'numerator':str(value.numerator),'denominator':str(value.denominator),
        'decimal':decimal}


def selector(signature):
    return keccak256(signature.encode())[:4]


def _request(row,method,params):
    same(row['request'],{'jsonrpc':'2.0','id':row['request']['id'],'method':method,'params':params},
        'Wire request identity differs')


def _call(row,target,data,block):
    _request(row,'eth_call',[{'to':target,'data':data,'gas':hex(500000)},block])


def _wire(row):
    response=row['response']
    return response['result'] if 'result' in response else {'rpc_error':response['error']}


def _logs(e,phase,count):
    log=e.obj(phase+'/RPC.json')
    require(type(log) is dict,'Invalid transport record')
    interval_key='actual_start_interval_seconds' if phase=='capture' else 'interval_seconds'
    same({k:v for k,v in log.items() if k!='rows'},
        {interval_key:2,'endpoint':ENDPOINT,'maximum_calls':count,
         'maximum_response_bytes':262144,'maximum_seconds':90,'read_only':True,'retries':0},
        'Wrong captured transport policy')
    require(type(log['rows']) is list and len(log['rows'])==count,'Wrong request count')
    last_start=-2;last_end=0
    for index,row in enumerate(log['rows'],1):
        require(type(row) is dict,'Invalid request row')
        number(row['http_status'],200,200)
        if phase=='capture':
            number(row['id'],index,index)
        raw=e.raw(phase+'/'+safe_name(row['raw_file']))
        require(len(raw)<=262144 and hashlib.sha256(raw).hexdigest()==row['raw_sha256'],
            'Raw response differs')
        if phase=='capture':
            require(len(raw)==number(row['raw_bytes'],0,262144),'Recorded raw response size differs')
        same(strict_json(raw),row['response'],'Parsed response differs from wire')
        response=row['response'];request=row['request']
        require(type(response) is dict and response.get('jsonrpc')=='2.0'
            and set(response) in ({'jsonrpc','id','result'},{'jsonrpc','id','error'}),
            'Invalid JSON-RPC envelope')
        number(response['id'],index,index);number(request['id'],index,index)
        require(type(request) is dict and set(request)=={'jsonrpc','id','method','params'}
            and request['jsonrpc']=='2.0','Invalid request envelope')
        start=elapsed(row['started_elapsed_seconds']);end=elapsed(row['finished_elapsed_seconds'])
        require(start>=last_end and start-last_start>=2 and end>=start,
            'Serialized HTTP pacing/time boundary differs')
        require(type(row['timeout_seconds']) in (int,float)
            and math.isfinite(row['timeout_seconds']) and 0<row['timeout_seconds']<=min(12,90-start),
            'Request timeout exceeds captured budget')
        last_start,last_end=start,end
    labels=[r['label'] for r in log['rows']]
    require(all(type(label) is str for label in labels) and len(labels)==len(set(labels)),
        'Duplicate request label')
    return log,{row['label']:row for row in log['rows']}


def _runtime(row,pin,prior,block):
    _request(row,'eth_getCode',[pin['address'],block])
    raw=_wire(row)
    require(type(raw) is str and re.fullmatch(r'0x(?:[0-9a-f]{2})+',raw),'Invalid runtime')
    code=bytes.fromhex(raw[2:]);expected=prior['keccak256']
    same(pin,{'address':prior['address'],'bytes':len(code),'keccak256':digest(code),
        'expected_prior_keccak256':expected,'matches_prior_runtime':True},
        'Runtime pin/identity differs')
    require(digest(code)==expected,'Runtime changed from reviewed provenance')


def _fee(pool,direction):
    packed=pool['slot0']['protocolFee']
    protocol=packed&4095 if direction else packed>>12
    lp=pool['slot0']['lpFee']
    number(protocol,0,1000);number(lp,0,999999)
    return protocol+lp-protocol*lp//1000000


def _error(raw,pool_id):
    require(type(raw) is dict and set(raw)=={'rpc_error'},'Invalid quote error')
    error=raw['rpc_error']
    require(type(error) is dict and set(error)=={'code','data','message'}
        and type(error['code']) is int and type(error['message']) is str,
        'Invalid RPC error')
    data=error['data']
    require(type(data) is str and re.fullmatch(r'0x(?:[0-9a-f]{2})*',data),
        'Invalid error bytes')
    b=bytes.fromhex(data[2:])
    require(len(b)>=68 and b[:4]==selector('UnexpectedRevertBytes(bytes)')
        and int.from_bytes(b[4:36],'big')==32,'Unrecognized quote error wrapper')
    length=int.from_bytes(b[36:68],'big')
    require(length in (0,36) and len(b)==68+((length+31)//32)*32
        and not any(b[68+length:]),'Malformed quote error')
    inner=b[68:68+length]
    if length:
        require(inner[:4]==selector('NotEnoughLiquidity(bytes32)')
            and inner[4:]==bytes.fromhex(pool_id[2:]),'Different full-input error')
    return {'rpc_error':error,'canonical_wrapped_bytes':'0x'+inner.hex(),
        'classification':'exact_full_input_incomplete' if length else
            'empty_wrapped_revert_at_500k_unknown_cause'}


def verify(path):
    """Verify one frozen capture. No current-source/market approval is implied."""
    try:
        return _verify(Archive(path))
    except (KeyError,TypeError,IndexError,OverflowError,ZeroDivisionError) as exc:
        raise ValueError('Malformed dated market evidence') from exc


def _verify(e):
    for name,expected in PROVENANCE.items():
        require(hashlib.sha256(e.raw(name)).hexdigest()==expected,
            'Unreviewed historical provenance')
    with gzip.GzipFile(fileobj=io.BytesIO(e.raw('provenance/Nov13-CAPTURE.json.gz'))) as stream:
        prior_raw=stream.read(MAX_MEMBER+1)
    prior=strict_json(prior_raw);inventory=e.obj('provenance/known95-Nov9.json')
    c=e.obj('capture/CAPTURE.json');result=e.obj('RESULTS.json');candidate=e.obj('CANDIDATE_CONFIG.json')
    require(all(type(obj) is dict for obj in (c,result,candidate)),'Invalid evidence object')
    primary,by=_logs(e,'capture',33);a=c['anchor'];block=a['selector'];header=_wire(by['fresh-anchor'])
    require(sum('result' in row['response'] for row in primary['rows'])==28,
        'Dated response classification differs')
    same(a,{'chain_id':4663,'hash':header['hash'],'header':header,
        'number':int(header['number'],16),'timestamp':int(header['timestamp'],16),
        'selector':{'blockHash':header['hash'],'requireCanonical':True}},'Anchor differs from wire')
    same({k:c[k] for k in ('production_approved','deployable_configuration','canonical_final_recheck',
        'public_transactions','source_or_settings_changes','source_pins_unchanged','request_count','safeguards_unchanged')},
        {'production_approved':False,'deployable_configuration':False,'canonical_final_recheck':True,
         'public_transactions':0,'source_or_settings_changes':False,'source_pins_unchanged':True,
         'request_count':33,'safeguards_unchanged':SAFEGUARDS},'Captured scope/limits differ')
    _request(by['chain'],'eth_chainId',[]);same(_wire(by['chain']),'0x1237','Wrong chain')
    _request(by['independent-genesis'],'eth_getBlockByNumber',['0x0',False])
    genesis=_wire(by['independent-genesis']);same(genesis['hash'],GENESIS,'Wrong genesis')
    same(genesis['number'],'0x0','Wrong genesis number')
    _request(by['fresh-anchor'],'eth_getBlockByNumber',['latest',False])
    _request(by['final-canonical-numbered-header'],'eth_getBlockByNumber',[hex(a['number']),False])
    same(_wire(by['final-canonical-numbered-header']),header,'Unclosed primary anchor')
    same(c['final_header'],header,'Embedded final anchor differs')
    same(c['prior_anchor'],prior['anchor'],'Historical anchor differs')
    same(c['prior_pool_inventory_sha256'],PROVENANCE['provenance/known95-Nov9.json'],
        'Historical inventory identity differs')
    require(type(c['runtimes']) is dict,'Invalid runtime inventory')
    for label,pin in c['runtimes'].items():
        _runtime(by[label+'.runtime'],pin,prior['runtimes'][label],block)
    require(set(c['runtimes'])==set(prior['runtimes']),'Runtime inventory differs')
    feeds=c['feeds'];cl=feeds['chainlink_primary'];cl2=feeds['chainlink_secondary']
    require(set(feeds)=={'chainlink_primary','chainlink_secondary','chainlink_aggregator','pyth','api3'},
        'Feed inventory differs')
    for label in ('chainlink_primary','chainlink_secondary','pyth','api3'):
        same(feeds[label]['address'],prior['feeds'][label]['address'],'Feed address differs')
        _runtime(by[label+'.runtime'],feeds[label]['runtime'],prior['feeds'][label]['runtime'],block)
    for label,feed in (('chainlink_primary',cl),('chainlink_secondary',cl2)):
        _call(by[label+'.aggregator'],feed['address'],'0x'+selector('aggregator()').hex(),block)
        same(feed['aggregator'],_wire(by[label+'.aggregator']),'Aggregator observation differs')
        words(feed['aggregator'],1)
    require(cl['aggregator']==cl2['aggregator'],'Historical proxies do not share aggregator')
    aggregator=feeds['chainlink_aggregator']
    same(aggregator['address'],'0x'+cl['aggregator'][-40:],'Aggregator identity differs')
    _runtime(by['chainlink_aggregator.runtime'],aggregator,prior['feeds']['chainlink_aggregator']['runtime'],block)
    for label,signature,field in (('chainlink.primary.round','latestRoundData()','latestRoundData'),
        ('chainlink.primary.decimals','decimals()','decimals')):
        _call(by[label],cl['address'],'0x'+selector(signature).hex(),block)
        same(cl[field],_wire(by[label]),'Chainlink wire observation differs')
    clwords=words(cl['latestRoundData'],5);dec=words(cl['decimals'],1)[0];stamp=a['timestamp']
    rid,answer,started,updated,answered=clwords
    valid=0<rid<1<<80 and 0<answer<1<<255 and 0<started<=updated<=stamp and rid<=answered<1<<80 \
        and dec<=18 and stamp-updated<=86400 and Fraction(answer*10**18,10**dec)<=10**36
    require(valid,'Historical ETH observation is not structurally valid')
    same({key:cl[key] for key in ('age_seconds','structurally_valid_hard_day','same_aggregator_as_secondary','qualified_independent_pair')},
        {'age_seconds':stamp-updated,'structurally_valid_hard_day':True,
         'same_aggregator_as_secondary':True,'qualified_independent_pair':False},'Chainlink interpretation differs')
    eth=Fraction(answer,10**dec)
    conditional=c['conditional_eth_usd']
    same({key:conditional[key] for key in ('numerator','denominator')},
        {key:ratio(eth)[key] for key in ('numerator','denominator')},'Conditional ETH value differs')
    # The old capture's float-formatted decimal is historical display only.
    # Current readable outputs below use exact rational-derived decimal strings.
    for label,signature,data in (('pyth','getPriceUnsafe(bytes32)',word(ETH_ID)),('api3','read()',b'')):
        feed=feeds[label];old=prior['feeds'][label]
        _request(by[label+'.implementation-slot'],'eth_getStorageAt',[feed['address'],SLOT,block])
        same(feed['implementation_slot'],_wire(by[label+'.implementation-slot']),'Implementation wire differs')
        same(feed['implementation_slot'],old['implementation_slot'],'Proxy implementation differs')
        require(feed['implementation_runtime']['address']=='0x'+feed['implementation_slot'][-40:],
            'Implementation address differs')
        _runtime(by[label+'.implementation.runtime'],feed['implementation_runtime'],old['implementation_runtime'],block)
        _call(by[label+'.observation'],feed['address'],'0x'+(selector(signature)+data).hex(),block)
        same(feed['observation'],_wire(by[label+'.observation']),'Feed wire observation differs')
    py=words(feeds['pyth']['observation'],4);exp=py[2]-(1<<256) if py[2]>>255 else py[2]
    require(0<py[0]<1<<63 and py[1]<1<<64 and -36<=exp<=36,'Invalid historical Pyth precision')
    pyprice=Fraction(py[0])*Fraction(10)**exp;spread=abs(pyprice-eth)/min(pyprice,eth)*10000
    pools=_pools(e,c,by,prior,inventory,block)
    selected=next(p for p in pools if p['poolId']==SELECTED)
    reference=max((p for p in pools if p['poolId']!=SELECTED and p['reference_fee_only_candidate']),
        key=lambda p:int(p['active_liquidity']))
    cheap=[p for p in pools if p['poolId'] not in (SELECTED,reference['poolId'])
        and p['strict_principal_fee_only_candidate'] and _fee(p,False)<10000]
    require(bool(cheap),'Missing historical cheap-fee lead')
    conversion=max(cheap,key=lambda p:(int(p['active_liquidity']),-_fee(p,False)))
    same(c['quote_selection'],{'selected':SELECTED,'largest_known_active_L_reference':reference['poolId'],
        'cheap_fee_only_conversion_lead':conversion['poolId'],'no_global_tvl_or_ownership_or_depth_claim':True},
        'Diagnostic venue selection differs')
    quotes=_quotes(c,by,block,eth,selected,reference,conversion)
    markets=_markets(pools,prior,eth,selected)
    primary_seconds=elapsed(c['phase_elapsed_seconds'])
    require(primary_seconds>=primary['rows'][-1]['finished_elapsed_seconds'],'Primary duration predates last response')
    expected={'production_approved':False,'deployable_configuration':False,
        'anchor':{k:v for k,v in a.items() if k!='header'},
        'anchor_utc':dt.datetime.fromtimestamp(stamp,dt.timezone.utc).isoformat(),
        'canonical_final_recheck':True,
        'network':{'primary_requests':33,'primary_phase_seconds':primary_seconds,
            'rpc_results':sum('result' in r['response'] for r in primary['rows']),
            'rpc_errors':sum('error' in r['response'] for r in primary['rows']),
            'read_only':True,'retries':0},
        'feeds':{'chainlink':{'usd':ratio(eth),'updated_at':updated,'age_seconds':stamp-updated,
            'decimals':dec,'two_proxies_same_aggregator':True,'qualified_independent_pair':False,
            'max_age_policy_unapproved':True},
            'pyth':{'stored_usd':ratio(pyprice),'publish_time':py[3],'age_seconds':stamp-py[3],
                'hard_86400_seconds_pass':0<py[3]<=stamp and stamp-py[3]<=86400,
                'confidence_usd':ratio(Fraction(py[1])*Fraction(10)**exp),
                'confidence_bps':ratio(Fraction(py[1],py[0])*10000),
                'spread_vs_chainlink_bps':ratio(spread),'agreement_300bps_pass':spread<=300,'qualified':False},
            'api3':{'current_read':feeds['api3']['observation'],
                'current_base_name_subscription_state':'not_refreshed; historical Nov13 zero values remain dated',
                'round_compatible_adapter_qualified':False}},
        'markets':markets,'quotes':quotes,
        'sources_qualified':{'independent_ETH_pair':False,'independent_ZZZ_pair':False},
        'unchanged_safeguards':SAFEGUARDS,'important_limits':LIMITS}
    same(result,expected,'Readable market/feed/quote/qualification summary differs from wire')
    expected_candidate={'production_approved':False,'deployable_configuration':False,
        'anchor':expected['anchor'],'eth_primary_candidate':{'address':cl['address'],
            'runtime_keccak256':cl['runtime']['keccak256'],'aggregator':aggregator['address'],
            'feed_decimals':dec,'maxAge':None,'independenceId':None,'reviewHash':None},
        'eth_secondary':None,'zzz_primary':None,'zzz_secondary':None,'reviewed_reference':None,
        'reviewed_swap_routes':[],'selected_pool_id':SELECTED,
        'current_selected_active_liquidity':selected['active_liquidity'],'explicit_blockers':BLOCKERS}
    same(candidate,expected_candidate,'Unconfigured candidate snapshot differs from evidence scope')
    discovery=_discovery(e,c)
    # If readable sidecars accompany a ZIP, they must be the exact archived bytes.
    for name in ('RESULTS.json','CANDIDATE_CONFIG.json'):
        sibling=e.path.parent/name
        if sibling.exists():
            require(sibling.is_file() and sibling.stat().st_size<=MAX_MEMBER,
                'Invalid readable evidence sidecar')
            with sibling.open('rb') as stream:
                same_raw=stream.read(MAX_MEMBER+1)
            require(same_raw==e.raw(name),'Readable sidecar differs from archived evidence')
    return {'status':'PASS','schema':SCHEMA,'public_files':e.member_count,
        'actual_read_responses':39,'valid_results':34,'explicit_rpc_errors':5,
        'known_pool_states':95,'quote_diagnostics':6,'discovery_queries':discovery,
        'production_approved':False,'deployable_configuration':False,
        'template_ready':False,'live_market_qualification':False,
        'scope':'dated internal evidence integrity and semantic closure; not provider truth or live admission',
        'network_calls':0,'EVM_runs':0,'compiler_runs':0}


def _pools(e,c,by,prior,inventory,block):
    rawpools=c['known_pool_states']
    require(type(rawpools) is list and len(rawpools)==95,'Wrong known pool count')
    require([p['poolId'] for p in rawpools]==[p['poolId'] for p in inventory]
        ==[p['poolId'] for p in prior['known_pool_states']],'Historical pool order/inventory differs')
    slots=[]
    for p,old in zip(rawpools,inventory):
        key=p['key'];same(key,old['key'],'Historical PoolKey differs')
        require(type(key) is list and len(key)==5 and key[0]==ZERO and key[1]==ZZZ and key[4]==ZERO,
            'Different market pair/hook')
        number(key[2],0,999999);number(key[3],1,32767)
        require(digest(b''.join(word(x) for x in key))==p['poolId'],'PoolKey hash differs')
        slot=int.from_bytes(keccak256(word(p['poolId'])+word(6)),'big');slots.extend((slot,slot+3))
    packed=[]
    for index,start in enumerate(range(0,len(slots),50)):
        chunk=slots[start:start+50]
        data='0x'+(selector('extsload(bytes32[])')+word(32)+word(len(chunk))
            +b''.join(word(x) for x in chunk)).hex()
        _call(by[f'known95-bulk-{index}'],c['runtimes']['core']['address'],data,block)
        values=words(_wire(by[f'known95-bulk-{index}']),len(chunk)+2)
        same(values[:2],[32,len(chunk)],'Bulk return layout differs');packed+=values[2:]
    pools=[]
    for index,p in enumerate(rawpools):
        raw,L=packed[2*index:2*index+2];tick=(raw>>160)&0xffffff
        tick-=1<<24 if tick&(1<<23) else 0
        require(raw>>232==0 and L<1<<128,'Pool storage word out of bounds')
        state={'sqrtPriceX96':raw&((1<<160)-1),'tick':tick,
            'protocolFee':(raw>>184)&0xffffff,'lpFee':(raw>>208)&0xffffff}
        require(state['sqrtPriceX96']>0 and state['lpFee']==p['key'][2],
            'Uninitialized or changed static fee')
        _fee({'slot0':state},True);_fee({'slot0':state},False)
        actual={'poolId':p['poolId'],'key':p['key'],'slot0':state,'active_liquidity':str(L),
            'reference_fee_only_candidate':state['lpFee']<1000000,
            'strict_principal_fee_only_candidate':state['lpFee']<100000}
        same(p,actual,'Decoded market state/fee-only flags differ');pools.append(actual)
    return pools


def _quotes(c,by,block,eth,selected,reference,conversion):
    require(type(c['quotes']) is list and len(c['quotes'])==6,'Exactly six diagnostics required')
    derived=[]
    for index,(label,p,nominal) in enumerate((('selected',selected,100),
        ('largest-known-active-L',reference,100),('cheap-fee-only',conversion,5))):
        for offset,direction in enumerate((True,False)):
            amount=int(Fraction(nominal*10**18)/eth) if direction else 1000*10**18
            require(0<amount<1<<128,'Diagnostic input outside bounds')
            data='0x'+(selector('quoteExactInputSingle(((address,address,uint24,int24,address),bool,uint128,bytes))')
                +word(32)+b''.join(word(x) for x in p['key'])+word(int(direction))+word(amount)+word(256)+word(0)).hex()
            wire=by['quote.'+label+'.'+('ETH-to-ZZZ' if direction else 'ZZZ-to-ETH')]
            _call(wire,c['runtimes']['quoter']['address'],data,block)
            observed=_wire(wire)
            quote={'venue_label':label,'pool_id':p['poolId'],'key':p['key'],
                'zero_for_one':direction,'input_raw':str(amount),
                'nominal_USD_from_single_ETH_round_only':nominal if direction else None,
                'result':observed,'gas_ceiling':500000,'postspot':None,'qualified_usd':False,
                'known_directional_total_fee_pips':_fee(p,direction)}
            same(c['quotes'][2*index+offset],quote,'Captured quote differs from exact wire/input/policy')
            out={**quote,'whole_operation_qualified':False,'analytical_floor_scope':ANALYTICAL_SCOPE}
            if type(observed) is str:
                value,gas=words(observed,2);number(gas,1,500000)
                price=Fraction(p['slot0']['sqrtPriceX96']**2,1<<192)
                ideal=amount*(price if direction else 1/price)
                net=ideal*Fraction(1000000-_fee(p,direction),1000000)
                out.update(amount_out_raw=str(value),quoter_reported_gas=gas,
                    conditional_own_spot_gross_loss_bps=ratio((1-Fraction(value)/ideal)*10000),
                    conditional_extra_loss_after_known_fee_bps=ratio((1-Fraction(value)/net)*10000),
                    passes_analytic_3pct_swap_value_floor=Fraction(value)>=ideal*Fraction(97,100),
                    passes_analytic_1pct_conversion_gross_floor=Fraction(value)>=ideal*Fraction(99,100),
                    passes_analytic_1pct_additional_after_fee_floor=Fraction(value)>=net*Fraction(99,100))
            else:
                out['error_decode']=_error(observed,p['poolId'])
            derived.append(out)
    return derived


def _markets(pools,prior,eth,selected):
    initial=Fraction(selected['slot0']['sqrtPriceX96']**2,1<<192)
    all_bands=[];active=[];changed=[]
    for p,old in zip(pools,prior['known_pool_states']):
        price=Fraction(p['slot0']['sqrtPriceX96']**2,1<<192);relative=price/initial
        row={**p,'zzz_per_eth':ratio(price),'eth_per_zzz':ratio(1/price),
            'conditional_zzz_usd_from_single_ETH_and_this_pool':ratio(eth/price),
            'price_ratio_to_selected':ratio(relative),
            'common_500bps_continuous_reference_possible':max(relative,1/relative)<=Fraction(105,95),
            'combined_fee_pips_ETH_to_ZZZ':_fee(p,True),'combined_fee_pips_ZZZ_to_ETH':_fee(p,False)}
        all_bands.append(row)
        if int(p['active_liquidity']):
            active.append(row)
        if p['slot0']!=old['slot0'] or int(p['active_liquidity'])!=old['liquidity']:
            changed.append(p['poolId'])
    return {'known_pool_count':95,'changed_since_Nov13':changed,
        'active_reference_fee_only_count':len(active),
        'active_strict_principal_fee_only_count':sum(p['strict_principal_fee_only_candidate'] for p in active),
        'selected':next(p for p in all_bands if p['poolId']==SELECTED),
        'active_by_rawL_not_TVL':sorted(active,key=lambda p:int(p['active_liquidity']),reverse=True),
        'all_bands':all_bands,'global_highest_or_ownership_or_depth_qualified':False}


def _discovery(e,c):
    topic=digest(b'Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)')
    for phase,lo,hi,target in (('discovery',113296580,c['anchor']['number'],c['anchor']),
        ('discovery-gap',110324512,113296579,c['prior_anchor'])):
        log,_by=_logs(e,phase,3);rows=log['rows'];out=e.obj(phase+'/RESULT.json')
        query={'address':c['runtimes']['core']['address'],'fromBlock':hex(lo),'toBlock':hex(hi),
            'topics':[topic,None,'0x'+'0'*64,'0x'+ZZZ[2:].rjust(64,'0')]}
        for row in (rows[0],rows[2]):
            _request(row,'eth_getBlockByNumber',[hex(target['number']),False])
            same(_wire(row),target['header'],'Discovery closure differs')
        _request(rows[1],'eth_getLogs',[query]);same(_wire(rows[1]),[],'Different discovery logs')
        same({k:out[k] for k in ('canonical_closed','exact_pair','global_inventory_complete',
            'new_pool_keys','production_approved','query','range_end','range_start','raw_log_count','requests')},
            {'canonical_closed':True,'exact_pair':{'currency0':ZERO,'currency1':ZZZ},
             'global_inventory_complete':False,'new_pool_keys':[],'production_approved':False,
             'query':query,'range_end':hi,'range_start':lo,'raw_log_count':0,'requests':3},
            'Discovery interpretation differs')
        require(elapsed(out['elapsed_seconds'])>=rows[-1]['finished_elapsed_seconds'],
            'Discovery duration predates response')
    return 2
