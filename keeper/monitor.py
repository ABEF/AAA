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
from zzz_ops.state import atomic_json, integer, process_lock, read_json

ACCOUNTING_MODEL = 'shared-pools-v2'
MAX_METADATA_SUPPLY = 1000
MAX_METADATA_BATCH = 50

def log(event: str, **fields: Any) -> None:
    print(json.dumps({'time':dt.datetime.now(dt.timezone.utc).isoformat(),'event':event,**fields},sort_keys=True),flush=True)

def positive(value: Any, field: str, *, zero: bool = False) -> int:
    return integer(value,field,minimum=0 if zero else 1)

def signer_environment(rpc_url: str | None = None) -> dict[str,str]:
    """Keep host/runtime settings, excluding ambient Foundry wallet/tx overrides."""
    blocked = ('ETH_', 'ETHERSCAN_', 'CAST_', 'FOUNDRY_', 'AWS_', 'GCP_')
    environment = {key:value for key,value in os.environ.items()
        if not key.startswith(blocked) and key not in ('CHAIN','PRIVATE_KEY','MNEMONIC','MNEMONIC_PASSPHRASE')}
    if rpc_url is not None: environment['ETH_RPC_URL'] = rpc_url
    return environment

class Keeper:
    def __init__(self, config: dict[str,Any], *, live: bool = False, rpc: Rpc | None = None):
        self.config, self.live = config, live
        self.chain = positive(config['chain_id'],'chain_id')
        self.rpc = rpc or Rpc(config['rpc_urls'],self.chain)
        self.sender = address(config['sender'])
        self.contracts = {k:address(v) for k,v in config['contracts'].items()}
        for name in ('access','vault','strategy','fees','compounder','buyback','pools'):
            if name not in self.contracts: raise ValueError(f'Missing contract: {name}')
        if 'positions' in config or config.get('accounting_model',ACCOUNTING_MODEL) != ACCOUNTING_MODEL:
            raise ValueError('Keeper configuration must use the shared-pool accounting model')
        discovery = config.get('bucket_discovery',{})
        if not isinstance(discovery,dict): raise ValueError('Bucket discovery settings must be an object')
        self.max_buckets = positive(discovery.get('maximum_count',10000),'bucket_discovery.maximum_count')
        self.batch_size = positive(discovery.get('max_per_cycle',32),'bucket_discovery.max_per_cycle')
        if self.max_buckets > 100000 or self.batch_size > min(self.max_buckets,1000):
            raise ValueError('Bucket discovery exceeds its bounded scan limits')
        self.maintenance = config.get('maintenance',{})
        self.overrides = config.get('bucket_overrides',{})
        if not isinstance(self.maintenance,dict) or not isinstance(self.overrides,dict):
            raise ValueError('Maintenance defaults and bucket overrides must be objects')
        for bucket,settings in self.overrides.items():
            if str(positive(bucket,'bucket_overrides key')) != bucket or not isinstance(settings,dict):
                raise ValueError('Bucket overrides require canonical decimal bucket IDs and object settings')
        for settings in (self.maintenance,*self.overrides.values()):
            if 'sync_external_rewards' in settings and type(settings['sync_external_rewards']) is not bool:
                raise ValueError('sync_external_rewards must be an explicit boolean')
        self.path = Path(config.get('state_path','var/keeper.json'))
        self.state = read_json(self.path,{'chain_id':self.chain,'sender':self.sender,'contracts':self.contracts,'accounting_model':ACCOUNTING_MODEL,
            'bucket_cursor':0,'last':{},'spent':{},'pending':None})
        if self.state['chain_id'] != self.chain or self.state['sender'] != self.sender:
            raise ValueError('Persistent state belongs to another chain or sender')
        if self.state.get('accounting_model') != ACCOUNTING_MODEL:
            raise ValueError('Persistent keeper state requires a reviewed shared-pool migration; preserve pending records')
        if self.state.get('contracts') != self.contracts:
            raise ValueError('Persistent keeper state belongs to another deployment')
        positive(self.state.get('bucket_cursor'),'bucket_cursor',zero=True)
        self.confirmations = positive(config.get('confirmations',12),'confirmations')
        self._configure_metadata()
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
            '--password-file',str(self.password)],env=signer_environment(),
            capture_output=True,text=True,timeout=30,check=False)
        if result.returncode or address(result.stdout.strip()) != self.sender:
            raise ValueError('Encrypted keystore does not match configured sender')

    def _validate_code_hashes(self) -> None:
        hashes = self.config.get('code_hashes',{})
        targets = dict(self.contracts)
        if self.metadata_enabled or (self.state.get('pending') or {}).get('metadata_observation'):
            targets['nft'] = self.metadata_nft
        for name,contract in targets.items():
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
        self._validate_pending_transaction(transaction,pending,tx_hash)
        if receipt.get('transactionHash','').lower() != tx_hash.lower():
            raise RpcError('Pending receipt transaction hash mismatch')
        success = int(receipt['status'],16) == 1
        gas_price = int(receipt.get('effectiveGasPrice',transaction.get('gasPrice','0x0')),16)
        cost = int(receipt['gasUsed'],16)*gas_price + (pending['value'] if success else 0)
        l1_fee = receipt.get('l1Fee','0x0')
        cost += int(l1_fee,16) if isinstance(l1_fee,str) and l1_fee.startswith('0x') else int(l1_fee)
        day = pending['day']
        if success and pending.get('metadata_observation') is not None:
            self._confirm_metadata(pending,block,header['hash'],head)
        self.state['spent'][day] = int(self.state['spent'].get(day,0)) + cost
        if success:
            self.state['last'][pending['key']] = int(header['timestamp'],16)
        self.state['pending'] = None; self.save()
        log('confirmed' if success else 'reverted',transaction=tx_hash,cost_wei=str(cost),action=pending['key'])
        return False

    def resolve_pending(self, tx_hash: str) -> None:
        if not re.fullmatch(r'0x[0-9a-fA-F]{64}',tx_hash): raise ValueError('Invalid transaction hash')
        if not self.state.get('pending'): raise ValueError('No ambiguous submission exists')
        pending = self.state['pending']
        # Verify the human-supplied candidate BEFORE changing durable recovery state.
        transaction = self.rpc.call('eth_getTransactionByHash',[tx_hash])
        self._validate_pending_transaction(transaction,pending,tx_hash)
        pending['hash'] = tx_hash.lower(); self.save()
        self.poll_pending()  # Independently checks sender, nonce, target and calldata.

    def _validate_pending_transaction(self,transaction: Any,pending: dict[str,Any],tx_hash: str) -> None:
        try:
            valid = isinstance(transaction,dict) and transaction.get('hash','').lower() == tx_hash.lower() and \
                address(transaction['from']) == self.sender and int(transaction['nonce'],16) == pending['nonce'] and \
                address(transaction['to']) == pending['to'] and transaction['input'].lower() == pending['data'].lower() and \
                int(transaction.get('value','0x0'),16) == pending['value']
        except (KeyError,TypeError,ValueError,AttributeError):
            valid = False
        if not valid: raise RpcError('Pending transaction identity mismatch')

    def submit(self, name: str, signature: str, args: tuple[int|str,...], key: str, *, value: int = 0,
               metadata_observation: dict[str,Any] | None = None) -> bool:
        if self.state.get('pending'): return False
        _,timestamp = self._head()
        to = self.metadata_nft if name == 'nft' and self.metadata_enabled else self.contracts[name]
        data = calldata(signature,*args)
        if metadata_observation is not None:
            self._validate_metadata_payload(metadata_observation)
            self._metadata_transaction({'to':to,'data':data,'value':value,'key':key,
                'metadata_observation':metadata_observation})
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
        if metadata_observation is not None: pending['metadata_observation'] = metadata_observation
        self.state['pending'] = pending; self.save()  # Durable BEFORE the external signer can broadcast.
        # Foundry 1.4.4 accepts raw calldata as positional SIG; --data is invalid.
        command = [self.cast,'send',to,data,'--from',self.sender,'--keystore',str(self.keystore),
            '--password-file',str(self.password),'--chain',str(self.chain),'--nonce',str(nonce),
            '--gas-limit',str(gas_limit),'--gas-price',str(gas_price),'--value',str(value),'--async','--json']
        environment = signer_environment(self.rpc.active_url)
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

    def _configure_metadata(self) -> None:
        settings = self.config.get('metadata_refresh',{})
        if not isinstance(settings,dict) or type(settings.get('enabled',False)) is not bool:
            raise ValueError('metadata_refresh requires an object and explicit boolean enabled flag')
        self.metadata_enabled = settings.get('enabled',False)
        configured = settings.get('nft')
        self.metadata_nft = address(configured) if configured is not None else None
        self.metadata_maximum = positive(settings.get('maximum_count',MAX_METADATA_SUPPLY),'metadata_refresh.maximum_count')
        self.metadata_scan = positive(settings.get('max_per_cycle',MAX_METADATA_BATCH),'metadata_refresh.max_per_cycle')
        self.metadata_batch = positive(settings.get('max_refresh_batch',min(self.metadata_scan,MAX_METADATA_BATCH)),
            'metadata_refresh.max_refresh_batch')
        self.metadata_age = positive(settings.get('maximum_observation_age_blocks',256),'metadata_refresh.maximum_observation_age_blocks')
        if self.metadata_maximum > MAX_METADATA_SUPPLY or self.metadata_scan > MAX_METADATA_BATCH or \
            self.metadata_batch > min(self.metadata_scan,MAX_METADATA_BATCH) or self.metadata_age > 10000:
            raise ValueError('Metadata discovery or refresh exceeds its bounded limits')
        if self.metadata_enabled and self.metadata_nft is None:
            raise ValueError('Enabled metadata refresh requires an explicit NFT address')
        state = self.state.get('metadata_refresh')
        if state is not None:
            if not isinstance(state,dict) or not isinstance(state.get('identity'),dict):
                raise ValueError('Malformed persistent metadata state')
            identity = state['identity']
            stored_nft = address(identity.get('nft'))
            expected = {'chain_id':self.chain,'controller':self.contracts['access'],'nft':stored_nft}
            if type(identity.get('chain_id')) is not int or identity != expected or \
                self.metadata_nft is not None and self.metadata_nft != stored_nft:
                raise ValueError('Persistent metadata state belongs to another NFT deployment')
            self.metadata_nft = stored_nft
            cursor = positive(state.get('cursor'),'metadata cursor')
            if cursor > MAX_METADATA_SUPPLY or type(state.get('next_first')) is not bool:
                raise ValueError('Malformed metadata scan cursor')
            records = state.get('notified')
            if not isinstance(records,dict) or len(records) > MAX_METADATA_SUPPLY:
                raise ValueError('Malformed notified metadata inventory')
            for ordinal,record in records.items():
                self._validate_metadata_record(record)
                if ordinal != str(record['ordinal']): raise ValueError('Metadata ordinal identity mismatch')
                for prefix in ('observed','notification'):
                    if type(record.get(prefix+'_number')) is not int:
                        raise ValueError('Malformed metadata block number')
                    positive(record.get(prefix+'_number'),prefix+' block',zero=True)
                    self._metadata_hash(record.get(prefix+'_hash'))
                if record['notification_number'] < record['observed_number']:
                    raise ValueError('Metadata notification precedes its observation')
        elif self.metadata_enabled:
            self.state['metadata_refresh'] = {'identity':{'chain_id':self.chain,'controller':self.contracts['access'],
                'nft':self.metadata_nft},'cursor':1,'next_first':True,'notified':{}}
        if self.metadata_nft is not None and 'nft' in self.contracts and self.contracts['nft'] != self.metadata_nft:
            raise ValueError('Conflicting configured NFT addresses')
        pending = self.state.get('pending')
        if pending and pending.get('metadata_observation') is not None:
            self._validate_metadata_payload(pending['metadata_observation'])
            self._metadata_transaction(pending)

    @staticmethod
    def _metadata_hash(value: Any) -> str:
        if not isinstance(value,str) or not re.fullmatch(r'0x[0-9a-f]{64}',value):
            raise ValueError('Malformed metadata block hash')
        return value

    @staticmethod
    def _validate_metadata_record(record: Any) -> None:
        if not isinstance(record,dict): raise ValueError('Malformed metadata observation')
        ordinal = positive(record.get('ordinal'),'metadata ordinal')
        token = positive(record.get('token_id'),'metadata token ID',zero=True)
        if type(record.get('ordinal')) is not int or record.get('token_id') != str(token) or \
            ordinal > MAX_METADATA_SUPPLY or token >= 1 << 256 or \
            type(record.get('available')) is not bool or type(record.get('traits_ready')) is not bool or \
            type(record.get('stage')) is not int or not 0 <= record['stage'] <= 3 or \
            not record['available'] and record['stage'] != 1 or \
            not record['traits_ready'] and (record['stage'] != 0 or not record['available']):
            raise ValueError('Noncanonical metadata state')

    def _validate_metadata_payload(self, payload: Any) -> None:
        state = self.state.get('metadata_refresh')
        if not isinstance(payload,dict) or not state or payload.get('identity') != state['identity']:
            raise ValueError('Pending metadata belongs to another deployment')
        for field in ('first_ordinal','last_ordinal','observed_number','maximum_age'):
            if type(payload.get(field)) is not int: raise ValueError('Malformed pending metadata integer')
        first = positive(payload.get('first_ordinal'),'metadata first ordinal')
        last = positive(payload.get('last_ordinal'),'metadata last ordinal')
        records = payload.get('records')
        if last < first or last > MAX_METADATA_SUPPLY or last-first+1 > MAX_METADATA_BATCH or \
            not isinstance(records,list) or len(records) != last-first+1:
            raise ValueError('Malformed pending metadata range')
        positive(payload.get('observed_number'),'metadata observed block',zero=True)
        self._metadata_hash(payload.get('observed_hash'))
        age = positive(payload.get('maximum_age'),'metadata observation maximum age')
        if age > 10000: raise ValueError('Metadata observation age exceeds bounded limit')
        ids = set()
        for ordinal,record in zip(range(first,last+1),records):
            self._validate_metadata_record(record)
            if record['ordinal'] != ordinal or str(record['token_id']) in ids:
                raise ValueError('Malformed pending metadata token inventory')
            ids.add(str(record['token_id']))

    def _metadata_transaction(self, pending: dict[str,Any]) -> None:
        payload = pending['metadata_observation']
        first,last = payload['first_ordinal'],payload['last_ordinal']
        if pending['to'] != self.metadata_nft or pending['value'] != 0 or \
            pending['key'] != f'metadata:{first}:{last}' or \
            pending['data'] != calldata('refreshMetadataRange(uint256,uint256)',first,last):
            raise ValueError('Pending metadata transaction does not match its observations')

    def _metadata_words(self, target: str, signature: str, block: int, *args: int|str) -> list[int]:
        result = self.rpc.call('eth_call',[{'to':target,'data':calldata(signature,*args)},hex(block)])
        return [int(word,16) for word in decode_words(result)]

    def _metadata_uint(self, target: str, signature: str, block: int, *args: int|str) -> int:
        words = self._metadata_words(target,signature,block,*args)
        if len(words) != 1: raise RpcError('Unexpected metadata getter ABI')
        return words[0]

    def _metadata_anchor(self, number: int, expected_hash: str) -> bool:
        header = self.rpc.call('eth_getBlockByNumber',[hex(number),False])
        return isinstance(header,dict) and header.get('number') == hex(number) and \
            isinstance(header.get('hash'),str) and header['hash'].lower() == expected_hash

    def _metadata_bindings(self, block: int) -> None:
        access,vault = self.contracts['access'],self.contracts['vault']
        reads = ((self.metadata_nft,'access()',(),int(access,16)),
            (access,'module(bytes32)',('0x'+keccak256(b'ZZZNFT').hex(),),int(self.metadata_nft,16)),
            (access,'module(bytes32)',('0x'+keccak256(b'ZZZVault').hex(),),int(vault,16)),
            (vault,'access()',(),int(access,16)),(vault,'canonicalChainId()',(),self.chain),
            (access,'isSealed()',(),1),(self.metadata_nft,'MAX_SUPPLY()',(),MAX_METADATA_SUPPLY),
            (self.metadata_nft,'MAX_METADATA_REFRESH_BATCH()',(),MAX_METADATA_BATCH))
        for target,signature,args,expected in reads:
            if self._metadata_uint(target,signature,block,*args) != expected:
                raise RpcError('Metadata deployment binding or protocol limit mismatch')
        if self.live: self._metadata_code_hash(block)

    def _metadata_code_hash(self, block: int) -> None:
        expected = self.config.get('code_hashes',{}).get('nft','').lower()
        if not re.fullmatch(r'0x[0-9a-f]{64}',expected): raise ValueError('Missing reviewed code hash: nft')
        code = self.rpc.call('eth_getCode',[self.metadata_nft,hex(block)])
        if not isinstance(code,str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+',code) or \
            '0x'+keccak256(bytes.fromhex(code[2:])).hex() != expected:
            raise RpcError('Metadata NFT deployment bytecode mismatch')

    def _metadata_record_at(self, ordinal: int, block: int, expected_token: str | None = None) -> dict[str,Any]:
        token = self._metadata_uint(self.metadata_nft,'tokenAtOrdinal(uint256)',block,ordinal)
        if expected_token is not None and str(token) != expected_token or \
            self._metadata_uint(self.metadata_nft,'mintOrdinalOf(uint256)',block,token) != ordinal:
            raise RpcError('NFT mint ordinal identity mismatch')
        ready = self._metadata_uint(self.metadata_nft,'traitsReady(uint256)',block,token)
        values = self._metadata_words(self.metadata_nft,'evolution(uint256)',block,token)
        if ready not in (0,1) or len(values) != 2 or values[0] not in (0,1):
            raise RpcError('Noncanonical NFT evolution ABI')
        record = {'ordinal':ordinal,'token_id':str(token),'traits_ready':bool(ready),
            'available':bool(values[0]),'stage':values[1]}
        self._validate_metadata_record(record)
        return record

    def _refresh_metadata(self) -> bool:
        """Separate bounded NFT notification scan; never an LP maintenance loop."""
        if not self.metadata_enabled or self.state.get('pending'): return False
        head,_ = self._head()
        block = head-self.confirmations+1
        if block < 0: raise RpcError('Insufficient chain history for confirmed metadata observation')
        header = self.rpc.call('eth_getBlockByNumber',[hex(block),False])
        if not isinstance(header,dict) or header.get('number') != hex(block):
            raise RpcError('Missing pinned metadata observation block')
        block_hash = self._metadata_hash(header.get('hash','').lower())
        self._metadata_bindings(block)
        count = self._metadata_uint(self.metadata_nft,'mintedCount()',block)
        if count > self.metadata_maximum: raise RpcError('NFT inventory exceeds reviewed metadata discovery limit')
        state = self.state['metadata_refresh']
        if count == 0:
            if not self._metadata_anchor(block,block_hash): raise RpcError('Metadata observation block reorged')
            state['cursor'] = 1; self.save(); return False
        first = (positive(state['cursor'],'metadata cursor')-1) % count+1
        records,changed,seen,anchors = [],[],set(),{}
        for offset in range(min(self.metadata_scan,count)):
            ordinal = (first-1+offset) % count+1
            record = self._metadata_record_at(ordinal,block)
            if record['token_id'] in seen: raise RpcError('Duplicate NFT token identity')
            seen.add(record['token_id'])
            records.append(record)
            previous = state['notified'].get(str(ordinal))
            differs = previous is None or any(previous[key] != value for key,value in record.items())
            if previous is not None and not differs:
                for prefix in ('observed','notification'):
                    anchor = (previous[prefix+'_number'],previous[prefix+'_hash'])
                    if anchor not in anchors: anchors[anchor] = self._metadata_anchor(*anchor)
                    if not anchors[anchor]: differs = True
            if differs: changed.append(ordinal)
        if not self._metadata_anchor(block,block_hash): raise RpcError('Metadata observation block reorged')
        if not changed:
            state['cursor'] = records[-1]['ordinal'] % count+1
            self.save(); return False
        start = changed[0]
        end = max(ordinal for ordinal in changed if start <= ordinal < start+self.metadata_batch)
        selected = [record for record in records if start <= record['ordinal'] <= end]
        # Retry unsent trailing work before rescanning a continuously changing
        # prefix, including when a discovery window wraps through ordinal one.
        state['cursor'] = end % count+1
        self.save()  # A fair scan cursor is not a successfully notified baseline.
        payload = {'identity':dict(state['identity']),'observed_number':block,'observed_hash':block_hash,
            'maximum_age':self.metadata_age,'first_ordinal':start,'last_ordinal':end,'records':selected}
        return self.submit('nft','refreshMetadataRange(uint256,uint256)',(start,end),f'metadata:{start}:{end}',
            metadata_observation=payload)

    def _confirm_metadata(self, pending: dict[str,Any], block: int, block_hash: str, head: int) -> None:
        payload = pending['metadata_observation']
        self._validate_metadata_payload(payload)
        self._metadata_transaction(pending)
        observed = payload['observed_number']
        observation_valid = observed <= block and head-observed <= payload['maximum_age'] and \
            self._metadata_anchor(observed,payload['observed_hash'])
        execution_records = []
        if observation_valid:
            self._metadata_bindings(block)
            execution_records = [self._metadata_record_at(record['ordinal'],block,record['token_id'])
                for record in payload['records']]
        if not self._metadata_anchor(block,block_hash.lower()):
            raise RpcError('Metadata confirmation block changed before checkpoint')
        records = self.state['metadata_refresh']['notified']
        if not observation_valid:
            # The event still happened, but its old trigger cannot describe the
            # cache state. Forget prior fingerprints so a retry is never hidden.
            for record in payload['records']: records.pop(str(record['ordinal']),None)
            log('metadata_observation_invalidated',action=pending['key']); return
        for record in execution_records:
            records[str(record['ordinal'])] = {**record,'observed_number':block,
                'observed_hash':block_hash.lower(),'notification_number':block,
                'notification_hash':self._metadata_hash(block_hash.lower())}

    @staticmethod
    def _address_word(word: str) -> str:
        if int(word,16) >= 1 << 160: raise RpcError('Noncanonical address in contract response')
        return address('0x'+word[-40:])

    def _bucket_batch(self) -> list[tuple[int,int]]:
        """Discover a bounded rotating batch of on-chain groups, never NFT IDs."""
        count = self.view('vault','bucketCount()')
        if count > self.max_buckets: raise RpcError('Bucket inventory exceeds reviewed discovery limit')
        if count == 0:
            self.state['bucket_cursor'] = 0
            return []
        start = positive(self.state['bucket_cursor'],'bucket_cursor',zero=True) % count
        batch: list[tuple[int,int]] = []
        seen: set[int] = set()
        for offset in range(min(self.batch_size,count)):
            slot = (start+offset) % count
            bucket = self.view('vault','bucketAt(uint256)',slot)
            if bucket == 0 or bucket in seen:
                raise RpcError('Malformed shared-pool inventory')
            seen.add(bucket); batch.append((slot,bucket))
        return batch

    def _bucket(self,bucket: int) -> tuple[list[str],list[str]]:
        fields = decode_words(self.rpc.eth_call(self.contracts['vault'],calldata('group(uint256)',bucket)))
        if len(fields) != 15: raise RpcError('Unexpected vault group ABI')
        status = int(fields[7],16)
        if status not in (1,2,3,4,6): return fields,[]
        if int(fields[0],16) == 0 or int(fields[5],16) >= 1 << 160 or int(fields[6],16) >= 1 << 64:
            raise RpcError('Malformed shared-pool state')
        if int(fields[8],16) == 0 or int(fields[13],16) == 0:
            raise RpcError('Missing shared-pool provenance')
        for index in (9,10,11,12,14): self._address_word(fields[index])
        if self.view('vault','bucketTotalShares(uint256)',bucket) == 0:
            raise RpcError('Shared pool has no shares')
        pool_id = '0x'+fields[0]
        if self.view('vault','poolBucket(bytes32)',pool_id) != bucket:
            raise RpcError('Pool occupancy does not match discovered bucket')
        if status == 1 and int(fields[1],16) == 0:
            raise RpcError('Active shared pool has no LP position')
        if status == 6 and int(fields[1],16) != 0:
            raise RpcError('Parked shared pool still has an LP position')
        if status == 6 and (int(fields[13],16) != self.chain or
                self._address_word(fields[14]) != self.contracts['vault']):
            raise RpcError('Parked principal is not in this local vault')
        config = decode_words(self.rpc.eth_call(self.contracts['pools'],calldata('get(bytes32)',pool_id)))
        if len(config) != 14 or '0x'+keccak256(bytes.fromhex(''.join(config[:5]))).hex() != pool_id:
            raise RpcError('Pool configuration does not match its identity')
        if int(config[0],16) >= int(config[1],16): raise RpcError('Invalid venue currency ordering')
        accounting = decode_words(self.rpc.eth_call(self.contracts['pools'],calldata('accounting(bytes32)',pool_id)))
        if len(accounting) != 14 or accounting[1:] != config[1:]:
            raise RpcError('Accounting configuration differs from the venue policy')
        tokens = [self._address_word(accounting[0]),self._address_word(accounting[1])]
        if int(config[0],16) == 0:
            wrapper = decode_words(self.rpc.eth_call(self.contracts['pools'],calldata('nativeAsset(bytes32)',pool_id)))
            if len(wrapper) != 1 or self._address_word(wrapper[0]) != tokens[0] or tokens[0] == tokens[1]:
                raise RpcError('Native accounting wrapper mismatch')
        elif accounting[0] != config[0]:
            raise RpcError('ERC20 accounting asset differs from the venue')
        # Normalized native assets retain venue orientation; never re-sort WETH.
        return fields,tokens

    def _sync_external(self, bucket: int) -> bool:
        receiver = self.view('fees','rewardReceiver(uint256)',bucket)
        if receiver == 0: return False
        if receiver >= 1 << 160: raise RpcError('Noncanonical reward receiver address')
        inbox = '0x'+f'{receiver:040x}'
        bound_fees = uint_result(self.rpc.eth_call(inbox,calldata('fees()')))
        bound_bucket = uint_result(self.rpc.eth_call(inbox,calldata('bucketId()')))
        if bound_fees != int(self.contracts['fees'],16) or bound_bucket != bucket:
            raise RpcError('Reward receiver does not bind the discovered bucket and fee controller')
        pending = decode_words(self.rpc.eth_call(inbox,calldata('pending()')))
        if len(pending) != 2: raise RpcError('Unexpected reward receiver pending ABI')
        if any(int(amount,16) != 0 for amount in pending):
            return self.submit('fees','syncExternal(uint256)',(bucket,),f'external_rewards:{bucket}')
        return False

    def cycle(self) -> None:
        if self.poll_pending(): return
        paused = self.view('access','paused()') != 0
        if self.view('access','isSealed()') != 1: raise RpcError('Protocol is not sealed')
        if self.view('access','keepers(address)',self.sender) != 1: raise RpcError('Configured sender is not an authorized keeper')
        metadata_first = False
        if self.metadata_enabled:
            # Alternate priority so changing artwork cannot starve LP maintenance
            # and a busy LP cannot indefinitely starve metadata notifications.
            metadata_first = self.state['metadata_refresh']['next_first']
            self.state['metadata_refresh']['next_first'] = not metadata_first
            if metadata_first and self._refresh_metadata(): return
        _,now = self._head()
        batch = self._bucket_batch()
        for slot,bucket in batch:
            # Advance before a submission: submit() persists this cursor together
            # with the intended nonce before the signer can broadcast.
            self.state['bucket_cursor'] = slot+1
            item = {**self.maintenance,**self.overrides.get(str(bucket),{})}
            try:
                fields,tokens = self._bucket(bucket)
                status = int(fields[7],16)
                if status not in (1,2,3,4,6): continue
                # Canonical funded revenue and claims remain available during
                # pauses and while the physical LP is away. No principal moves.
                if item.get('sync_external_rewards',True) and self._sync_external(bucket): return
                if paused: continue
                if status == 1:
                    minimum = positive(item.get('minimum_liquidity',1),'minimum_liquidity')
                    _,fresh = self._head(); deadline = fresh+180
                    if self.view('strategy','needsRebalance(uint256)',bucket):
                        if self.submit('vault','rebalance(uint256,uint128,uint256)',(bucket,minimum,deadline),f'rebalance:{bucket}'): return
                    if item.get('compound',True):
                        reserves = [self.view('fees','compoundBalance(uint256,address)',bucket,t) for t in tokens]
                        threshold = positive(item.get('minimum_compound_units',1),'minimum_compound_units')
                        if max(reserves,default=0) >= threshold:
                            if self.submit('compounder','compound(uint256,uint128,uint256)',(bucket,minimum,deadline),f'compound:{bucket}'): return
                    interval = positive(item.get('harvest_interval_seconds',14400),'harvest_interval_seconds')
                    if item.get('harvest',True) and now-int(self.state['last'].get(f'harvest:{bucket}',0)) >= interval:
                        if self.submit('vault','collectFees(uint256,uint256)',(bucket,deadline),f'harvest:{bucket}'): return
                # Funded satellite rewards remain deliverable after principal leaves.
                for remote in item.get('reward_routes',[]):
                    token = address(remote['token'])
                    personal = self.view('fees','remoteIndividual(uint256,address)',bucket,token)
                    shared = self.view('fees','remoteCollective(uint256,address)',bucket,token)
                    if personal+shared >= positive(remote['minimum_units'],'minimum_units'):
                        if self.submit('fees','bridgeRewards(uint256,address,bytes32)',(bucket,token,remote['route_id']),
                            f'bridge_rewards:{bucket}:{token}',value=positive(remote.get('native_fee_wei',0),'native_fee_wei',zero=True)): return
            except (ValueError,RpcError) as exc:
                log('bucket_skipped',bucket_id=str(bucket),error_type=type(exc).__name__)
        if batch: self.save()
        if self.metadata_enabled and not metadata_first and self._refresh_metadata(): return
        if paused:
            log('protocol_paused'); return
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
