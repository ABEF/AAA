"""Offline, explicit history recovery; never adopts configuration or repairs data.

SQLite snapshots preserve every retained row. This is local integrity/provenance,
not global snapshot atomicity, canonical chain proof or log-completeness proof.
Existing semantic readers, accounting and HTTP budgets are unchanged.
"""
from contextlib import closing
from contextlib import ExitStack
import copy
import hashlib
import heapq
import json
import os
from pathlib import Path
import platform
import re
import sqlite3
import stat

from frontend_api.earnings_checkpoint import MAX_BYTES, decode, encode, identity
from frontend_api.earnings_checkpoint_build import BuildBudget
from frontend_api.earnings_checkpoint_v3 import graph_identity, peers, sources
from frontend_api.earnings_checkpoint_import import _bind_review, PRODUCER_FILES as IMPORT_PRODUCERS
from frontend_api.earnings_replay import require
from frontend_api.history import HistoryError, _hash, _quantity, _stored_json
from frontend_api.service import Projection
from zzz_ops.abi import address
from zzz_ops.log_provenance import OrderedTransactions
from zzz_ops.work_budget import checkpoint, request_scope

ROOT = Path(__file__).resolve().parents[1]
PRODUCERS = ('frontend_api/history_recovery.py', 'scripts/history-recovery.py',
             'frontend_api/earnings_checkpoint_import.py')
MAX_JSON = 1024 * 1024
DEFAULT_BYTES = 1 << 30
MAX_PACKAGE_BYTES = 1 << 40
OFFLINE_URL = 'https://offline.invalid'
FLAGS = ('approved', 'production_approved', 'installed', 'ready_for_submission')
DDL = {
    'cursors': 'CREATE TABLE cursors(chain INTEGER PRIMARY KEY,next_block INTEGER NOT NULL,config TEXT NOT NULL)',
    'blocks': 'CREATE TABLE blocks(chain INTEGER,number INTEGER,hash TEXT NOT NULL,parent TEXT NOT NULL,timestamp INTEGER NOT NULL,PRIMARY KEY(chain,number))',
    'logs': 'CREATE TABLE logs(chain INTEGER,block_number INTEGER,block_hash TEXT,transaction_hash TEXT,log_index INTEGER,address TEXT,event TEXT,decoded TEXT,raw TEXT NOT NULL,PRIMARY KEY(chain,transaction_hash,log_index),FOREIGN KEY(chain,block_number) REFERENCES blocks(chain,number) ON DELETE CASCADE)',
    'event_lookup': 'CREATE INDEX event_lookup ON logs(chain,address,event,block_number)',
    'block_log_lookup': 'CREATE INDEX block_log_lookup ON logs(chain,block_number,log_index)',
}
MANIFEST_FIELDS = frozenset(('schema', 'kind', *FLAGS, 'source_configuration_sha256', 'producer_sources',
    'semantic_sources', 'graph', 'files', 'databases', 'checkpoint', 'import_review', 'raw_retention',
    'snapshot_consistency', 'runtime', 'max_bytes'))


class NoNetwork:
    def call(self, *args, **kwargs):
        raise HistoryError('History recovery cannot make network calls')


def _json(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode('utf-8')


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _digest(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def producer_sources():
    return {n: _sha((ROOT/n).read_bytes().replace(b'\r\n', b'\n')) for n in PRODUCERS}


def _limit(value):
    require(type(value) is int and 1 <= value <= MAX_PACKAGE_BYTES, 'Invalid offline package byte bound')


def _path(value, *, kind=None):
    """Reject aliases/reparse entries; owner-controlled directories remain required."""
    p = Path(value).expanduser().absolute()
    require('..' not in p.parts, 'Recovery paths must not contain parent traversal')
    for item in (*reversed(p.parents), p):
        try:
            info = item.lstat()
        except FileNotFoundError:
            require(item == p and kind is None, 'Recovery path is missing')
            continue
        require(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) &
                getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400), 'Recovery path must not use links or reparse points')
    if kind == 'file': require(p.is_file(), 'Recovery input must be a regular file')
    if kind == 'dir': require(p.is_dir(), 'Recovery input must be a directory')
    return p


