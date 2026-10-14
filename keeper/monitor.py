"""ZZZKeeper: serial, dry-run-by-default automation. Python 3.11+, Linux.

Live signing is delegated to a local Foundry `cast` encrypted keystore. No private
key is accepted by this program. Ambiguous broadcasts stop further submissions.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import time
from typing import Any
from zzz_ops.abi import address, calldata, decode_words, keccak256, uint_result
from zzz_ops.rpc import Rpc, RpcError
from zzz_ops.state import atomic_json, process_lock, read_json

def log(event: str, **fields: Any) -> None:
    print(json.dumps({'time':dt.datetime.now(dt.timezone.utc).isoformat(),'event':event,**fields},sort_keys=True),flush=True)

def positive(value: Any, field: str, *, zero: bool = False) -> int:
    if isinstance(value,bool): raise ValueError(f'{field} must be an integer')
    n = int(value)
    if n < (0 if zero else 1): raise ValueError(f'{field} must be positive')
    return n

class Keeper:
    def __init__(self, config: dict[str,Any], *, live: bool = False, rpc: Rpc | None = None):
        self.config, self.live = config, live
        self.chain = positive(config['chain_id'],'chain_id')
        self.rpc = rpc or Rpc(config['rpc_urls'],self.chain)
        self.sender = address(config['sender'])
        self.contracts = {k:address(v) for k,v in config['contracts'].items()}
        for name in ('access','vault','strategy','fees','compounder','buyback'):
            if name not in self.contracts: raise ValueError(f'Missing contract: {name}')
        self.path = Path(config.get('state_path','var/keeper.json'))
        self.state = read_json(self.path,{'chain_id':self.chain,'sender':self.sender,'last':{},'spent':{},'pending':None})
        if self.state['chain_id'] != self.chain or self.state['sender'] != self.sender:
            raise ValueError('Persistent state belongs to another chain or sender')
        self.confirmations = positive(config.get('confirmations',12),'confirmations')
        if self.live:
            if config.get('reviewed_for_live_use') is not True:
                raise ValueError('Live use requires an explicit reviewed deployment configuration')
            self._validate_signer()
            self._validate_code_hashes()

    def save(self) -> None: atomic_json(self.path,self.state)
    def view(self,name: str,signature: str,*args: int|str) -> int:
        return uint_result(self.rpc.eth_call(self.contracts[name],calldata(signature,*args)))

    def _validate_signer(self) -> None:
        self.cast = shutil.which(self.config.get('cast_binary','cast'))
        if not self.cast: raise ValueError('Foundry cast is required for live signing')
        self.keystore = Path(self.config['keystore']).resolve()
        self.password = Path(self.config['password_file']).resolve()
        for path in (self.keystore,self.password):
            st = path.stat()
            if not stat.S_ISREG(st.st_mode) or st.st_mode & 0o077:
                raise ValueError('Signing files must be regular files with mode 0600')
            if st.st_uid != os.getuid(): raise ValueError('Signing files must belong to the keeper user')
        result = subprocess.run([self.cast,'wallet','address','--keystore',str(self.keystore),
            '--password-file',str(self.password)],capture_output=True,text=True,timeout=30,check=False)
        if result.returncode or address(result.stdout.strip()) != self.sender:
            raise ValueError('Encrypted keystore does not match configured sender')

    def _validate_code_hashes(self) -> None:
        hashes = self.config.get('code_hashes',{})
        for name,contract in self.contracts.items():
            expected = hashes.get(name,'').lower()
            if not re.fullmatch(r'0x[0-9a-f]{64}',expected): raise ValueError(f'Missing reviewed code hash: {name}')
            code = self.rpc.call('eth_getCode',[contract,'latest'])
            if code == '0x' or '0x'+keccak256(bytes.fromhex(code[2:])).hex() != expected:
                raise ValueError(f'Deployment bytecode mismatch: {name}')

    def _head(self) -> tuple[int,int]:
        head = self.rpc.call('eth_getBlockByNumber',['latest',False])
        number,timestamp = int(head['number'],16),int(head['timestamp'],16)
        if abs(time.time()-timestamp) > 600: raise RpcError('RPC head timestamp is stale or implausible')
        return number,timestamp

    def poll_pending(self) -> bool:
        pending = self.state.get('pending')
        if not pending: return False
        tx_hash = pending.get('hash')
        if not tx_hash:
            log('broadcast_ambiguous',nonce=pending['nonce'],action=pending['key'])
            return True
        receipt = self.rpc.call('eth_getTransactionReceipt',[tx_hash])
        if receipt is None:
            log('pending',transaction=tx_hash)
            return True
        head,_ = self._head()
        block = int(receipt['blockNumber'],16)
        if head-block+1 < self.confirmations: return True
        header = self.rpc.call('eth_getBlockByNumber',[hex(block),False])
        if header is None or header['hash'].lower() != receipt['blockHash'].lower():
            log('receipt_reorged',transaction=tx_hash); return True
        transaction = self.rpc.call('eth_getTransactionByHash',[tx_hash])
        if not transaction or address(transaction['from']) != self.sender or int(transaction['nonce'],16) != pending['nonce'] or \
            address(transaction['to']) != pending['to'] or transaction['input'].lower() != pending['data'].lower() or \
            int(transaction.get('value','0x0'),16) != pending['value']:
            raise RpcError('Pending transaction identity mismatch')
        success = int(receipt['status'],16) == 1
        gas_price = int(receipt.get('effectiveGasPrice',transaction.get('gasPrice','0x0')),16)
        cost = int(receipt['gasUsed'],16)*gas_price + (pending['value'] if success else 0)
        l1_fee = receipt.get('l1Fee','0x0')
        cost += int(l1_fee,16) if isinstance(l1_fee,str) and l1_fee.startswith('0x') else int(l1_fee)
        day = pending['day']
        self.state['spent'][day] = int(self.state['spent'].get(day,0)) + cost
        if success: self.state['last'][pending['key']] = int(header['timestamp'],16)
        self.state['pending'] = None; self.save()
        log('confirmed' if success else 'reverted',transaction=tx_hash,cost_wei=str(cost),action=pending['key'])
        return False

    def resolve_pending(self, tx_hash: str) -> None:
        if not re.fullmatch(r'0x[0-9a-fA-F]{64}',tx_hash): raise ValueError('Invalid transaction hash')
        if not self.state.get('pending'): raise ValueError('No ambiguous submission exists')
        self.state['pending']['hash'] = tx_hash.lower(); self.save()
        self.poll_pending()  # Independently checks sender, nonce, target and calldata.

    def submit(self, name: str, signature: str, args: tuple[int|str,...], key: str, *, value: int = 0) -> bool:
        if self.state.get('pending'): return False
        _,timestamp = self._head()
        to,data = self.contracts[name],calldata(signature,*args)
        tx = {'from':self.sender,'to':to,'data':data,'value':hex(value)}
        self.rpc.call('eth_call',[tx,'latest'])
        estimated = int(self.rpc.call('eth_estimateGas',[tx]),16)
        gas_limit = (estimated*125+99)//100
        gas_price = int(self.rpc.call('eth_gasPrice',[]),16)
        if gas_limit > positive(self.config['max_gas_limit'],'max_gas_limit') or \
            gas_price > positive(self.config['max_gas_price_wei'],'max_gas_price_wei'):
            log('gas_cap_exceeded',action=key); return False
        cost = gas_limit*gas_price + value + positive(self.config.get('l1_fee_allowance_wei',0),'l1_fee_allowance_wei',zero=True)
        day = dt.datetime.fromtimestamp(timestamp,dt.timezone.utc).date().isoformat()
        if cost > positive(self.config['max_transaction_cost_wei'],'max_transaction_cost_wei') or \
            int(self.state['spent'].get(day,0))+cost > positive(self.config['max_daily_cost_wei'],'max_daily_cost_wei'):
            log('cost_cap_exceeded',action=key); return False
        if not self.live:
            log('dry_run',action=key,to=to,calldata=data,estimated_cost_wei=str(cost))
            return False
        # Revalidate code after simulation and before signing; stop on mutable deployments.
        self._validate_code_hashes()
        nonce = int(self.rpc.call('eth_getTransactionCount',[self.sender,'pending']),16)
        pending = {'key':key,'nonce':nonce,'to':to,'data':data,'value':value,'day':day,'hash':None}
        self.state['pending'] = pending; self.save()  # Durable BEFORE the external signer can broadcast.
        command = [self.cast,'send',to,'--data',data,'--keystore',str(self.keystore),
            '--password-file',str(self.password),'--chain',str(self.chain),'--nonce',str(nonce),
            '--gas-limit',str(gas_limit),'--gas-price',str(gas_price),'--value',str(value),'--async','--json']
        environment = dict(os.environ,ETH_RPC_URL=self.rpc.active_url)
        try:
            result = subprocess.run(command,env=environment,capture_output=True,text=True,timeout=90,check=False)
            if result.returncode: raise RuntimeError('Signer command failed; broadcast status must be checked')
            try: parsed = json.loads(result.stdout)
            except json.JSONDecodeError: parsed = result.stdout.strip()
            candidate = parsed.get('transactionHash',parsed.get('hash')) if isinstance(parsed,dict) else parsed
            if not isinstance(candidate,str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}',candidate):
                raise RuntimeError('Signer did not return a transaction hash')
            pending['hash'] = candidate.lower(); self.save()
            log('submitted',action=key,transaction=candidate)
        except Exception as exc:
            # Deliberately retain pending state. NEVER automatically resubmit on timeout.
            log('submission_requires_reconciliation',action=key,error_type=type(exc).__name__)
            raise
        return True

    def cycle(self) -> None:
        if self.poll_pending(): return
        if self.view('access','paused()') != 0:
            log('protocol_paused'); return
        if self.view('access','isSealed()') != 1: raise RpcError('Protocol is not sealed')
        if self.view('access','keepers(address)',self.sender) != 1: raise RpcError('Configured sender is not an authorized keeper')
        _,now = self._head()
        for item in self.config.get('positions',[]):
            nft = positive(item['nft_id'],'nft_id')
            minimum = positive(item['minimum_liquidity'],'minimum_liquidity')
            try:
                fields = decode_words(self.rpc.eth_call(self.contracts['vault'],calldata('position(uint256)',nft)))
                if len(fields) != 15: raise RpcError('Unexpected vault Position ABI')
                if int(fields[7],16) != 1: continue
                _,fresh = self._head(); deadline = fresh+180
                if self.view('strategy','needsRebalance(uint256)',nft):
                    if self.submit('vault','rebalance(uint256,uint128,uint256)',(nft,minimum,deadline),f'rebalance:{nft}'): return
                if item.get('compound'):
                    tokens = [address(t) for t in item['tokens']]
                    reserves = [self.view('fees','compoundBalance(uint256,address)',nft,t) for t in tokens]
                    threshold = positive(item.get('minimum_compound_units',1),'minimum_compound_units')
                    if max(reserves,default=0) >= threshold:
                        if self.submit('compounder','compound(uint256,uint128,uint256)',(nft,minimum,deadline),f'compound:{nft}'): return
                interval = positive(item.get('harvest_interval_seconds',14400),'harvest_interval_seconds')
                if item.get('harvest') and now-int(self.state['last'].get(f'harvest:{nft}',0)) >= interval:
                    if self.submit('vault','collectFees(uint256,uint256)',(nft,deadline),f'harvest:{nft}'): return
                for remote in item.get('reward_routes',[]):
                    token = address(remote['token'])
                    personal = self.view('fees','remoteIndividual(uint256,address)',nft,token)
                    shared = self.view('fees','remoteCollective(uint256,address)',nft,token)
                    if personal+shared >= positive(remote['minimum_units'],'minimum_units'):
                        if self.submit('fees','bridgeRewards(uint256,address,bytes32)',(nft,token,remote['route_id']),
                            f'bridge_rewards:{nft}:{token}',value=positive(remote.get('native_fee_wei',0),'native_fee_wei',zero=True)): return
            except (ValueError,RpcError) as exc:
                log('position_skipped',nft_id=str(nft),error_type=type(exc).__name__)
        for task in self.config.get('buybacks',[]):
            token = address(task['token']); amount = positive(task['amount'],'amount')
            if self.view('fees','buybackBalance(address)',token) >= amount:
                _,fresh = self._head()
                if self.submit('buyback','execute(address,uint256,bytes32,uint256)',(token,amount,task['pool_id'],fresh+180),f'buyback:{token}'): return

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',required=True);parser.add_argument('--live',action='store_true')
    parser.add_argument('--once',action='store_true');parser.add_argument('--resolve-pending')
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    interval = positive(config.get('interval_seconds',600),'interval_seconds')
    if interval < 60: raise ValueError('Polling interval must be at least 60 seconds')
    stop = False
    def halt(*_: Any) -> None:
        nonlocal stop;stop=True
    signal.signal(signal.SIGINT,halt);signal.signal(signal.SIGTERM,halt)
    with process_lock(config.get('lock_path','var/keeper.lock')):
        keeper = Keeper(config,live=args.live)
        if args.resolve_pending:
            keeper.resolve_pending(args.resolve_pending);return
        while not stop:
            try: keeper.cycle()
            except Exception as exc:
                log('cycle_failed',error_type=type(exc).__name__)
                if args.once: raise
            if args.once: break
            for _ in range(interval):
                if stop: break
                time.sleep(1)

if __name__ == '__main__': main()
