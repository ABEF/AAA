"""Confirmed-block SQLite event indexer with bounded reorg rollback. Python 3.11+."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import signal
import sqlite3
import time
from typing import Any
from indexer.events import decode
from zzz_ops.abi import address
from zzz_ops.rpc import Rpc,RpcError
from zzz_ops.state import integer, process_lock, read_json
from zzz_ops.log_provenance import OrderedTransactions

class IndexerSafetyError(RpcError):
    """A public, fixed diagnostic; provider payloads and URLs are never included."""
    def __init__(self,code:str,message:str):
        super().__init__(message);self.code=code

def _header_hash(value:Any,*,nonzero:bool=False)->str:
    if not isinstance(value,str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}',value) or (nonzero and int(value,16)==0):
        raise IndexerSafetyError('invalid_header','Malformed block header; retained history is unchanged')
    return value.lower()

def _header_quantity(value:Any)->int:
    if not isinstance(value,str) or not re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]*)',value):
        raise IndexerSafetyError('invalid_header','Malformed block header quantity; retained history is unchanged')
    number=int(value,16)
    if number>2**63-1:
        raise IndexerSafetyError('invalid_header','Block header exceeds the supported database range')
    return number

MAX_RAW_LOG = 131072

def _log_quantity(value:Any)->int:
    if not isinstance(value,str) or not re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]{0,15})',value):
        raise IndexerSafetyError('invalid_log','Malformed log quantity; retained history is unchanged')
    number=int(value,16)
    if number>2**63-1:
        raise IndexerSafetyError('invalid_log','Log quantity exceeds the supported database range')
    return number

def _log_hash(value:Any)->str:
    if not isinstance(value,str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}',value) or int(value,16)==0:
        raise IndexerSafetyError('invalid_log','Malformed log hash; retained history is unchanged')
    return value.lower()

class Indexer:
    def __init__(self,config:dict[str,Any],rpc:Rpc|None=None):
        self.config=config
        self.chain=integer(config['chain_id'],'chain_id',minimum=1)
        self.start=integer(config['start_block'],'start_block')
        self.confirmations=integer(config.get('confirmations',12),'confirmations',minimum=1)
        self.chunk=integer(config.get('block_chunk',100),'block_chunk',minimum=1)
        self.max_reorg=integer(config.get('max_reorg_depth',256),'max_reorg_depth',minimum=1)
        self.poll_seconds=integer(config.get('poll_seconds',15),'poll_seconds',minimum=1)
        self.contracts=[address(a) for a in config['contracts']]
        if not self.contracts: raise ValueError('At least one contract is required')
        self.rpc=rpc or Rpc(config['rpc_urls'],self.chain)
        path=Path(config.get('database','var/indexer.sqlite'))
        path.parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(path,timeout=10)
        self.db.execute('PRAGMA journal_mode=WAL');self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS cursors(chain INTEGER PRIMARY KEY,next_block INTEGER NOT NULL,config TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS blocks(chain INTEGER,number INTEGER,hash TEXT NOT NULL,parent TEXT NOT NULL,timestamp INTEGER NOT NULL,
          PRIMARY KEY(chain,number));
        CREATE TABLE IF NOT EXISTS logs(chain INTEGER,block_number INTEGER,block_hash TEXT,transaction_hash TEXT,log_index INTEGER,
          address TEXT,event TEXT,decoded TEXT,raw TEXT NOT NULL,PRIMARY KEY(chain,transaction_hash,log_index),
          FOREIGN KEY(chain,block_number) REFERENCES blocks(chain,number) ON DELETE CASCADE);
        CREATE INDEX IF NOT EXISTS event_lookup ON logs(chain,address,event,block_number);
        CREATE INDEX IF NOT EXISTS block_log_lookup ON logs(chain,block_number,log_index);
        ''')
        identity=json.dumps({'contracts':sorted(self.contracts),'start':self.start,
            'parent_hash':config.get('start_parent_hash')},sort_keys=True)
        cursor=self.db.execute('SELECT config FROM cursors WHERE chain=?',(self.chain,)).fetchone()
        if cursor and cursor[0]!=identity:
            self.db.close()
            raise ValueError('Indexer identity changed; use a separate database or explicit rescan')
        with self.db:self.db.execute('INSERT OR IGNORE INTO cursors VALUES(?,?,?)',(self.chain,self.start,identity))

    @property
    def next_block(self)->int:
        return self.db.execute('SELECT next_block FROM cursors WHERE chain=?',(self.chain,)).fetchone()[0]
    def header(self,number:int)->dict[str,Any]:
        value=self.rpc.call('eth_getBlockByNumber',[hex(number),False])
        if value is None:
            raise IndexerSafetyError('header_unavailable','RPC block history is unavailable; retry a reviewed endpoint without resetting the database')
        if not isinstance(value,dict) or _header_quantity(value.get('number'))!=number:
            raise IndexerSafetyError('invalid_header','Missing or misnumbered block header; retained history is unchanged')
        return {'number':hex(number),'hash':_header_hash(value.get('hash'),nonzero=True),
            'parentHash':_header_hash(value.get('parentHash')),'timestamp':hex(_header_quantity(value.get('timestamp')))}
    def reconcile(self)->int:
        rows=self.db.execute('SELECT number,hash,parent,timestamp FROM blocks WHERE chain=? ORDER BY number DESC LIMIT ?',
            (self.chain,self.max_reorg+1)).fetchall()
        if not rows:return 0
        tip=self.next_block-1
        if rows[0][0]!=tip:
            raise IndexerSafetyError('database_boundary','Stored blocks and cursor disagree; preserve the database for operator review')
        ancestor=None;removed=0;child_parent=None;proof=None
        for number,stored_hash,stored_parent,stored_timestamp in rows:
            if number!=tip-removed:
                raise IndexerSafetyError('database_boundary','Stored history is not contiguous; preserve the database for operator review')
            remote=self.header(number)
            if child_parent is not None and remote['hash']!=child_parent:
                raise IndexerSafetyError('unstable_ancestry','RPC ancestry changed during reconciliation; retry without resetting the database')
            if remote['hash']==stored_hash:
                if remote['parentHash']!=stored_parent or int(remote['timestamp'],16)!=stored_timestamp:
                    raise IndexerSafetyError('inconsistent_header','RPC metadata disagrees for the same block hash; preserve the database and review the endpoint')
                ancestor=number;proof=remote;break
            removed+=1
            if removed>self.max_reorg:
                raise IndexerSafetyError('reorg_depth','Reorg exceeds configured safety bound; manual reconciliation required')
            child_parent=remote['parentHash'];proof=remote
        if removed==0:return 0
        if ancestor is None:
            anchor=self.config.get('start_parent_hash')
            if rows[-1][0]!=self.start or self.start==0 or anchor is None or proof['parentHash']!=_header_hash(anchor):
                raise IndexerSafetyError('unproved_ancestor','No reviewed common ancestor was proved; preserve the database for operator reconciliation')
        boundary=ancestor if ancestor is not None else self.start
        if self.header(boundary)!=proof:
            raise IndexerSafetyError('unstable_ancestry','RPC ancestry changed during reconciliation; retry without resetting the database')
        rollback=self.start if ancestor is None else ancestor+1
        # All RPC reads and the complete ancestry proof precede any destructive write.
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            current=self.db.execute('SELECT number,hash,parent,timestamp FROM blocks WHERE chain=? ORDER BY number DESC LIMIT ?',
                (self.chain,self.max_reorg+1)).fetchall()
            if current!=rows or self.next_block!=tip+1:
                raise IndexerSafetyError('database_changed','Indexer state changed during reconciliation; retry with one writer')
            self.db.execute('DELETE FROM blocks WHERE chain=? AND number>=?',(self.chain,rollback))
            self.db.execute('UPDATE cursors SET next_block=? WHERE chain=?',(rollback,self.chain))
        return removed

    def step(self)->int:
        self.reconcile()
        head=_header_quantity(self.rpc.call('eth_blockNumber',[]))
        safe=head-self.confirmations+1
        start=self.next_block
        if start>safe:return 0
        end=min(safe,start+self.chunk-1)
        while True:
            try:
                logs=self.rpc.call('eth_getLogs',[{'address':self.contracts,'fromBlock':hex(start),'toBlock':hex(end)}]);break
            except RpcError:
                if end==start:raise
                end=start+(end-start)//2
        if not isinstance(logs,list):raise RpcError('Malformed eth_getLogs result')
        headers={}
        previous=self.db.execute('SELECT hash,parent,timestamp FROM blocks WHERE chain=? AND number=?',(self.chain,start-1)).fetchone()
        parent=previous[0] if previous else self.config.get('start_parent_hash')
        parent_timestamp=previous[2] if previous else None
        for number in range(start,end+1):
            h=self.header(number)
            if parent is not None and h['parentHash'].lower()!=parent.lower():raise RpcError('Non-contiguous block ancestry')
            timestamp=int(h['timestamp'],16)
            if parent_timestamp is not None and timestamp<parent_timestamp:
                raise IndexerSafetyError('invalid_timestamp','Block timestamps regress; retained history is unchanged')
            # Equal timestamps are valid for supported L2s. A configured hash
            # alone supplies no timestamp for an unindexed starting parent.
            headers[number]=h;parent=h['hash'];parent_timestamp=timestamp
        prepared=[];seen_logs=set();transaction_blocks={};ordered_logs=[]
        for item in logs:
            if not isinstance(item,dict) or item.get('removed') is not False:
                raise IndexerSafetyError('invalid_log','Malformed or removed log; retained history is unchanged')
            number=_log_quantity(item.get('blockNumber'))
            block_hash=_log_hash(item.get('blockHash'))
            transaction_hash=_log_hash(item.get('transactionHash'))
            log_index=_log_quantity(item.get('logIndex'))
            if number not in headers or block_hash!=headers[number]['hash']:
                raise IndexerSafetyError('invalid_log','Log is outside the confirmed block range')
            try:contract=address(item.get('address'))
            except (ValueError,TypeError,AttributeError):
                raise IndexerSafetyError('invalid_log','Malformed log emitter; retained history is unchanged') from None
            if contract not in self.contracts:
                raise IndexerSafetyError('invalid_log','Unexpected log emitter; retained history is unchanged')
            topics=item.get('topics');data=item.get('data')
            if (not isinstance(topics,list) or len(topics)>4 or
                    any(not isinstance(t,str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}',t) for t in topics) or
                    not isinstance(data,str) or len(data)>MAX_RAW_LOG or
                    not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*',data)):
                raise IndexerSafetyError('invalid_log','Malformed log topics or data; retained history is unchanged')
            transaction_index=_log_quantity(item['transactionIndex']) if 'transactionIndex' in item else None
            try:
                raw=json.dumps(item,sort_keys=True,allow_nan=False)
                if len(raw)>MAX_RAW_LOG:raise ValueError()
                event,decoded=decode(item)
            except (ValueError,TypeError,KeyError,AttributeError,RecursionError):
                raise IndexerSafetyError('invalid_log','Malformed or oversized raw event; retained history is unchanged') from None
            if ((number,log_index) in seen_logs or
                    transaction_hash in transaction_blocks and transaction_blocks[transaction_hash]!=number):
                raise IndexerSafetyError('duplicate_log','Conflicting log provenance; retained history is unchanged')
            seen_logs.add((number,log_index));transaction_blocks[transaction_hash]=number
            ordered_logs.append((number,log_index,transaction_hash,transaction_index))
            prepared.append((self.chain,number,block_hash,transaction_hash,log_index,contract,event,
                json.dumps(decoded,sort_keys=True) if decoded is not None else None,raw))
        # Providers may return valid filtered logs out of order. Validate their
        # canonical sequence before any durable write, including unknown events.
        chronology=OrderedTransactions()
        try:
            for row in sorted(ordered_logs,key=lambda row:row[:2]):chronology.add(*row)
        except ValueError:
            raise IndexerSafetyError('invalid_transaction_order','Contradictory transaction provenance; retained history is unchanged') from None
        # Failover may retain this tip while losing its confirming descendants.
        # Recheck after decoding too; prepared data has not changed the database.
        final_head=_header_quantity(self.rpc.call('eth_blockNumber',[]))
        if final_head<end+self.confirmations-1:
            raise IndexerSafetyError('confirmation_depth','Indexed chunk lost its required confirmation depth; no new blocks were stored')
        if self.header(end)!=headers[end]:raise RpcError('Chain changed during log fetch')
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            current_previous=self.db.execute('SELECT hash,parent,timestamp FROM blocks WHERE chain=? AND number=?',
                (self.chain,start-1)).fetchone()
            if self.next_block!=start or current_previous!=previous:
                # A concurrent reorg/reingestion can restore the same cursor
                # while changing the parent to which this batch would attach.
                raise IndexerSafetyError('database_changed','Indexer boundary changed during ingestion; retry with one writer')
            # One indexed, LIMIT-1 lookup per distinct incoming transaction.
            # No history list is materialized, and every check precedes INSERT.
            for transaction_hash,number in transaction_blocks.items():
                if self.db.execute('SELECT 1 FROM logs WHERE chain=? AND transaction_hash=? AND block_number!=? LIMIT 1',
                        (self.chain,transaction_hash,number)).fetchone():
                    raise IndexerSafetyError('duplicate_log','Transaction conflicts with retained history; no new blocks were stored')
            for number,h in headers.items():
                self.db.execute('INSERT INTO blocks VALUES(?,?,?,?,?)',(self.chain,number,h['hash'].lower(),h['parentHash'].lower(),int(h['timestamp'],16)))
            self.db.executemany('INSERT INTO logs VALUES(?,?,?,?,?,?,?,?,?)',prepared)
            self.db.execute('UPDATE cursors SET next_block=? WHERE chain=?',(end+1,self.chain))
        return len(headers)

    def nft_owners(self,nft_contract:str)->dict[str,str]:
        owners={};contract=address(nft_contract)
        rows=self.db.execute("SELECT decoded FROM logs WHERE chain=? AND address=? AND event='Transfer' ORDER BY block_number,log_index",
            (self.chain,contract)).fetchall()
        for (decoded,) in rows:
            if decoded:
                item=json.loads(decoded)
                if int(item['to'],16)==0:owners.pop(item['tokenId'],None)
                else:owners[item['tokenId']]=item['to']
        return owners
    def close(self)->None:self.db.close()

def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',required=True);parser.add_argument('--once',action='store_true')
    args=parser.parse_args()
    missing=object()
    try:config=read_json(args.config,missing)
    except (ValueError,RecursionError):
        raise ValueError('Invalid indexer configuration JSON') from None
    if config is missing:raise FileNotFoundError('Indexer configuration is missing')
    if not isinstance(config,dict):raise ValueError('Indexer configuration must be a JSON object')
    stop=False
    def halt(*_:Any)->None:
        nonlocal stop;stop=True
    signal.signal(signal.SIGINT,halt);signal.signal(signal.SIGTERM,halt)
    with process_lock(config.get('lock_path','var/indexer.lock')):
        index=Indexer(config)
        try:
            while not stop:
                try:
                    count=index.step()
                    print(json.dumps({'event':'indexed','blocks':count,'next_block':index.next_block}),flush=True)
                except Exception as exc:
                    error={'event':'indexer_error','error_type':type(exc).__name__}
                    if isinstance(exc,IndexerSafetyError):error['reason']=exc.code
                    print(json.dumps(error),flush=True)
                    if args.once:raise
                    count=0
                if args.once:break
                if count==0:
                    for _ in range(index.poll_seconds):
                        if stop:break
                        time.sleep(1)
        finally:index.close()

if __name__=='__main__':main()