def _read(path, maximum):
    path = _path(path, kind='file'); checkpoint()
    with path.open('rb') as handle: raw = handle.read(maximum+1)
    require(len(raw) <= maximum, 'Recovery input exceeds its byte bound')
    checkpoint()
    return raw


def load_config(path):
    value = _stored_json(_read(path, MAX_JSON).decode('utf-8'))
    require(isinstance(value, dict), 'Recovery configuration must be an object')
    return value


def _engine(config):
    # Check unresolved input entries before History's normal resolve() drops
    # symlink spelling. Construction is configuration-only; injected RPC denies
    # accidental future network work in current and predecessor constructors.
    require(isinstance(config, dict), 'Recovery requires a reviewed API configuration')
    require(isinstance(config.get('earnings_history'),dict) and
            isinstance(config.get('predecessors',[]),list), 'Recovery requires an exact earnings/history inventory')
    for row in [*config.get('predecessors', []), config]:
        require(isinstance(row, dict) and isinstance(row.get('history'), dict), 'Every epoch needs raw history')
        _path(row['history']['database'], kind='file')
    cp = config.get('earnings_history', {}).get('checkpoint')
    if cp is not None:
        require(isinstance(cp, dict), 'Invalid reviewed checkpoint configuration')
        _path(cp['path'], kind='file')
    p = Projection(config, NoNetwork())
    engine = p.earnings_history
    require(engine is not None and p.accounting_version == 7 and p.custody_version == 5 and
            p.fee_intake_version == 1, 'Recovery requires the current exact-accounting earnings profile')
    group = peers(engine) if p.lineage else [p]
    require(all(q.history is not None for q in group), 'Recovery omits an epoch history')
    paths = [q.history.database for q in group]
    require(len(paths) == len(set(paths)), 'Recovery databases must be distinct')
    # Two hardlinks are also one database, not two independent histories.
    require(len({(p.stat().st_dev, p.stat().st_ino) for p in paths}) == len(paths), 'Recovery database aliases are forbidden')
    graph = (graph_identity(engine) if p.lineage else [dict(deployment=identity(engine),
        mint_integration_version=p.mint_integration_version, execution_price_version=p.execution_price_version,
        retirement_transaction_hash=None)])
    return engine, group, graph


def _portable(config, count):
    value = copy.deepcopy(config); value['rpc_urls'] = [OFFLINE_URL]
    for n, row in enumerate([*value.get('predecessors', []), value]):
        row['history']['database'] = f'databases/{n:03d}.sqlite'
    require(count == len(value.get('predecessors', []))+1, 'Portable profile graph differs')
    cp = value['earnings_history'].get('checkpoint')
    if cp is not None: cp['path'] = 'checkpoint.json'
    return value


def _materialize(profile, folder):
    require(isinstance(profile, dict) and profile.get('rpc_urls') == [OFFLINE_URL], 'Recovery profile is not offline')
    value = copy.deepcopy(profile)
    for n, row in enumerate([*value.get('predecessors', []), value]):
        require(row['history']['database'] == f'databases/{n:03d}.sqlite', 'Recovery database path differs')
        row['history']['database'] = str(folder/f'databases/{n:03d}.sqlite')
    cp = value.get('earnings_history', {}).get('checkpoint')
    if cp is not None:
        require(cp['path'] == 'checkpoint.json', 'Recovery checkpoint path differs')
        cp['path'] = str(folder/'checkpoint.json')
    return value


def _reserve(folder):
    folder = _path(folder)
    require(folder.parent.is_dir(), 'Recovery output parent must exist')
    folder.mkdir(mode=0o700)  # Exclusive, including empty/existing/dangling entries.
    _sync_dir(folder.parent)
    (folder/'databases').mkdir(mode=0o700)
    _sync_dir(folder)
    return folder


def _sync_dir(folder):
    if os.name != 'nt':
        fd = os.open(folder, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
        try: os.fsync(fd)
        finally: os.close(fd)


def _write(path, raw):
    checkpoint()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    with os.fdopen(fd, 'wb') as handle:
        handle.write(raw); handle.flush(); os.fsync(handle.fileno())
    _sync_dir(path.parent); checkpoint()


def _file(path, maximum=MAX_PACKAGE_BYTES):
    path = _path(path, kind='file'); before = path.stat(); digest = hashlib.sha256(); size = 0
    require(before.st_size<=maximum,'Recovery payload exceeds its remaining byte bound')
    with path.open('rb') as handle:
        while True:
            checkpoint(); raw = handle.read(1024*1024)
            if not raw: break
            size += len(raw); require(size<=maximum,'Recovery payload grew beyond its byte bound'); digest.update(raw)
    after = path.stat()
    require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) and size == after.st_size,
            'Recovery payload changed while reading')
    return {'bytes': size, 'sha256': digest.hexdigest()}


