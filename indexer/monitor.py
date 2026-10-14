"""Confirmed-block SQLite event indexer with bounded reorg rollback. Python 3.11+."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import signal
import sqlite3
import time
from typing import Any
from indexer.events import decode
from zzz_ops.abi import address
from zzz_ops.rpc import Rpc,RpcError
from zzz_ops.state import integer, process_lock

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
    def header(self,number:int)->dict[str,Any]|None:
        return self.rpc.call('eth_getBlockByNumber',[hex(number),False])
    def reconcile(self)->int:
        rows=self.db.execute('SELECT number,hash FROM blocks WHERE chain=? ORDER BY number DESC LIMIT ?',
            (self.chain,self.max_reorg+1)).fetchall()
        if not rows:return 0
        ancestor=None;removed=0
        for number,stored_hash in rows:
            remote=self.header(number)
            if remote and remote['hash'].lower()==stored_hash:
                ancestor=number;break
            removed+=1
            if removed>self.max_reorg:raise RpcError('Reorg exceeds configured safety bound; manual reconciliation required')
        if removed==0:return 0
        rollback=self.start if ancestor is None else ancestor+1
        with self.db:
            self.db.execute('DELETE FROM blocks WHERE chain=? AND number>=?',(self.chain,rollback))
            self.db.execute('UPDATE cursors SET next_block=? WHERE chain=?',(rollback,self.chain))
        return removed

    def step(self)->int:
        self.reconcile()
        head=int(self.rpc.call('eth_blockNumber',[]),16)
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
        previous=self.db.execute('SELECT hash FROM blocks WHERE chain=? AND number=?',(self.chain,start-1)).fetchone()
        parent=previous[0] if previous else self.config.get('start_parent_hash')
        for number in range(start,end+1):
            h=self.header(number)
            if h is None or int(h['number'],16)!=number:raise RpcError('Missing or misnumbered block')
            if parent is not None and h['parentHash'].lower()!=parent.lower():raise RpcError('Non-contiguous block ancestry')
            headers[number]=h;parent=h['hash']
        last=self.header(end)
        if last is None or last['hash'].lower()!=headers[end]['hash'].lower():raise RpcError('Chain changed during log fetch')
        prepared=[]
        for item in logs:
            number=int(item['blockNumber'],16)
            if number not in headers or item.get('removed') or item['blockHash'].lower()!=headers[number]['hash'].lower():
                raise RpcError('Log does not belong to the confirmed block range')
            contract=address(item['address'])
            if contract not in self.contracts:raise RpcError('Unexpected contract in log response')
            event,decoded=decode(item)
            prepared.append((self.chain,number,item['blockHash'].lower(),item['transactionHash'].lower(),
                int(item['logIndex'],16),contract,event,json.dumps(decoded,sort_keys=True) if decoded is not None else None,
                json.dumps(item,sort_keys=True)))
        with self.db:
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
    args=parser.parse_args();config=json.loads(Path(args.config).read_text())
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
                    print(json.dumps({'event':'indexer_error','error_type':type(exc).__name__}),flush=True)
                    if args.once:raise
                    count=0
                if args.once:break
                if count==0:
                    for _ in range(index.poll_seconds):
                        if stop:break
                        time.sleep(1)
        finally:index.close()

if __name__=='__main__':main()