def _connect(path):
    db = sqlite3.connect(_path(path, kind='file').as_uri()+'?mode=ro', uri=True, timeout=0.1)
    try:
        db.execute('PRAGMA query_only=ON'); db.execute('PRAGMA trusted_schema=OFF')
        def progress():
            checkpoint()
            return 0
        db.set_progress_handler(progress, 1000)
        db.execute('BEGIN'); db.execute('SELECT count(*) FROM sqlite_schema').fetchone()
        return db
    except BaseException:
        db.close(); raise


def _schema(db):
    normalize = lambda sql: re.sub(r'\s+', '', sql).lower()
    rows = db.execute('SELECT type,name,tbl_name,sql FROM sqlite_schema LIMIT 8').fetchall()
    expected = {('table', n, n, normalize(DDL[n])) for n in ('cursors','blocks','logs')}
    expected |= {('index', n, 'logs', normalize(DDL[n])) for n in ('event_lookup','block_log_lookup')}
    expected |= {('index', 'sqlite_autoindex_'+n+'_1', n, None) for n in ('blocks','logs')}
    require({(t,n,table,normalize(sql) if sql else None) for t,n,table,sql in rows} == expected and
            len(rows) == len(expected), 'Unsupported recovery database schema')
    require(db.execute('PRAGMA integrity_check(1)').fetchall() == [('ok',)] and
            db.execute('PRAGMA foreign_key_check').fetchone() is None, 'Recovery database integrity failed')


def _summary(db, p, *, scan):
    _schema(db); h = p.history
    row = db.execute('SELECT chain,next_block,config FROM cursors LIMIT 2').fetchall()
    expected = {'contracts':h.contracts,'start':h.start,'parent_hash':h.parent}
    require(len(row) == 1 and type(row[0][0]) is int and row[0][0] == h.chain and
            type(row[0][1]) is int and h.start <= row[0][1] < 1 << 63 and
            isinstance(row[0][2], str) and encode(_stored_json(row[0][2])) == encode(expected),
            'Recovery cursor or database identity differs')
    count, low, high = db.execute('SELECT count(*),min(number),max(number) FROM blocks').fetchone()
    require(count == row[0][1]-h.start and (not count or (low == h.start and high == row[0][1]-1)),
            'Recovery block coverage or cursor differs')
    logs = db.execute('SELECT count(*) FROM logs').fetchone()[0]
    joined=db.execute('SELECT count(*) FROM logs l JOIN blocks b ON b.chain=l.chain AND b.number=l.block_number').fetchone()[0]
    require(joined==logs,'Recovery contains null or orphaned log locations')
    first = tip = None; previous_hash = h.parent; previous_time = 0; number = h.start
    for chain,n,digest,parent,timestamp in db.execute('SELECT chain,number,hash,parent,timestamp FROM blocks ORDER BY number'):
        checkpoint()
        require(type(chain) is int and chain == h.chain and type(n) is int and n == number and
                type(timestamp) is int and previous_time <= timestamp < 1 << 63 and
                _hash(digest) == digest and _hash(parent) == parent and parent == previous_hash,
                'Recovery block ancestry or timestamps differ')
        header = dict(number=n,hash=digest,timestamp=timestamp)
        first = first or header; tip = header; number += 1; previous_hash=digest; previous_time=timestamp
    if count:
        deployment = db.execute('SELECT hash FROM blocks WHERE number=? AND chain=?',(p.start,p.chain)).fetchone()
        require(deployment == (p.start_hash,), 'Recovery deployment anchor is missing or differs')
    require(not db.execute('SELECT 1 FROM logs WHERE chain!=? OR chain IS NULL LIMIT 1',(h.chain,)).fetchone(),
            'Recovery logs contain another chain')
    if scan:
        order = OrderedTransactions()
        for chain,n,bhash,tx,index,emitter,raw,stored_hash in db.execute('''SELECT l.chain,l.block_number,l.block_hash,
                l.transaction_hash,l.log_index,l.address,l.raw,b.hash FROM logs l JOIN blocks b
                ON b.chain=l.chain AND b.number=l.block_number ORDER BY l.block_number,l.log_index'''):
            checkpoint()
            require(type(n) is int and type(index) is int and 0 <= index < 1 << 63 and
                    _hash(bhash) == stored_hash and _hash(tx) == tx and address(emitter) == emitter and
                    emitter in h.contracts and isinstance(raw, str) and len(raw) <= 131072,
                    'Recovery raw log identity differs')
            item = _stored_json(raw)
            require(isinstance(item,dict) and item.get('removed') is False and
                    address(item.get('address')) == emitter and _quantity(item.get('blockNumber')) == n and
                    _hash(item.get('blockHash')) == bhash and _hash(item.get('transactionHash')) == tx and
                    _quantity(item.get('logIndex')) == index and isinstance(item.get('topics'), list) and
                    len(item['topics']) <= 4 and all(isinstance(t,str) and re.fullmatch('0x[0-9a-fA-F]{64}',t) for t in item['topics']) and
                    isinstance(item.get('data'),str) and re.fullmatch('0x(?:[0-9a-fA-F]{2})*',item['data']),
                    'Recovery stored raw envelope differs')
            order.add(n,index,tx,None if 'transactionIndex' not in item else _quantity(item['transactionIndex']))
        require(not db.execute('SELECT 1 FROM logs GROUP BY transaction_hash HAVING min(block_number)!=max(block_number) LIMIT 1').fetchone(),
                'Recovery transaction appears in multiple blocks')
    return dict(next_block=row[0][1],block_count=count,log_count=logs,first=first,tip=tip)


def _coherent(group):
    with ExitStack() as stack:
        connections=[stack.enter_context(closing(_connect(p.history.database))) for p in group]
        streams=[db.execute('SELECT number,hash,parent,timestamp FROM blocks ORDER BY number') for db in connections]
        prior=None
        for row in heapq.merge(*streams):
            checkpoint()
            require(prior is None or row[0] != prior[0] or row == prior,
                    'Recovery epoch snapshots disagree on overlapping headers')
            prior=row


def _checkpoint_info(engine, group):
    cp = engine.checkpoint
    if cp is None: return None
    cursor=getattr(cp,'cursor',0)
    anchors=[*getattr(cp,'_completed_anchors',()),cp.anchor]
    require(len(anchors)==cursor+1, 'Recovery checkpoint epochs differ')
    for p,header in zip(group,anchors):
        with closing(_connect(p.history.database)) as db:
            actual=db.execute('SELECT hash,timestamp FROM blocks WHERE chain=? AND number=?',(p.chain,header['number'])).fetchone()
            require(actual==(header['hash'],header['timestamp']), 'Recovery checkpoint anchor is absent or differs')
    data=_stored_json(cp._raw.decode('utf-8'))
    return dict(path='checkpoint.json',sha256=cp.digest,schema=data['schema'],cursor=cursor,
                anchor=dict(cp.anchor),earliest_served_timestamp=cp.anchor['timestamp']+86400)


def _review(raw, digest, checkpoint_info, graph, cp_raw):
    require(_digest(digest) and _sha(raw)==digest and checkpoint_info is not None,
            'Recovery review needs its exact external digest and checkpoint')
    item=_stored_json(raw.decode('utf-8')); data=_stored_json(cp_raw.decode('utf-8'))
    require(isinstance(item,dict) and type(item.get('schema')) is int and item['schema']==1 and
            item.get('kind')=='popl-offline-checkpoint-prefix-import' and
            item.get('checkpoint_sha256')==checkpoint_info['sha256'] and
            encode(item.get('target_graph'))==encode(graph) and
            item.get('prefix_sha256')==data.get('previous_sha256') and
            item.get('output_semantic_sources')==data.get('sources') and
            all(item.get(flag) is False for flag in (*FLAGS,'transactions_submitted')),
            'Recovery import review does not bind the exact checkpoint graph')
    require(isinstance(item.get('producer_sources'),dict) and set(item['producer_sources'])==set(IMPORT_PRODUCERS) and
            all(_digest(v) for v in item['producer_sources'].values()), 'Invalid original import producer provenance')
    # Preserve externally reviewed ORIGINAL producer pins; this does not adopt
    # its code. Bind every sidecar graph/anchor/timer claim through the fixed
    # original importer's validator, whose source is pinned by this producer.
    _bind_review(data,item)
    return dict(path='import-review.json',sha256=digest)


def _files(folder, names, maximum):
    records=[];size=0
    for name in names:
        entry=dict(path=name,**_file(folder/name,maximum-size));size+=entry['bytes'];records.append(entry)
        require(size<=maximum,'Recovery package exceeds its explicit byte bound')
    return records


def backup(config, output_dir, *, review=None, budget=None, max_bytes=DEFAULT_BYTES):
    """Read-only sources; new exclusive directory. Failures retain partial output."""
    with request_scope(budget or BuildBudget()):
        _limit(max_bytes); producer=producer_sources(); semantic=sources()
        config=copy.deepcopy(config)
        engine,group,graph=_engine(config)
        cp_raw=None if engine.checkpoint is None else engine.checkpoint._raw
        review_raw=None
        if review is not None:
            require(isinstance(review,dict) and set(review)=={'path','sha256'}, 'Invalid import review input')
            review_raw=_read(review['path'],MAX_JSON)
            _review(review_raw,review['sha256'],{'sha256':engine.checkpoint.digest} if cp_raw else None,graph,cp_raw)
        profile=_portable(config,len(group));profile_raw=_json(profile)
        require(len(profile_raw)<=MAX_JSON,'Recovery profile exceeds its byte bound')
        artifacts={'profile.json':profile_raw}
        if cp_raw is not None:artifacts['checkpoint.json']=cp_raw
        if review_raw is not None:artifacts['import-review.json']=review_raw
        used=sum(len(raw) for raw in artifacts.values())
        require(used<=max_bytes,'Recovery artifacts exceed the package byte bound')
        folder=_reserve(output_dir);names=[];snapshots=[]
        # Snapshot each database independently. No source PRAGMA checkpoint,
        # schema creation, journal-mode change or WAL deletion is performed.
        for n,p in enumerate(group):
            checkpoint();name=f'databases/{n:03d}.sqlite';target=folder/name
            original=_path(p.history.database,kind='file').stat()
            with closing(_connect(p.history.database)) as source:
                page_size=source.execute('PRAGMA page_size').fetchone()[0]
                pages=source.execute('PRAGMA page_count').fetchone()[0]
                require(used+page_size*pages<=max_bytes,'Recovery database exceeds its explicit byte bound')
                before=_summary(source,p,scan=False)
                fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
                with closing(sqlite3.connect(target,timeout=0.1)) as destination:
                    def progress(status,remaining,total):
                        checkpoint()
                        require(used+total*page_size<=max_bytes,'Recovery snapshot exceeds its byte bound')
                    source.backup(destination,pages=64,progress=progress,sleep=0.01)
                    require(destination.execute('PRAGMA journal_mode=DELETE').fetchone()==('delete',),
                            'Recovery copy is not a standalone database')
                    destination.commit()
                require(_summary(source,p,scan=False)==before,'Recovery source snapshot changed')
            after=_path(p.history.database,kind='file').stat()
            require((original.st_dev,original.st_ino)==(after.st_dev,after.st_ino),
                    'Recovery source database was replaced during its snapshot')
            with target.open('r+b') as handle:os.fsync(handle.fileno())
            used+=target.stat().st_size;names.append(name)
            snapshots.append(dict(path=name,controller=p.contracts['access'].address,snapshot=before))
        for name,raw in artifacts.items():_write(folder/name,raw);names.append(name)
        restored_engine,restored_group,restored_graph=_engine(_materialize(profile,folder))
        require(encode(restored_graph)==encode(graph),'Recovery portable deployment graph differs')
        for p,row in zip(restored_group,snapshots):
            with closing(_connect(p.history.database)) as db:require(_summary(db,p,scan=True)==row['snapshot'], 'Recovery copied snapshot differs')
        _coherent(restored_group);cp_info=_checkpoint_info(restored_engine,restored_group)
        review_info=None if review_raw is None else _review(review_raw,review['sha256'],cp_info,graph,cp_raw)
        manifest=dict(schema=1,kind='popl-history-recovery',**{flag:False for flag in FLAGS},
            source_configuration_sha256=engine.p.identity,producer_sources=producer,semantic_sources=semantic,
            graph=graph,files=_files(folder,names,max_bytes),databases=snapshots,checkpoint=cp_info,import_review=review_info,
            raw_retention=dict(mode='all_retained_rows',window_seconds=86400,pruned=False,serving_eligibility='unverified'),
            snapshot_consistency='individual_sqlite_snapshots_not_atomic_graph',
            runtime=dict(python=platform.python_version(),sqlite=sqlite3.sqlite_version),max_bytes=max_bytes)
        require(producer_sources()==producer and sources()==semantic,'Recovery source changed during construction')
        raw=_json(manifest);require(len(raw)<=MAX_JSON,'Recovery manifest exceeds its byte bound')
        require(sum(r['bytes'] for r in manifest['files'])+len(raw)<=max_bytes,
                'Recovery manifest exceeds the remaining package byte bound')
        _sync_dir(folder/'databases');_write(folder/'manifest.json',raw)
        return manifest,_sha(raw)


def _inventory(folder, names, *, receipt):
    expected={'manifest.json',*names}
    if receipt:expected.add('restore.json')
    actual=set()
    for path in folder.iterdir():
        _path(path,kind='dir' if path.name=='databases' else 'file')
        if path.name=='databases':
            for child in path.iterdir():
                _path(child,kind='file');actual.add('databases/'+child.name)
        else:actual.add(path.name)
    require(actual==expected,'Recovery bundle has missing or unexpected entries')


def _receipt(raw, manifest_sha, files):
    value=_stored_json(raw.decode('utf-8'))
    require(isinstance(value,dict) and set(value)=={'schema','kind','manifest_sha256','files',*FLAGS} and
            type(value['schema']) is int and value['schema']==1 and value['kind']=='popl-history-restore' and
            value['manifest_sha256']==manifest_sha and value['files']==files and
            all(value[flag] is False for flag in FLAGS),'Recovery receipt differs from the reviewed bundle')


def verify(bundle_dir, manifest_sha256, *, budget=None, max_bytes=DEFAULT_BYTES):
    """Offline integrity/profile verification, never canonical approval or repair."""
    with request_scope(budget or BuildBudget()):
        _limit(max_bytes);require(_digest(manifest_sha256),'Invalid externally reviewed manifest digest')
        folder=_path(bundle_dir,kind='dir');raw=_read(folder/'manifest.json',MAX_JSON)
        require(_sha(raw)==manifest_sha256,'Recovery manifest differs from the reviewed digest')
        value=_stored_json(raw.decode('utf-8'))
        require(isinstance(value,dict) and set(value)==MANIFEST_FIELDS and type(value['schema']) is int and value['schema']==1 and
                value['kind']=='popl-history-recovery' and all(value[flag] is False for flag in FLAGS) and
                value['producer_sources']==producer_sources() and value['semantic_sources']==sources() and
                _digest(value['source_configuration_sha256']) and value['snapshot_consistency']=='individual_sqlite_snapshots_not_atomic_graph' and
                encode(value['raw_retention'])==encode(dict(mode='all_retained_rows',window_seconds=86400,pruned=False,serving_eligibility='unverified')),
                'Recovery manifest source, profile or scope differs')
        _limit(value['max_bytes'])
        require(isinstance(value['files'],list) and 2<=len(value['files'])<=12 and
                all(isinstance(r,dict) and set(r)=={'path','bytes','sha256'} and type(r['bytes']) is int and
                    0<r['bytes']<=max_bytes and _digest(r['sha256']) for r in value['files']), 'Invalid recovery file inventory')
        require(isinstance(value['databases'],list) and 1<=len(value['databases'])<=9 and
                all(isinstance(r,dict) and set(r)=={'path','controller','snapshot'} and r['path']==f'databases/{n:03d}.sqlite'
                    for n,r in enumerate(value['databases'])), 'Invalid recovery database inventory')
        names=['profile.json',*[r['path'] for r in value['databases']]]
        if value['checkpoint'] is not None:names.append('checkpoint.json')
        if value['import_review'] is not None:names.append('import-review.json')
        require(len({r['path'] for r in value['files']})==len(names) and {r['path'] for r in value['files']}==set(names),
                'Recovery payload names differ')
        package_bytes=sum(row['bytes'] for row in value['files'])+len(raw)
        require(package_bytes<=min(max_bytes,value['max_bytes']),'Recovery total package byte bound exceeded')
        receipt=(folder/'restore.json').exists() or (folder/'restore.json').is_symlink()
        _inventory(folder,names,receipt=receipt)
        actual={r['path']:r for r in _files(folder,names,min(max_bytes,value['max_bytes']))}
        require(all(actual[r['path']]==r for r in value['files']),'Recovery payload bytes differ')
        profile=_stored_json(_read(folder/'profile.json',MAX_JSON).decode('utf-8'))
        engine,group,graph=_engine(_materialize(profile,folder))
        require(encode(graph)==encode(value['graph']) and len(group)==len(value['databases']), 'Recovery deployment graph differs')
        for p,row in zip(group,value['databases']):
            require(row['controller']==p.contracts['access'].address,'Recovery controller order differs')
            with closing(_connect(p.history.database)) as db:require(encode(_summary(db,p,scan=True))==encode(row['snapshot']),'Recovery snapshot differs')
        _coherent(group);cp_info=_checkpoint_info(engine,group)
        require(encode(cp_info)==encode(value['checkpoint']),'Recovery checkpoint coverage differs')
        if value['import_review'] is not None:
            require(value['import_review']==_review(_read(folder/'import-review.json',MAX_JSON),
                actual['import-review.json']['sha256'],cp_info,graph,engine.checkpoint._raw),'Recovery review differs')
        if receipt:
            receipt_raw=_read(folder/'restore.json',MAX_JSON)
            require(package_bytes+len(receipt_raw)<=max_bytes,'Recovery receipt exceeds its byte bound')
            _receipt(receipt_raw,manifest_sha256,value['files'])
        require(all(dict(path=n,**_file(folder/n,actual[n]['bytes']))==actual[n] for n in names) and
                _sha(_read(folder/'manifest.json',MAX_JSON))==manifest_sha256,'Recovery package changed during verification')
        _inventory(folder,names,receipt=receipt)
        return value


def _copy(source, target, expected):
    _path(source,kind='file');digest=hashlib.sha256();size=0
    fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0),0o600)
    with os.fdopen(fd,'wb') as dst,source.open('rb') as src:
        while True:
            checkpoint();raw=src.read(1024*1024)
            if not raw:break
            size+=len(raw);require(size<=expected['bytes'],'Recovery source grew during copy')
            dst.write(raw);digest.update(raw)
        dst.flush();os.fsync(dst.fileno())
    require(size==expected['bytes'] and digest.hexdigest()==expected['sha256'],'Recovery source changed during copy')


def restore(bundle_dir, manifest_sha256, output_dir, *, budget=None, max_bytes=DEFAULT_BYTES):
    """Create separate working copies; never overwrites, links or starts a service."""
    with request_scope(budget or BuildBudget()):
        manifest=verify(bundle_dir,manifest_sha256,max_bytes=max_bytes)
        source=_path(bundle_dir,kind='dir');target=_path(output_dir)
        require(not target.is_relative_to(source),'Recovery output must not be inside its source bundle')
        raw=_read(source/'manifest.json',MAX_JSON)
        require(_sha(raw)==manifest_sha256,'Recovery source manifest changed')
        receipt=_json(dict(schema=1,kind='popl-history-restore',manifest_sha256=manifest_sha256,
                           files=manifest['files'],**{flag:False for flag in FLAGS}))
        require(len(receipt)<=MAX_JSON and sum(r['bytes'] for r in manifest['files'])+len(raw)+len(receipt)<=max_bytes,
                'Restored package and receipt exceed the byte bound')
        folder=_reserve(target)
        for row in manifest['files']:_copy(source/row['path'],folder/row['path'],row)
        require(_sha(_read(source/'manifest.json',MAX_JSON))==manifest_sha256,'Recovery source manifest changed')
        _sync_dir(folder/'databases');_write(folder/'manifest.json',raw)
        verify(folder,manifest_sha256,max_bytes=max_bytes)
        _write(folder/'restore.json',receipt)
        return manifest,_sha(receipt)
