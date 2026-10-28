"""ZZZKeeper: serial, dry-run-by-default automation. Python 3.11+, Linux.

Live signing is delegated to a local Foundry `cast` encrypted keystore. No private
key is accepted by this program. Ambiguous broadcasts stop further submissions.
"""
from __future__ import annotations
import argparse
import copy
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import signal
import stat
import subprocess
import time
from typing import Any
from zzz_ops.abi import address, calldata, decode_words, keccak256, uint_result
from zzz_ops.rpc import Rpc, RpcError
from zzz_ops.state import atomic_json, integer, process_lock, read_json
from zzz_ops.ethereum_fees import execution_price, fee_cap, transaction_chain_id
from zzz_ops.range_policy import observe as observe_range_policy, verify as verify_range_policy
from zzz_ops.position import decode_position
from keeper.royalties import RoyaltyAutomation, BATCH as ROYALTY_BATCH, encode_batch
from keeper.watchdog import ProgressWatchdog, ProgressRPC
from keeper.principal import PrincipalDistribution, BATCH as PRINCIPAL_BATCH, encode_batch as encode_principal_batch

ACCOUNTING_MODEL = 'shared-pools-v2'
NATIVE_ASSET = '0x'+'0'*40
# Only these argument positions are currencies. Contract/owner/sender zeroes
# remain invalid in the shared ABI codec and all other keeper calls.
ASSET_ARGUMENTS = {
    'compoundBalance(uint256,address)': (1,),
    'buybackBalance(address)': (0,),
    'execute(address,uint256,bytes32,uint256)': (0,),
}
MAX_METADATA_SUPPLY = 1000
MAX_METADATA_BATCH = 50
MAX_BUYBACK_TASKS = 32
OUTSIDE_REBALANCE_STATE = 'outside_rebalance_v2'
REBALANCE_CHECK_SECONDS = 3600
MAX_OUTSIDE_SCHEDULES = 10000
CANONICAL_STATES = ('operating', 'frozen', 'importing', 'retired', 'cancelled')
PREPARATION_BLOCKED_ACTIONS = frozenset((
    ('strategy','applyKeeperRange(bytes32)'),
    ('vault','rebalance(uint256,uint128,uint256)'),
    ('compounder','compound(uint256,uint128,uint256)'),
    ('buyback','execute(address,uint256,bytes32,uint256)'),
    ('royalties',ROYALTY_BATCH),
    ('rewards',ROYALTY_BATCH),
))
LP_EXIT_BLOCKED_ACTIONS = frozenset((
    ('strategy','applyKeeperRange(bytes32)'),
    ('vault','rebalance(uint256,uint128,uint256)'),
    ('compounder','compound(uint256,uint128,uint256)'),
    ('vault','collectFees(uint256,uint256)'),
))

def log(event: str, **fields: Any) -> None:
    print(json.dumps({'time':dt.datetime.now(dt.timezone.utc).isoformat(),'event':event,**fields},sort_keys=True),flush=True)

def error_context(exc: Exception) -> dict[str,str]:
    # Never log exception text, signer output, RPC URLs or the full traceback.
    trace = exc.__traceback__
    while trace and trace.tb_next: trace = trace.tb_next
    return {'error_type':type(exc).__name__, 'error_site':
        f'{Path(trace.tb_frame.f_code.co_filename).name}:{trace.tb_frame.f_code.co_name}:{trace.tb_lineno}' if trace else 'unknown'}

def positive(value: Any, field: str, *, zero: bool = False) -> int:
    return integer(value,field,minimum=0 if zero else 1)

def rpc_quantity(value: Any, field: str, *, minimum: int = 0) -> int:
    """Require a complete canonical RPC quantity, without defaults/coercion."""
    if not isinstance(value,str) or not re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]{0,63})',value):
        raise RpcError(f'Malformed {field}')
    number = int(value,16)
    if number < minimum: raise RpcError(f'Invalid {field}')
    return number

def rpc_hash(value: Any, field: str) -> str:
    if not isinstance(value,str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}',value) or int(value,16) == 0:
        raise RpcError(f'Malformed {field}')
    return value.lower()

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
        # A heartbeat must identify the actual loaded configuration, not just a
        # signer/chain which may be reused across deployments or policy reviews.
        # Export only the digest: endpoint and signer-file secrets stay private.
        self.configuration_sha256 = hashlib.sha256(json.dumps(
            config,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        self.accounting_version = config.get('accounting_version',1)
        if type(self.accounting_version) is not int or self.accounting_version not in (1,2,3,4):
            raise ValueError('Unsupported keeper accounting version')
        self.fee_intake_version = config.get('fee_intake_version',0)
        if type(self.fee_intake_version) is not int or self.fee_intake_version not in (0,1) or \
                (self.fee_intake_version == 1 and self.accounting_version not in (2,3,4)) or \
                (self.accounting_version in (3,4) and self.fee_intake_version != 1):
            raise ValueError('Unsupported keeper fee-intake profile')
        self.chain = positive(config['chain_id'],'chain_id')
        self.rpc = rpc or Rpc(config['rpc_urls'],self.chain)
        self.sender = address(config['sender'])
        self.contracts = {k:address(v) for k,v in config['contracts'].items()}
        for name in ('access','vault','strategy','fees','compounder','buyback','pools') + (('principal_exit',) if self.accounting_version == 4 else ()):
            if name not in self.contracts: raise ValueError(f'Missing contract: {name}')
        adaptive = config.get('adaptive_range',{})
        if not isinstance(adaptive,dict) or type(adaptive.get('enabled',False)) is not bool:
            raise ValueError('Adaptive range requires explicit boolean configuration')
        self.adaptive_range_enabled = adaptive.get('enabled',False)
        # Absent accounting4 policy is explicitly the historical service mode.
        # A fresh deployment must opt into version2; never probe/fallback from a
        # failed getter or relabel a saved old deployment to activate new rules.
        self.maintenance_policy_version = config.get('maintenance_policy_version',1 if self.accounting_version == 4 else 0)
        if type(self.maintenance_policy_version) is not int or self.maintenance_policy_version not in (
                (1,2) if self.accounting_version == 4 else (0,)):
            raise ValueError('Unsupported keeper maintenance policy version')
        if self.maintenance_policy_version == 2 and self.adaptive_range_enabled:
            raise ValueError('Outside-only policy requires operator-selected ranges')
        self.lp_routing_version = config.get('lp_routing_version',0)
        if type(self.lp_routing_version) is not int or self.lp_routing_version not in (0,1):
            raise ValueError('Unsupported keeper LP-routing profile')
        if self.lp_routing_version == 1:
            if self.accounting_version != 4 or self.maintenance_policy_version != 2:
                raise ValueError('LP routing requires explicit accounting4 and maintenance2')
            for role in ('liquidity','balancing_router','pool_manager','state_view'):
                if role not in self.contracts: raise ValueError('Missing reviewed LP execution contract: '+role)
                pin=config.get('code_hashes',{}).get(role,'')
                if not isinstance(pin,str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}',pin) or int(pin,16)==0:
                    raise ValueError('Missing reviewed LP execution runtime: '+role)
        if self.adaptive_range_enabled and (type(adaptive.get('policy_version')) is not int or adaptive['policy_version'] != 1):
            raise ValueError('Adaptive range requires the explicit reviewed policy version 1')
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
        self.health_path = Path(config.get('health_path',str(self.path.with_suffix('.health.json'))))
        paths = [self.path.resolve(),self.health_path.resolve(),Path(config.get('lock_path','var/keeper.lock')).resolve()]
        paths.extend(Path(config[name]).resolve() for name in ('keystore','password_file') if config.get(name))
        if len(set(paths)) != len(paths): raise ValueError('State, health and lock paths must be distinct')
        if live and not self.path.is_file():
            raise ValueError('Live state is missing; restore a verified backup or initialize an unused keeper')
        self.state = read_json(self.path,{'chain_id':self.chain,'sender':self.sender,'contracts':self.contracts,'accounting_model':ACCOUNTING_MODEL,'accounting_version':self.accounting_version,'fee_intake_version':self.fee_intake_version,
            'bucket_cursor':0,'last':{},'spent':{},'pending':None,'next_nonce':None,'receipt_anchor':None})
        if not isinstance(self.state,dict): raise ValueError('Malformed persistent state')
        if self.state['chain_id'] != self.chain or self.state['sender'] != self.sender:
            raise ValueError('Persistent state belongs to another chain or sender')
        if self.state.get('accounting_model') != ACCOUNTING_MODEL:
            raise ValueError('Persistent keeper state requires a reviewed shared-pool migration; preserve pending records')
        # A missing field is a historical WETH-accounting journal, never an
        # implicit native port. No pending intent, nonce or receipt is rewritten.
        if self.state.get('accounting_version',1) != self.accounting_version or type(self.state.get('accounting_version',1)) is not int:
            raise ValueError('Persistent keeper state belongs to another accounting version; preserve recovery records')
        if type(self.state.get('fee_intake_version',0)) is not int or self.state.get('fee_intake_version',0) != self.fee_intake_version:
            raise ValueError('Persistent keeper state belongs to another fee-intake version; preserve recovery records')
        if self.state.get('contracts') != self.contracts:
            raise ValueError('Persistent keeper state belongs to another deployment')
        positive(self.state.get('bucket_cursor'),'bucket_cursor',zero=True)
        self._validate_state()
        # Old pending transactions retain their original recovery path. Retired
        # bridge configuration may not schedule any NEW transaction, but must
        # not prevent inspection of an already saved hash.
        self._validate_maintenance_config(allow_retired=bool(self.state.get('pending')))
        self.retry_cooldown = positive(config.get('revert_cooldown_seconds',3600),'revert_cooldown_seconds')
        if not 60 <= self.retry_cooldown <= 86400: raise ValueError('Revert cooldown must be 60-86400 seconds')
        self.cycle_failures = 0
        self.skipped_buckets = 0
        self.blocked_actions = 0
        self.confirmed_reverts = 0
        self.active_revert_cooldowns = None
        self.next_revert_retry_after = None
        self.strategy_paused = False
        self.preparing = None
        self.canonical_lifecycle = None
        self.principal_exit_started = None
        self.stop_requested = lambda: False
        self.last_success_at = None
        self.confirmations = positive(config.get('confirmations',12),'confirmations')
        self.fee_policy = config.get('receipt_fee_policy','unverified')
        if self.fee_policy not in ('unverified','included','separate_l1_fee'):
            raise ValueError('Unsupported receipt fee policy')
        self._configure_metadata()
        self.royalties = RoyaltyAutomation(self)
        self.lp_rewards = RoyaltyAutomation(self, lp=True)
        self.principal_distribution = PrincipalDistribution(self)
        turn = self.state.get('conversion_turn',0)
        if type(turn) is not int or not 0 <= turn <= 2: raise ValueError('Invalid conversion scheduling state')
        if type(self.state.get('buyback_priority',False)) is not bool:
            raise ValueError('Invalid buyback priority state')
        cursor = self.state.get('buyback_cursor',0)
        if type(cursor) is not int or not 0 <= cursor <= MAX_BUYBACK_TASKS:
            raise ValueError('Invalid buyback scheduling cursor')
        # A bad new task must not prevent recovery of an already saved hash.
        if not self.state.get('pending'): self._buyback_tasks()
        if self.live:
            if config.get('reviewed_for_live_use') is not True:
                raise ValueError('Live use requires an explicit reviewed deployment configuration')
            if self.state.get('next_nonce') is None:
                raise ValueError('Live state needs a reviewed nonce checkpoint; do not reset old recovery state')
            if self.fee_policy == 'unverified': raise ValueError('Qualify network receipt fee accounting before live use')
            if self.fee_policy == 'separate_l1_fee': positive(config.get('l1_fee_allowance_wei'),'l1_fee_allowance_wei')
            self._validate_runtime_files()
            self._validate_signer()
            self._validate_code_hashes()
            self._validate_accounting_version()
            # Receipt recovery needs no new balancing decision. Preserve the
            # saved intent through a helper-read outage; every later balance
            # action still rechecks this capability before simulation/signing.
            if not self.state.get('pending'): self._validate_lp_routing()
            self._validate_checkpoint()

    def _validate_state(self) -> None:
        schedules = self.state.get(OUTSIDE_REBALANCE_STATE,{})
        if not isinstance(schedules,dict) or len(schedules) > min(self.max_buckets,MAX_OUTSIDE_SCHEDULES):
            raise ValueError('Malformed outside-rebalance schedule inventory')
        for bucket,record in schedules.items():
            if not isinstance(bucket,str) or str(positive(bucket,'schedule bucket')) != bucket or int(bucket) >= 1 << 256:
                raise ValueError('Outside-rebalance bucket identity must be canonical')
            if not isinstance(record,dict) or set(record) != {'identity','observed_at','next_check_at','execute_after'}:
                raise ValueError('Malformed outside-rebalance schedule')
            rpc_hash(record['identity'],'outside-rebalance identity')
            for name in ('observed_at','next_check_at','execute_after'):
                value = record[name]
                if type(value) is not int or not 0 <= value < 1 << 64:
                    raise ValueError('Malformed outside-rebalance schedule time')
            observed,check,execute = (record[name] for name in ('observed_at','next_check_at','execute_after'))
            if not (execute == 0 and check == observed+REBALANCE_CHECK_SECONDS or
                    check == 0 and 60 <= execute-observed <= 600):
                raise ValueError('Invalid outside-rebalance schedule bounds')
        for field in ('last','spent','retry_after'):
            values = self.state.get(field,{}) if field == 'retry_after' else self.state.get(field)
            if not isinstance(values,dict): raise ValueError('Malformed keeper counters')
            for key,value in values.items():
                if not isinstance(key,str) or not key: raise ValueError('Malformed keeper counter key')
                positive(value,field,zero=True)
                if field == 'spent': dt.date.fromisoformat(key)
        nonce = self.state.get('next_nonce')
        if nonce is not None: positive(nonce,'next_nonce',zero=True)
        anchor = self.state.get('receipt_anchor')
        if anchor is not None:
            if not isinstance(anchor,dict): raise ValueError('Malformed receipt checkpoint')
            for field in ('number','nonce','timestamp'): positive(anchor.get(field),field,zero=True)
            rpc_hash(anchor.get('hash'),'receipt checkpoint hash')
            if nonce != anchor['nonce']+1: raise ValueError('Receipt checkpoint nonce mismatch')
        pending = self.state.get('pending')
        if pending is not None:
            if not isinstance(pending,dict): raise ValueError('Malformed pending intent')
            for field in ('nonce','value'): positive(pending.get(field),field,zero=True)
            if nonce is not None and pending['nonce'] != nonce: raise ValueError('Pending nonce checkpoint mismatch')
            address(pending.get('to'))
            if not isinstance(pending.get('key'),str) or not pending['key']: raise ValueError('Missing action identity')
            if not isinstance(pending.get('data'),str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2}){4,}',pending['data']):
                raise ValueError('Malformed pending calldata')
            dt.date.fromisoformat(pending['day'])
            if pending.get('hash') is not None: rpc_hash(pending['hash'],'pending hash')
            # Older pending intents remain recoverable evidence. Never invent
            # the signing-time budget they did not record; reconciliation stops
            # with an explicit diagnostic until an operator reviews that record.
            if 'fee_review' in pending: self._fee_review(pending)

    @staticmethod
    def _fee_review(pending: dict[str,Any]) -> dict[str,Any]:
        review = pending.get('fee_review')
        fields = {'schema','gas_limit','max_fee_per_gas','l1_fee_allowance_wei',
                  'maximum_cost_wei','receipt_fee_policy'}
        if review is None:
            log('pending_fee_review_required',operator_action='preserve_and_review_original_evidence_never_resend')
            raise RpcError('Legacy pending intent lacks its original fee review; preserve it and perform reviewed operator reconciliation, never resend')
        if not isinstance(review,dict) or set(review) != fields or type(review.get('schema')) is not int or review['schema'] != 1:
            raise RpcError('Malformed pending fee review')
        for name in ('gas_limit','max_fee_per_gas','l1_fee_allowance_wei','maximum_cost_wei'):
            if type(review[name]) is not int or not 0 <= review[name] < 1 << 256:
                raise RpcError('Malformed pending fee bound')
        if review['gas_limit'] == 0 or review['maximum_cost_wei'] != \
                review['gas_limit']*review['max_fee_per_gas']+review['l1_fee_allowance_wei']+pending['value']:
            raise RpcError('Pending fee review arithmetic differs')
        if review['receipt_fee_policy'] not in ('included','separate_l1_fee'):
            raise RpcError('Pending network fee semantics are unqualified')
        return review

    def _validate_runtime_files(self) -> None:
        if os.name != 'posix': raise ValueError('Live keeper requires supported Unix ownership/locking')
        for path in (self.path,self.health_path):
            parent = path.parent.stat()
            if parent.st_uid != os.getuid() or parent.st_mode & 0o022:
                raise ValueError('Runtime directory must belong to keeper and not be writable by others')
            if path.is_symlink(): raise ValueError('Runtime state/health symlinks are forbidden')
            if path.exists():
                st = path.stat()
                if not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid() or st.st_mode & 0o077:
                    raise ValueError('Runtime files must be private regular files owned by keeper')

    def _validate_checkpoint(self) -> None:
        anchor = self.state.get('receipt_anchor')
        if anchor is None:
            if self.live and self.state.get('next_nonce') != 0:
                raise RpcError('Missing confirmed checkpoint for a used signer')
            return
        head,_ = self._head()
        block = positive(anchor['number'],'receipt checkpoint block',zero=True)
        header = self.rpc.call('eth_getBlockByNumber',[hex(block),False])
        if (head-block+1 < self.confirmations or not isinstance(header,dict) or
                rpc_quantity(header.get('number'),'checkpoint header number') != block or
                rpc_hash(header.get('hash'),'checkpoint header hash') != anchor['hash'] or
                rpc_quantity(header.get('timestamp'),'checkpoint header timestamp') != anchor['timestamp']):
            log('confirmed_checkpoint_invalidated',block_number=block)
            raise RpcError('Confirmed receipt checkpoint changed; manual reorg reconciliation required')

    def initialize_state(self) -> None:
        """Explicit bootstrap only. Used signers require restoration, never reset."""
        if self.live or self.path.exists(): raise ValueError('Initialization requires missing state in dry-run mode')
        if self.config.get('reviewed_for_live_use') is not True: raise ValueError('Review configuration before initialization')
        self._validate_code_hashes()
        self._validate_accounting_version()
        self._validate_lp_routing()
        self._head()
        for tag in ('latest','pending'):
            if rpc_quantity(self.rpc.call('eth_getTransactionCount',[self.sender,tag]),'initial nonce') != 0:
                raise ValueError('Used keeper requires restored/reconciled state or a fresh authorized signer')
        self.state['next_nonce'] = 0
        self.save()
        log('state_initialized',sender=self.sender,chain_id=self.chain)

    def run_cycle(self) -> bool:
        """Write a heartbeat separately from durable transaction recovery state."""
        start = time.monotonic()
        self.skipped_buckets = 0
        self.blocked_actions = 0
        self.confirmed_reverts = 0
        self.active_revert_cooldowns = None
        self.next_revert_retry_after = None
        def health(status: str, **extra: Any) -> None:
            atomic_json(self.health_path,{'time':dt.datetime.now(dt.timezone.utc).isoformat(),
                'status':status,'live':self.live,'chain_id':self.chain,'sender':self.sender,
                'configuration_sha256':self.configuration_sha256,
                'last_success_at':self.last_success_at,'consecutive_failures':self.cycle_failures,
                'skipped_buckets':self.skipped_buckets,'pending':bool(self.state.get('pending')),
                'blocked_actions':self.blocked_actions,'strategy_paused':self.strategy_paused,
                'confirmed_reverts':self.confirmed_reverts,
                'active_revert_cooldowns':self.active_revert_cooldowns,
                'next_revert_retry_after':self.next_revert_retry_after,
                'preparation_active':self.preparing,
                'canonical_state':self.canonical_lifecycle,
                'lp_exit_started':self.principal_exit_started,
                'pending_action':(self.state.get('pending') or {}).get('key'),
                'pending_day':(self.state.get('pending') or {}).get('day'),
                'duration_seconds':round(time.monotonic()-start,3),**extra})
        health('running')  # A failed health write stops the cycle before signing.
        try:
            self.cycle()
            self._observe_revert_cooldowns()
        except Exception as exc:
            self.cycle_failures += 1
            details = error_context(exc)
            retryable = isinstance(exc,(RpcError,subprocess.TimeoutExpired))
            health('error' if retryable else 'halted',**details)
            log('cycle_failed',retryable=retryable,consecutive_failures=self.cycle_failures,**details)
            if not retryable: raise
            return False
        pending = bool(self.state.get('pending'))
        if self.skipped_buckets or self.blocked_actions:
            self.cycle_failures += 1
            status = 'degraded'
        elif pending:
            status = 'awaiting_receipt' if self.state['pending'].get('hash') else 'recovery_required'
        elif self.canonical_lifecycle not in (None,0):
            self.cycle_failures = 0
            self.last_success_at = dt.datetime.now(dt.timezone.utc).isoformat()
            status = 'canonical_locked'
        else:
            self.cycle_failures = 0
            if not self.confirmed_reverts:
                self.last_success_at = dt.datetime.now(dt.timezone.utc).isoformat()
            # A paid failure remains an observable restriction until its
            # existing action cooldown expires, including after restart or
            # another job succeeds. It does not stop independent scheduling or
            # introduce additional loop backoff.
            status = ('revert_cooldown' if self.active_revert_cooldowns else
                ('degraded' if self.confirmed_reverts else ('healthy' if self.live else 'dry_run')))
        health(status)
        log('cycle_completed',status=status,skipped_buckets=self.skipped_buckets,pending=pending,
            confirmed_reverts=self.confirmed_reverts,
            active_revert_cooldowns=self.active_revert_cooldowns,next_revert_retry_after=self.next_revert_retry_after)
        return not (self.skipped_buckets or self.blocked_actions)

    def save(self) -> None: atomic_json(self.path,self.state)

    def _observe_revert_cooldowns(self) -> None:
        """Summarize existing paid-revert restrictions without changing the journal."""
        deadlines = self.state.get('retry_after',{})
        count,earliest = 0,None
        if deadlines:
            _,timestamp = self._head()
            for value in deadlines.values():
                deadline = positive(value,'retry_after',zero=True)
                if timestamp < deadline:
                    count += 1
                    earliest = deadline if earliest is None else min(earliest,deadline)
        self.active_revert_cooldowns = count
        self.next_revert_retry_after = earliest

    def _validate_maintenance_settings(self,settings: dict[str,Any],*,allow_retired: bool = False) -> None:
        if not isinstance(settings,dict): raise ValueError('Maintenance settings must be an object')
        if self.fee_intake_version == 1 and settings.get('sync_external_rewards',False) and not allow_retired:
            raise ValueError('LP-only fee intake has no creator-payment synchronization job')
        for name in ('compound','compound_idle','harvest','sync_external_rewards'):
            if name in settings and type(settings[name]) is not bool:
                raise ValueError(f'{name} must be an explicit boolean')
        limits = {'minimum_liquidity':128,'minimum_compound_units':256}
        for name,bits in limits.items():
            if name in settings and positive(settings[name],name) >= 1 << bits:
                raise ValueError(f'{name} exceeds uint{bits}')
        if 'harvest_interval_seconds' in settings:
            positive(settings['harvest_interval_seconds'],'harvest_interval_seconds')
        if 'compound_interval_seconds' in settings:
            interval = positive(settings['compound_interval_seconds'],'compound_interval_seconds',zero=True)
            if interval != 0 and not 600 <= interval <= 604800:
                raise ValueError('Compounding interval must be zero or 600-604800 seconds')
        if 'compound_thresholds' in settings:
            thresholds = settings['compound_thresholds']
            if not isinstance(thresholds,dict) or not 1 <= len(thresholds) <= 33:
                raise ValueError('Compound thresholds require a bounded nonempty currency map')
            for currency,raw in thresholds.items():
                if self._asset(currency) != currency:
                    raise ValueError('Compound threshold currencies must use canonical lowercase addresses')
                if positive(raw,'compound threshold') >= 1 << 256:
                    raise ValueError('Compound threshold exceeds uint256')
        if 'reward_routes' in settings:
            routes = settings['reward_routes']
            if not isinstance(routes,list) or routes and not allow_retired:
                raise ValueError('Reward bridge scheduling is retired; remove reward_routes without changing pending evidence')

    def _validate_maintenance_config(self,*,allow_retired: bool = False) -> None:
        for settings in (self.maintenance,*self.overrides.values()):
            self._validate_maintenance_settings(settings,allow_retired=allow_retired)
        for override in ({},*self.overrides.values()):
            settings = {**self.maintenance,**override}
            if self.maintenance_policy_version == 2 and settings.get('compound',True) and not settings.get('compound_thresholds'):
                raise ValueError('Fresh compounding requires explicit actual-currency thresholds')
            if settings.get('compound_idle',False):
                if self.accounting_version not in (2,3,4) or not settings.get('compound_thresholds') or \
                        not 600 <= positive(settings.get('compound_interval_seconds',0),'compound_interval_seconds',zero=True) <= 604800:
                    raise ValueError('Idle compounding requires native V2, currency thresholds and an explicit 600-604800-second interval')
                address(self.config.get('idle_compounding_budget'))
                pin = self.config.get('code_hashes',{}).get('idle_compounding_budget','')
                if not isinstance(pin,str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}',pin) or int(pin,16) == 0:
                    raise ValueError('Idle compounding requires an exact reviewed budget runtime pin')

    def _compound_budget(self,version: int) -> str:
        """Authenticate the reviewed companion before trusting maintenance eligibility."""
        try:
            budget = address(self.config.get('idle_compounding_budget'))
        except ValueError as exc:
            raise RpcError('Compounding requires a reviewed budget binding') from exc
        pin = self.config.get('code_hashes',{}).get('idle_compounding_budget','')
        if not isinstance(pin,str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}',pin) or int(pin,16) == 0:
            raise RpcError('Compounding requires an exact reviewed budget runtime pin')
        code = self.rpc.call('eth_getCode',[budget,'latest'])
        if not isinstance(code,str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+',code) or \
                '0x'+keccak256(bytes.fromhex(code[2:])).hex() != pin.lower():
            raise RpcError('Compounding budget runtime differs from the reviewed profile')
        def read(signature: str,*args: int) -> int:
            return uint_result(self.rpc.eth_call(budget,calldata(signature,*args)))
        if self.view('vault','migrationBudget()') != int(budget,16) or \
                read('vault()') != int(self.contracts['vault'],16) or read('IDLE_COMPOUNDING_VERSION()') != version:
            raise RpcError('Compounding budget capability or Vault binding differs')
        return budget

    def _idle_compound_checkpoint(self,bucket: int,fields: list[str]) -> tuple[int,int]:
        """Preserve the explicitly opted-in historical V1 cooldown reader."""
        budget = self._compound_budget(1)
        last = uint_result(self.rpc.eth_call(budget,calldata('lastCompound(uint256)',bucket)))
        if last >= 1 << 64: raise RpcError('Malformed compound checkpoint')
        config = decode_words(self.rpc.eth_call(self.contracts['pools'],calldata('get(bytes32)','0x'+fields[0])))
        if len(config) != 14 or not 600 <= int(config[11],16) <= 604800:
            raise RpcError('Malformed on-chain compound cooldown')
        if int(config[6],16) != 1: raise RpcError('Pool operations are not enabled for idle compounding')
        return last,int(config[11],16)

    def _compound_ready(self,bucket: int) -> bool:
        """Read the exact historical V2 or separate-interval V3 companion policy."""
        budget = self._compound_budget(3 if self.maintenance_policy_version == 2 else 2)
        ready = uint_result(self.rpc.eth_call(budget,calldata('compoundReady(uint256)',bucket)))
        if ready not in (0,1): raise RpcError('Malformed compound eligibility')
        return ready == 1

    def _validate_upkeep_policy(self) -> None:
        if self.maintenance_policy_version != 2: return
        for name in ('strategy','pools'):
            pin = self.config.get('code_hashes',{}).get(name,'')
            code = self.rpc.call('eth_getCode',[self.contracts[name],'latest'])
            if not isinstance(pin,str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}',pin) or int(pin,16) == 0 or \
                    not isinstance(code,str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+',code) or \
                    '0x'+keccak256(bytes.fromhex(code[2:])).hex() != pin.lower():
                raise RpcError('Outside-only runtime differs from the reviewed profile')
            module = '0x'+keccak256(('ZZZStrategy' if name == 'strategy' else 'ZZZPoolRegistry').encode()).hex()
            if self.view(name,'access()') != int(self.contracts['access'],16) or \
                    self.view('access','module(bytes32)',module) != int(self.contracts[name],16):
                raise RpcError('Outside-only module binding differs from the reviewed profile')
        if self.view('strategy','MAINTENANCE_POLICY_VERSION()') != 2:
            raise RpcError('Outside-only maintenance policy version differs')

    def _validate_lp_routing(self) -> None:
        """Fresh helper metadata and runtimes use one canonical, read-only block."""
        if self.lp_routing_version != 1: return
        from zzz_ops.lp_execution import observe
        header=self.rpc.call('eth_getBlockByNumber',['latest',False])
        if not isinstance(header,dict): raise RpcError('Missing LP execution header')
        block={'blockHash':rpc_hash(header.get('hash'),'LP execution block hash'),'requireCanonical':True}
        rpc_quantity(header.get('number'),'LP execution block number')
        if abs(time.time()-rpc_quantity(header.get('timestamp'),'LP execution timestamp',minimum=1))>600:
            raise RpcError('Stale LP execution snapshot')
        def read(target,method,*args):
            return decode_words(self.rpc.call('eth_call',[{'to':target,'data':calldata(method,*args)},block]))
        try:
            for role in ('access','pools','liquidity','balancing_router','pool_manager','state_view'):
                expected=self.config.get('code_hashes',{}).get(role,'')
                code=self.rpc.call('eth_getCode',[self.contracts[role],block])
                if (not isinstance(expected,str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}',expected) or
                        not isinstance(code,str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+',code) or
                        '0x'+keccak256(bytes.fromhex(code[2:])).hex()!=expected.lower()):
                    raise ValueError('LP execution runtime differs')
            for role,label in (('pools','ZZZPoolRegistry'),('liquidity','ZZZLiquidityManager')):
                if (read(self.contracts['access'],'module(bytes32)','0x'+keccak256(label.encode()).hex())!=[f'{int(self.contracts[role],16):064x}'] or
                        read(self.contracts[role],'access()')!=[f'{int(self.contracts["access"],16):064x}']):
                    raise ValueError('LP execution module binding differs')
            self.lp_execution_observation=observe(read,liquidity=self.contracts['liquidity'],
                router=self.contracts['balancing_router'],pool_manager=self.contracts['pool_manager'],
                state_view=self.contracts['state_view'],access=self.contracts['access'],pools=self.contracts['pools'])
        except (ValueError,TypeError,KeyError) as exc:
            raise RpcError('LP execution capability differs from the reviewed profile') from exc

    def _store_rebalance_schedule(self,bucket: int,record: dict[str,Any] | None) -> None:
        # Durability precedes both waiting and any eventual signer. A failed save
        # restores memory too; restart never draws a fresh delay to bypass it.
        previous = self.state
        updated = copy.deepcopy(previous)
        schedules = updated.setdefault(OUTSIDE_REBALANCE_STATE,{})
        if record is None:
            if str(bucket) not in schedules: return
            del schedules[str(bucket)]
        else:
            if str(bucket) not in schedules and len(schedules) >= min(self.max_buckets,MAX_OUTSIDE_SCHEDULES):
                raise ValueError('Outside-rebalance schedule inventory is full')
            schedules[str(bucket)] = record
        self.state = updated
        try: self.save()
        except BaseException:
            self.state = previous
            raise

    def _rebalance_due(self,bucket: int,fields: list[str],now: int) -> bool:
        if self.maintenance_policy_version != 2:
            return bool(self.view('strategy','needsRebalance(uint256)',bucket))
        position = decode_position(fields,self.accounting_version)
        if position['status'] != 'active' or position['lp_token_id'] == 0:
            return False
        config = decode_words(self.rpc.eth_call(self.contracts['pools'],calldata('get(bytes32)',position['pool_id'])))
        if len(config) != 14 or '0x'+keccak256(bytes.fromhex(''.join(config[:5]))).hex() != position['pool_id']:
            raise RpcError('Outside-rebalance pool configuration differs')
        interval = int(config[11],16)
        if not 600 <= interval <= 604800 or int(config[6],16) not in (0,1):
            raise RpcError('Malformed outside-rebalance interval or operation flag')
        if type(now) is not int or not 0 <= now < (1 << 64)-REBALANCE_CHECK_SECONDS or position['last_rebalance'] > now:
            raise RpcError('Invalid outside-rebalance chain clock')
        orientation = self.view('strategy','rangeOrientation(bytes32)',position['pool_id'])
        if orientation not in (0,1): raise RpcError('Malformed range orientation')
        # Deliberately exclude balances, idle, NAV and prices: contributions and
        # harvesting must not reset a replacement's waiting period or jitter.
        basis = [2,self.chain,self.contracts['vault'],self.contracts['strategy'],
            self.config['code_hashes']['strategy'],self.contracts['pools'],self.config['code_hashes']['pools'],
            bucket,position['pool_id'],position['lp_token_id'],position['last_rebalance'],config,orientation]
        identity = '0x'+keccak256(json.dumps(basis,separators=(',',':')).encode()).hex()
        record = self.state.get(OUTSIDE_REBALANCE_STATE,{}).get(str(bucket))
        if record is not None and record['identity'] != identity:
            self._store_rebalance_schedule(bucket,None)
            record = None
        if record is not None and now < record['observed_at']:
            raise RpcError('Outside-rebalance chain clock retreated')
        if int(config[6],16) != 1 or now < position['last_rebalance']+interval:
            return False
        manual = self.view('strategy','rangeUpdatePending(uint256)',bucket)
        if manual not in (0,1): raise RpcError('Malformed desired-range flag')
        if record is not None and not manual and record['execute_after'] == 0 and now < record['next_check_at']:
            return False
        needed = self.view('strategy','needsRebalance(uint256)',bucket)
        if needed not in (0,1): raise RpcError('Malformed outside-rebalance eligibility')
        if not needed:
            self._store_rebalance_schedule(bucket,dict(identity=identity,observed_at=now,
                next_check_at=now+REBALANCE_CHECK_SECONDS,execute_after=0))
            return False
        if record is not None and record['execute_after']:
            return now >= record['execute_after']
        delay = 60+secrets.randbelow(541)
        self._store_rebalance_schedule(bucket,dict(identity=identity,observed_at=now,
            next_check_at=0,execute_after=now+delay))
        log('rebalance_scheduled',bucket_id=str(bucket),execute_after=now+delay,manual_range=bool(manual))
        return False

    def _rebalance_submission_ready(self,args: tuple[int|str,...]) -> bool:
        if self.maintenance_policy_version != 2: return True
        if len(args) != 3 or type(args[0]) is not int:
            raise ValueError('Malformed outside-rebalance submission')
        fields,_ = self._bucket(args[0])
        _,fresh = self._head()
        return self._rebalance_due(args[0],fields,fresh)

    def _adaptive_range_target(self,pool: str,now: int) -> int:
        # Opt-in only; historical profiles never call new Strategy getters.
        for name in ('strategy','pools'):
            pin = self.config.get('code_hashes',{}).get(name,'')
            code = self.rpc.call('eth_getCode',[self.contracts[name],'latest'])
            if not isinstance(pin,str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}',pin) or \
                    not isinstance(code,str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+',code) or \
                    '0x'+keccak256(bytes.fromhex(code[2:])).hex() != pin.lower():
                raise RpcError('Adaptive range runtime differs from the reviewed profile')
        def read(signature: str,*args: int|str,count: int) -> list[str]:
            result = decode_words(self.rpc.eth_call(self.contracts['strategy'],calldata(signature,*args)))
            if len(result) != count: raise RpcError('Malformed adaptive range response')
            return result
        observed = observe_range_policy(read,pool)
        config = decode_words(self.rpc.eth_call(self.contracts['pools'],calldata('get(bytes32)',pool)))
        # The on-chain governance-approved policy is the authority. Independently
        # check its ABI/bounds/fingerprint; no local raw-width override is used.
        metadata = verify_range_policy({key:observed[key] for key in ('orientation','keeper')},observed,config,now)
        return metadata['target_half_width_bps']

    def _compound_due(self,bucket: int,tokens: list[str],reserves: list[int],item: dict[str,Any],now: int,
                      fields: list[str]) -> bool:
        interval = positive(item.get('compound_interval_seconds',0),'compound_interval_seconds',zero=True)
        last = positive(self.state['last'].get(f'compound:{bucket}',0),'last compound',zero=True)
        if now < last+interval: return False
        if item.get('compound_idle',False):
            # Only this bucket's attributed balances, never a raw contract
            # balance or another NFT/bucket's rewards, can become principal.
            reserves = [amount+int(fields[index],16) for amount,index in zip(reserves,(2,3))]
            if any(amount >= 1 << 256 for amount in reserves): raise RpcError('Compound amount exceeds uint256')
        thresholds = item.get('compound_thresholds')
        if thresholds is not None:
            if any(currency not in thresholds for currency in tokens):
                raise ValueError('Missing compound threshold for the actual pool currency')
            # Raw units belong to one currency only: never sum ETH, ZZZ or a
            # six-decimal stablecoin, and never silently reuse another's bound.
            due = any(amount >= positive(thresholds[currency],'compound threshold')
                      for currency,amount in zip(tokens,reserves))
        else:
            threshold = positive(item.get('minimum_compound_units',1),'minimum_compound_units')
            due = any(amount >= threshold for amount in reserves)
        if due and self.accounting_version == 4:
            # Authoritative shared cooldown includes other keepers and the last
            # rebalance. Never infer it solely from this sender's journal.
            return self._compound_ready(bucket)
        if due and item.get('compound_idle',False):
            chain_last,chain_interval = self._idle_compound_checkpoint(bucket,fields)
            if now < max(last,chain_last)+max(interval,chain_interval): return False
        return due

    def view(self,name: str,signature: str,*args: int|str) -> int:
        return uint_result(self.rpc.eth_call(self.contracts[name],self._calldata(signature,*args)))

    def _asset(self,value: Any) -> str:
        if self.accounting_version in (2,3,4) and isinstance(value,str) and value.lower() == NATIVE_ASSET:
            return NATIVE_ASSET
        return address(value)

    def _calldata(self,signature: str,*args: int|str) -> str:
        positions = ASSET_ARGUMENTS.get(signature,())
        values = list(args)
        native = []
        for index in positions:
            if index >= len(values): raise ValueError('Missing currency argument')
            values[index] = self._asset(values[index])
            if values[index] == NATIVE_ASSET:
                native.append(index)
                # Use the strict shared encoder, replacing only reviewed asset
                # words afterwards. Never loosen address() globally.
                values[index] = '0x'+'0'*39+'1'
        data = calldata(signature,*values)
        for index in native:
            start=10+64*index
            data=data[:start]+'0'*64+data[start+64:]
        return data

    def _validate_accounting_version(self) -> None:
        if self.accounting_version == 1: return
        pin=self.config.get('code_hashes',{}).get('vault','')
        if not isinstance(pin,str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}',pin):
            raise RpcError('Native accounting requires a reviewed Vault runtime pin')
        code=self.rpc.call('eth_getCode',[self.contracts['vault'],'latest'])
        if not isinstance(code,str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+',code) or '0x'+keccak256(bytes.fromhex(code[2:])).hex()!=pin.lower():
            raise RpcError('Native Vault runtime differs from the reviewed keeper profile')
        try: version = self.view('vault','ACCOUNTING_VERSION()')
        except (ValueError,RpcError) as exc: raise RpcError('Native accounting version is unavailable') from exc
        if version != self.accounting_version: raise RpcError('Vault accounting version differs from the reviewed keeper profile')
        if self.fee_intake_version == 1:
            pin = self.config.get('code_hashes',{}).get('fees','')
            if not isinstance(pin,str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}',pin):
                raise RpcError('LP-only fee intake requires a reviewed fee-controller runtime pin')
            code = self.rpc.call('eth_getCode',[self.contracts['fees'],'latest'])
            if not isinstance(code,str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+',code) or \
                    '0x'+keccak256(bytes.fromhex(code[2:])).hex() != pin.lower():
                raise RpcError('LP-only fee-controller runtime differs from the reviewed keeper profile')
            if self.view('fees','FEE_INTAKE_VERSION()') != 1:
                raise RpcError('LP-only fee-intake version differs from the reviewed keeper profile')
        if self.accounting_version == 4:
            for name in ('access', 'principal_exit'):
                pin = self.config.get('code_hashes',{}).get(name, '')
                code = self.rpc.call('eth_getCode', [self.contracts[name], 'latest'])
                if (not isinstance(pin,str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}',pin) or
                        not isinstance(code,str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+',code) or
                        '0x'+keccak256(bytes.fromhex(code[2:])).hex() != pin.lower()):
                    raise RpcError('Holder-exit runtime differs from the reviewed keeper profile')
            module = '0x'+keccak256(b'ZZZMigration').hex()
            if (self.view('access','module(bytes32)',module) != int(self.contracts['principal_exit'],16) or
                    self.view('principal_exit','access()') != int(self.contracts['access'],16) or
                    self.view('principal_exit','CUSTODY_VERSION()') != 3):
                raise RpcError('Holder-exit module binding or capability differs')
        self._validate_upkeep_policy()

    def lp_exit_started(self) -> bool:
        # Historical controllers have no such getter. Their profiles and
        # pending journals must never inherit a fabricated retirement state.
        if self.accounting_version != 4: return False
        value = self.view('access','lpExitStarted()')
        phase = self.view('principal_exit','exitPhase()')
        if value not in (0,1) or not 0 <= phase <= 3 or bool(value) != bool(phase):
            raise RpcError('Inconsistent collective LP exit lifecycle')
        self.principal_exit_started = bool(value)
        return bool(value)

    def preparation_active(self) -> bool:
        """Current deployments must expose this strict ABI; no legacy fallback."""
        try:
            value = self.view('access','preparationActive()')
        except ValueError as exc:
            raise RpcError('Malformed canonical preparation flag') from exc
        if value not in (0,1): raise RpcError('Noncanonical preparation flag')
        active = bool(value)
        if self.preparing is not active and (self.preparing is not None or active):
            log('canonical_preparation_observed',active=active)
        self.preparing = active
        return active

    def canonical_state(self) -> int:
        """Fail closed on absent/old/malformed controller interfaces, never infer operating."""
        previous = self.canonical_lifecycle
        self.canonical_lifecycle = None
        try:
            state = self.view('access','canonicalState()')
        except ValueError as exc:
            raise RpcError('Malformed canonical lifecycle state') from exc
        if type(state) is not int or not 0 <= state < len(CANONICAL_STATES):
            raise RpcError('Unknown canonical lifecycle state')
        if previous != state and (previous is not None or state != 0):
            log('canonical_lifecycle_observed',state=state,name=CANONICAL_STATES[state])
        self.canonical_lifecycle = state
        return state

    def _defer_for_lifecycle(self, name: str, signature: str) -> bool:
        # All newly submitted transactions stop while ownership/accounting is
        # frozen or inert. Receipt reconciliation runs before these observations.
        if self.canonical_state() != 0: return True
        # Read even for drain actions: unsupported deployments cannot silently
        # inherit new-source compatibility. Reconciliation remains independent.
        preparing = self.preparation_active()
        exiting = self.lp_exit_started()
        return (preparing and (name,signature) in PREPARATION_BLOCKED_ACTIONS or
                exiting and (name,signature) in LP_EXIT_BLOCKED_ACTIONS)

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
        if any(({**self.maintenance,**override}).get('compound_idle',False)
               for override in ({},*self.overrides.values())):
            targets['idle_compounding_budget'] = address(self.config['idle_compounding_budget'])
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
        if not isinstance(head,dict): raise RpcError('Missing RPC head')
        number = rpc_quantity(head.get('number'),'head block number')
        timestamp = rpc_quantity(head.get('timestamp'),'head timestamp',minimum=1)
        rpc_hash(head.get('hash'),'head block hash')
        if abs(time.time()-timestamp) > 600: raise RpcError('RPC head timestamp is stale or implausible')
        return number,timestamp

    def poll_pending(self) -> bool:
        self._validate_checkpoint()
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
        if not isinstance(receipt,dict): raise RpcError('Malformed pending receipt')
        if rpc_hash(receipt.get('transactionHash'),'receipt transaction hash') != rpc_hash(tx_hash,'pending transaction hash'):
            raise RpcError('Pending receipt transaction hash mismatch')
        try:
            if address(receipt.get('from')) != self.sender or address(receipt.get('to')) != pending['to']:
                raise ValueError('Receipt sender or target differs')
        except (ValueError,TypeError,AttributeError) as exc:
            raise RpcError('Pending receipt sender/target mismatch') from exc
        block = rpc_quantity(receipt.get('blockNumber'),'receipt block number')
        block_hash = rpc_hash(receipt.get('blockHash'),'receipt block hash')
        transaction_index = rpc_quantity(receipt.get('transactionIndex'),'receipt transaction index')
        status = rpc_quantity(receipt.get('status'),'receipt status')
        if status not in (0,1): raise RpcError('Unsupported receipt status')
        success = status == 1
        gas_used = rpc_quantity(receipt.get('gasUsed'),'receipt gas used',minimum=1)
        # Keep the provider's derived field as evidence, but calculate dynamic
        # execution cost from signed caps and the canonical inclusion block.
        reported_price = rpc_quantity(receipt.get('effectiveGasPrice'),'receipt effective gas price')
        review = self._fee_review(pending)
        # Optional chain-specific extension: production must qualify whether
        # additional L1 cost is reported separately or included in gasUsed.
        if review['receipt_fee_policy'] == 'separate_l1_fee' and 'l1Fee' not in receipt:
            raise RpcError('Required separate L1 fee is missing')
        l1_fee = rpc_quantity(receipt['l1Fee'],'receipt L1 fee') if 'l1Fee' in receipt else 0
        if review['receipt_fee_policy'] == 'included' and l1_fee != 0:
            raise RpcError('Separate L1 fee conflicts with reviewed inclusive accounting')
        if l1_fee > review['l1_fee_allowance_wei']:
            raise RpcError('Actual L1 fee exceeds the captured allowance; preserve pending intent for operator reconciliation')
        head,head_timestamp = self._head()
        if head-block+1 < self.confirmations: return True
        header = self.rpc.call('eth_getBlockByNumber',[hex(block),False])
        if header is None:
            log('receipt_reorged',transaction=tx_hash); return True
        if not isinstance(header,dict) or rpc_quantity(header.get('number'),'receipt header number') != block:
            raise RpcError('Receipt header has the wrong block number')
        if rpc_hash(header.get('hash'),'receipt header hash') != block_hash:
            log('receipt_reorged',transaction=tx_hash); return True
        timestamp = rpc_quantity(header.get('timestamp'),'receipt header timestamp',minimum=1)
        if timestamp > head_timestamp: raise RpcError('Receipt block timestamp exceeds the head')
        try: day = dt.datetime.fromtimestamp(timestamp,dt.timezone.utc).date().isoformat()
        except (ValueError,OverflowError,OSError) as exc: raise RpcError('Invalid receipt inclusion date') from exc
        transaction = self.rpc.call('eth_getTransactionByHash',[tx_hash])
        self._validate_pending_transaction(transaction,pending,tx_hash)
        if (rpc_quantity(transaction.get('blockNumber'),'transaction block number') != block or
                rpc_hash(transaction.get('blockHash'),'transaction block hash') != block_hash or
                rpc_quantity(transaction.get('transactionIndex'),'transaction index') != transaction_index):
            raise RpcError('Transaction and receipt inclusion differ')
        if gas_used > rpc_quantity(transaction.get('gas'),'transaction gas limit',minimum=1):
            raise RpcError('Receipt gas exceeds the transaction limit')
        try: gas_price = execution_price(transaction,header,receipt)
        except (ValueError,TypeError,KeyError) as exc: raise RpcError('Canonical transaction execution fee cannot be verified') from exc
        if rpc_quantity(transaction.get('type','0x0'),'transaction type') in (0,1) and gas_price != fee_cap(transaction):
            raise RpcError('Legacy receipt price differs from signed gas price')
        if gas_price > review['max_fee_per_gas']:
            raise RpcError('Actual execution price exceeds the captured fee cap')
        cost = gas_used*gas_price + l1_fee + (pending['value'] if success else 0)
        if cost > review['maximum_cost_wei']:
            raise RpcError('Actual transaction cost exceeds the captured fee budget')
        metadata_records = None
        if success and pending.get('metadata_observation') is not None:
            metadata_records = self._confirm_metadata(pending,block,block_hash,head)
        # RPC failover/reorgs can happen during transaction or metadata reads.
        # Recheck depth and the exact header before changing ANY durable state.
        final_head,final_timestamp = self._head()
        if final_head-block+1 < self.confirmations: return True
        final = self.rpc.call('eth_getBlockByNumber',[hex(block),False])
        if (not isinstance(final,dict) or rpc_quantity(final.get('number'),'final receipt header number') != block or
                rpc_hash(final.get('hash'),'final receipt header hash') != block_hash or
                rpc_quantity(final.get('timestamp'),'final receipt timestamp') != timestamp or timestamp > final_timestamp):
            raise RpcError('Receipt block changed before checkpoint')
        try:
            if execution_price(transaction,final,receipt) != gas_price:
                raise RpcError('Canonical execution price changed before checkpoint')
        except (ValueError,TypeError,KeyError) as exc: raise RpcError('Final canonical execution fee cannot be verified') from exc
        previous_state = self.state
        updated = copy.deepcopy(previous_state)
        updated['spent'][day] = positive(updated['spent'].get(day,0),'recorded daily spend',zero=True) + cost
        if success:
            updated['last'][pending['key']] = timestamp
            updated.setdefault('retry_after',{}).pop(pending['key'],None)
        else:
            updated.setdefault('retry_after',{})[pending['key']] = timestamp+self.retry_cooldown
        if metadata_records is not None: updated['metadata_refresh']['notified'] = metadata_records
        updated['pending'] = None
        updated['next_nonce'] = pending['nonce']+1
        updated['receipt_anchor'] = {'number':block,'hash':block_hash,'timestamp':timestamp,'nonce':pending['nonce']}
        updated['last_fee_observation'] = {'transaction':tx_hash,'reported_price_wei':reported_price,
            'execution_price_wei':gas_price,'gas_used':gas_used,'l1_fee_wei':l1_fee,
            'receipt_fee_policy':review['receipt_fee_policy'],'cost_wei':cost}
        self.state = updated
        try: self.save()
        except Exception:
            self.state = previous_state
            raise
        if not success: self.confirmed_reverts += 1
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
        review = self._fee_review(pending)
        try:
            valid = isinstance(transaction,dict) and rpc_hash(transaction.get('hash'),'transaction hash') == rpc_hash(tx_hash,'pending transaction hash') and \
                address(transaction['from']) == self.sender and rpc_quantity(transaction.get('nonce'),'transaction nonce') == pending['nonce'] and \
                address(transaction['to']) == pending['to'] and transaction['input'].lower() == pending['data'].lower() and \
                rpc_quantity(transaction.get('value'),'transaction value') == pending['value'] and \
                transaction_chain_id(transaction) == self.chain and \
                rpc_quantity(transaction.get('gas'),'transaction gas limit',minimum=1) == review['gas_limit'] and \
                fee_cap(transaction) == review['max_fee_per_gas']
        except (KeyError,TypeError,ValueError,AttributeError,RpcError):
            valid = False
        if not valid: raise RpcError('Pending transaction identity mismatch')

    def submit(self, name: str, signature: str, args: tuple[int|str|list[int],...], key: str, *, value: int = 0,
               metadata_observation: dict[str,Any] | None = None, maximum_cost: int | None = None) -> bool:
        if self.state.get('pending'): return False
        if signature == 'bridgeRewards(uint256,address,bytes32)':
            raise ValueError('Reward bridge scheduling is retired')
        if self.fee_intake_version == 1 and signature in ('syncExternal(uint256)','syncAllExternal()'):
            raise ValueError('Creator-payment synchronization is retired in the LP-only profile')
        self._validate_maintenance_config()
        if self.stop_requested():
            log('shutdown_before_submission',action=key); return False
        self._validate_accounting_version()
        if self._defer_for_lifecycle(name,signature): return False
        lp_balance_action=(name,signature) in (('vault','rebalance(uint256,uint128,uint256)'),
            ('compounder','compound(uint256,uint128,uint256)'))
        if lp_balance_action:self._validate_lp_routing()
        if name == 'vault' and signature == 'rebalance(uint256,uint128,uint256)' and not self._rebalance_submission_ready(args): return False
        if self.live: self._validate_checkpoint()
        _,timestamp = self._head()
        retry_after = positive(self.state.get('retry_after',{}).get(key,0),'retry_after',zero=True)
        if timestamp < retry_after:
            self.blocked_actions += 1
            log('action_cooldown',action=key,retry_after=retry_after)
            return False
        to = self.metadata_nft if name == 'nft' and self.metadata_enabled else self.contracts[name]
        if name == 'principal_exit' and signature == PRINCIPAL_BATCH:
            if len(args) != 1: raise ValueError('Principal delivery accepts exactly one array')
            data = encode_principal_batch(args[0])
        else:
            data = encode_batch(*args) if name in ('royalties','rewards') and signature == ROYALTY_BATCH else self._calldata(signature,*args)
        if metadata_observation is not None:
            self._validate_metadata_payload(metadata_observation)
            self._metadata_transaction({'to':to,'data':data,'value':value,'key':key,
                'metadata_observation':metadata_observation})
        tx = {'from':self.sender,'to':to,'data':data,'value':hex(value)}
        self.rpc.call('eth_call',[tx,'latest'])
        estimated = rpc_quantity(self.rpc.call('eth_estimateGas',[tx]),'estimated gas',minimum=1)
        gas_limit = (estimated*125+99)//100
        gas_price = rpc_quantity(self.rpc.call('eth_gasPrice',[]),'gas price')
        if gas_limit > positive(self.config['max_gas_limit'],'max_gas_limit') or \
            gas_price > positive(self.config['max_gas_price_wei'],'max_gas_price_wei'):
            self.blocked_actions += 1
            log('gas_cap_exceeded',action=key); return False
        cost = gas_limit*gas_price + value + positive(self.config.get('l1_fee_allowance_wei',0),'l1_fee_allowance_wei',zero=True)
        if maximum_cost is not None and cost > positive(maximum_cost,'maximum_cost',zero=True):
            self.blocked_actions += 1
            log('lp_conversion_uneconomic' if name == 'rewards' else 'royalty_conversion_uneconomic',action=key,gas_cost_wei=str(cost),maximum_cost_wei=str(maximum_cost))
            return False
        day = dt.datetime.fromtimestamp(timestamp,dt.timezone.utc).date().isoformat()
        if cost > positive(self.config['max_transaction_cost_wei'],'max_transaction_cost_wei') or \
            int(self.state['spent'].get(day,0))+cost > positive(self.config['max_daily_cost_wei'],'max_daily_cost_wei'):
            self.blocked_actions += 1
            log('cost_cap_exceeded',action=key); return False
        if self._defer_for_lifecycle(name,signature): return False
        if not self.live:
            log('dry_run',action=key,to=to,calldata=data,estimated_cost_wei=str(cost))
            return False
        # Revalidate code after simulation and before signing; stop on mutable deployments.
        self._validate_code_hashes()
        if lp_balance_action:self._validate_lp_routing()
        nonce = rpc_quantity(self.rpc.call('eth_getTransactionCount',[self.sender,'pending']),'pending nonce')
        latest_nonce = rpc_quantity(self.rpc.call('eth_getTransactionCount',[self.sender,'latest']),'latest nonce')
        if nonce != latest_nonce or nonce != self.state.get('next_nonce'):
            log('nonce_reconciliation_required',action=key,expected_nonce=self.state.get('next_nonce'),
                latest_nonce=latest_nonce,pending_nonce=nonce)
            raise RpcError('Unreconciled keeper nonce; stop other signers and restore/reconcile state')
        balance = rpc_quantity(self.rpc.call('eth_getBalance',[self.sender,'latest']),'keeper balance')
        if balance < cost:
            log('keeper_balance_insufficient',action=key,balance_wei=str(balance),required_wei=str(cost))
            raise RpcError('Keeper native balance is below the bounded transaction cost')
        if self.stop_requested():
            log('shutdown_before_submission',action=key); return False
        # A notice may become active during simulation, code/nonce or balance
        # reads. The on-chain guard still covers later inclusion-time races.
        if self._defer_for_lifecycle(name,signature): return False
        if name == 'vault' and signature == 'rebalance(uint256,uint128,uint256)' and not self._rebalance_submission_ready(args): return False
        pending = {'key':key,'nonce':nonce,'to':to,'data':data,'value':value,'day':day,'hash':None}
        pending['fee_review'] = {'schema':1,'gas_limit':gas_limit,'max_fee_per_gas':gas_price,
            'l1_fee_allowance_wei':positive(self.config.get('l1_fee_allowance_wei',0),'l1_fee_allowance_wei',zero=True),
            'maximum_cost_wei':cost,'receipt_fee_policy':self.fee_policy}
        self._fee_review(pending)
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

    def _validate_metadata_record(self, record: Any) -> None:
        if not isinstance(record,dict): raise ValueError('Malformed metadata observation')
        ordinal = positive(record.get('ordinal'),'metadata ordinal')
        token = positive(record.get('token_id'),'metadata token ID',zero=True)
        if type(record.get('ordinal')) is not int or record.get('token_id') != str(token) or \
            ordinal > MAX_METADATA_SUPPLY or token >= 1 << 256 or \
            type(record.get('available')) is not bool or type(record.get('traits_ready')) is not bool or \
            type(record.get('stage')) is not int or not 0 <= record['stage'] <= (4 if self.accounting_version == 4 else 3) or \
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

    def _confirm_metadata(self, pending: dict[str,Any], block: int, block_hash: str, head: int) -> dict[str,Any]:
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
        # Return a candidate checkpoint. Receipt finality and the durable save
        # must succeed before publishing it, including in-memory state.
        records = dict(self.state['metadata_refresh']['notified'])
        if not observation_valid:
            # The event still happened, but its old trigger cannot describe the
            # cache state. Forget prior fingerprints so a retry is never hidden.
            for record in payload['records']: records.pop(str(record['ordinal']),None)
            log('metadata_observation_invalidated',action=pending['key']); return records
        for record in execution_records:
            records[str(record['ordinal'])] = {**record,'observed_number':block,
                'observed_hash':block_hash.lower(),'notification_number':block,
                'notification_hash':self._metadata_hash(block_hash.lower())}
        return records

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

    def _asset_word(self,word: str) -> str:
        if int(word,16) >= 1 << 160: raise RpcError('Noncanonical currency in contract response')
        return self._asset('0x'+word[-40:])

    def _bucket(self,bucket: int) -> tuple[list[str],list[str]]:
        fields = decode_words(self.rpc.eth_call(self.contracts['vault'],calldata('group(uint256)',bucket)))
        try: position = decode_position(fields,self.accounting_version)
        except ValueError as exc: raise RpcError('Unexpected or malformed vault group ABI') from exc
        status = position['status']
        if status in ('none','dormant'): return fields,[]
        if int(fields[0],16) == 0:
            raise RpcError('Malformed shared-pool state')
        if self.accounting_version not in (3,4):
            if int(fields[8],16) == 0 or int(fields[13],16) == 0:
                raise RpcError('Missing shared-pool provenance')
            for index in (9,10,12,14): self._address_word(fields[index])
            self._asset_word(fields[11])
        if self.view('vault','bucketTotalShares(uint256)',bucket) == 0:
            raise RpcError('Shared pool has no shares')
        pool_id = '0x'+fields[0]
        if self.view('vault','poolBucket(bytes32)',pool_id) != bucket:
            raise RpcError('Pool occupancy does not match discovered bucket')
        if status == 'active' and int(fields[1],16) == 0:
            raise RpcError('Active shared pool has no LP position')
        if status == 'parked' and int(fields[1],16) != 0:
            raise RpcError('Parked shared pool still has an LP position')
        if status == 'exited' and (int(fields[1],16) or int(fields[2],16) or int(fields[3],16) or not self.lp_exit_started()):
            raise RpcError('Exited shared pool retains principal or lacks its lifecycle lock')
        if status == 'parked' and self.accounting_version not in (3,4) and (
                position['location_chain'] != self.chain or position['location_vault'] != self.contracts['vault']):
            raise RpcError('Parked principal is not in this local vault')
        config = decode_words(self.rpc.eth_call(self.contracts['pools'],calldata('get(bytes32)',pool_id)))
        if len(config) != 14 or '0x'+keccak256(bytes.fromhex(''.join(config[:5]))).hex() != pool_id:
            raise RpcError('Pool configuration does not match its identity')
        if int(config[0],16) >= int(config[1],16): raise RpcError('Invalid venue currency ordering')
        accounting = decode_words(self.rpc.eth_call(self.contracts['pools'],calldata('accounting(bytes32)',pool_id)))
        if len(accounting) != 14 or accounting[1:] != config[1:]:
            raise RpcError('Accounting configuration differs from the venue policy')
        tokens = [self._asset_word(accounting[0]),self._address_word(accounting[1])]
        if self.accounting_version in (2,3,4):
            if accounting != config: raise RpcError('Native accounting currencies differ from actual venue currencies')
        elif int(config[0],16) == 0:
            wrapper = decode_words(self.rpc.eth_call(self.contracts['pools'],calldata('nativeAsset(bytes32)',pool_id)))
            if len(wrapper) != 1 or self._address_word(wrapper[0]) != tokens[0] or tokens[0] == tokens[1]:
                raise RpcError('Native accounting wrapper mismatch')
        elif accounting[0] != config[0]:
            raise RpcError('ERC20 accounting asset differs from the venue')
        # Legacy WETH normalization is confined to version1; native versions2/3
        # keeps assetzero and never consults the optional wrapper getter.
        return fields,tokens

    def _sync_external(self, bucket: int) -> bool:
        if self.fee_intake_version == 1:
            raise RpcError('Creator-payment synchronization is retired in the LP-only profile')
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

    def _convert_royalties(self) -> bool:
        return self._convert_rewards(self.royalties)

    def _convert_rewards(self, worker) -> bool:
        try: return worker.scan_once()
        except (ValueError,RpcError) as exc:
            if self.state.get('pending'): raise
            self.blocked_actions += 1
            log(worker.key+'_deferred',**error_context(exc))
            return False

    def _buyback_tasks(self) -> list[dict[str,Any]]:
        tasks = self.config.get('buybacks',[])
        if not isinstance(tasks,list) or len(tasks) > MAX_BUYBACK_TASKS:
            raise ValueError('Buybacks require a bounded task list')
        tokens = set()
        for task in tasks:
            if not isinstance(task,dict): raise ValueError('Buyback task must be an object')
            token = self._asset(task.get('token'))
            amount = positive(task.get('amount'),'buyback amount')
            pool = task.get('pool_id')
            if amount >= 1 << 256 or not isinstance(pool,str) or \
                    not re.fullmatch(r'0x[0-9a-fA-F]{64}',pool) or token in tokens:
                raise ValueError('Invalid or duplicate buyback task')
            tokens.add(token)
        return tasks

    def _buyback_once(self,tasks: list[dict[str,Any]]) -> bool:
        """Bounded currency rotation; every actual submission uses normal guards."""
        if not tasks: return False
        start = self.state.get('buyback_cursor',0) % len(tasks)
        for offset in range(len(tasks)):
            slot = (start+offset) % len(tasks)
            task = tasks[slot]
            token = self._asset(task['token'])
            amount = positive(task['amount'],'buyback amount')
            # Advance before submit() persists any intent. Even a funded first
            # currency or a reverted/deferred task cannot monopolize the next turn.
            self.state['buyback_cursor'] = slot+1
            try:
                if self.view('fees','buybackBalance(address)',token) >= amount:
                    _,fresh = self._head()
                    if self.submit('buyback','execute(address,uint256,bytes32,uint256)',
                            (token,amount,task['pool_id'],fresh+180),f'buyback:{token}'):
                        return True
            except (ValueError,RpcError) as exc:
                if self.state.get('pending'): raise
                self.blocked_actions += 1
                log('buyback_deferred',token=token,**error_context(exc))
        self.save()
        return False

    def cycle(self) -> None:
        if self.poll_pending(): return
        self.principal_distribution.configure()
        self._validate_maintenance_config()
        buybacks = self._buyback_tasks()
        self._validate_accounting_version()
        if self.canonical_state() != 0: return
        paused = self.view('access','paused()') != 0
        self.strategy_paused = paused
        preparing = self.preparation_active()
        lp_exit = self.lp_exit_started()
        if self.view('access','isSealed()') != 1: raise RpcError('Protocol is not sealed')
        if self.view('access','keepers(address)',self.sender) != 1: raise RpcError('Configured sender is not an authorized keeper')
        if lp_exit and self.principal_distribution.enabled:
            if self.principal_distribution.run(): return
        # Three-way durable priority: LP conversion, royalty conversion, then
        # maintenance. One busy stream cannot consume every serial nonce slot.
        workers = (self.lp_rewards,self.royalties)
        turn = self.state.get('conversion_turn',0)
        self.state['conversion_turn'] = (turn+1)%3
        self.save()
        if turn < 2 and workers[turn].enabled and not paused and not preparing:
            if self._convert_rewards(workers[turn]): return
        # Keep the historical three-way conversion cursor intact. Alternate
        # buyback priority only when reaching maintenance; busy maintenance and
        # metadata cannot indefinitely hide funded buyback reserves. Metadata's
        # own alternation advances only if reached, preserving LP opportunities.
        buyback_first = False
        if buybacks and not paused and not preparing:
            buyback_first = self.state.get('buyback_priority',False)
            self.state['buyback_priority'] = not buyback_first
            self.save()
            if buyback_first and self._buyback_once(buybacks): return
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
                self._validate_maintenance_settings(item)
                fields,tokens = self._bucket(bucket)
                status = decode_position(fields,self.accounting_version)['status']
                if self.maintenance_policy_version == 2 and status != 'active':
                    self._store_rebalance_schedule(bucket,None)
                if status in ('none','dormant'): continue
                # Canonical funded revenue and claims remain available during
                # pauses and while the physical LP is away. No principal moves.
                if self.fee_intake_version == 0 and item.get('sync_external_rewards',True) and self._sync_external(bucket): return
                if paused: continue
                if status == 'active' and not lp_exit:
                    minimum = positive(item.get('minimum_liquidity',1),'minimum_liquidity')
                    _,fresh = self._head(); deadline = fresh+180
                    maintenance_failed = False
                    if not preparing:
                        try:
                            self._validate_lp_routing()
                            if self.adaptive_range_enabled and self._adaptive_range_target('0x'+fields[0],fresh):
                                if self.submit('strategy','applyKeeperRange(bytes32)',('0x'+fields[0],),f'range_policy:{bucket}'): return
                            if self._rebalance_due(bucket,fields,fresh):
                                if self.submit('vault','rebalance(uint256,uint128,uint256)',(bucket,minimum,deadline),f'rebalance:{bucket}'): return
                            if item.get('compound',True):
                                reserves = [self.view('fees','compoundBalance(uint256,address)',bucket,t) for t in tokens]
                                if self._compound_due(bucket,tokens,reserves,item,now,fields):
                                    if self.submit('compounder','compound(uint256,uint128,uint256)',(bucket,minimum,deadline),f'compound:{bucket}'): return
                        except RpcError as exc:
                            # Fee collection has no price dependency or principal
                            # movement. Only an authenticated active bucket may
                            # proceed to its separately guarded due harvest.
                            # Config/ABI ValueError stays fail-closed outside.
                            if self.state.get('pending'): raise
                            maintenance_failed = True
                            self.blocked_actions += 1
                            log('maintenance_deferred',bucket_id=str(bucket),**error_context(exc))
                    # Fresh accounting4 defaults to hourly independent collection;
                    # historical profiles keep their original omitted-field schedule.
                    default_harvest = 3600 if self.accounting_version == 4 else 14400
                    interval = positive(item.get('harvest_interval_seconds',default_harvest),'harvest_interval_seconds')
                    if item.get('harvest',True) and now-int(self.state['last'].get(f'harvest:{bucket}',0)) >= interval:
                        if maintenance_failed:
                            _,fresh = self._head(); deadline = fresh+180
                        if self.submit('vault','collectFees(uint256,uint256)',(bucket,deadline),f'harvest:{bucket}'): return
            except (ValueError,RpcError) as exc:
                if self.state.get('pending'): raise
                self.skipped_buckets += 1
                log('bucket_skipped',bucket_id=str(bucket),**error_context(exc))
        if batch: self.save()
        if self.metadata_enabled and not metadata_first and self._refresh_metadata(): return
        if paused:
            log('protocol_paused'); return
        if preparing: return
        if not buyback_first and self._buyback_once(buybacks): return
        for i in ((turn+1)%2, turn%2):
            if i != turn and workers[i].enabled and self._convert_rewards(workers[i]): return

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',required=True);parser.add_argument('--live',action='store_true')
    parser.add_argument('--once',action='store_true');parser.add_argument('--resolve-pending')
    parser.add_argument('--initialize-state',action='store_true')
    args = parser.parse_args()
    if args.initialize_state and (args.live or args.resolve_pending): parser.error('Initialization cannot sign or resolve a transaction')
    watchdog = ProgressWatchdog.from_environment()
    watchdog.pulse(force=True)
    config = json.loads(Path(args.config).read_text())
    interval = positive(config.get('interval_seconds',600),'interval_seconds')
    if interval < 60: raise ValueError('Polling interval must be at least 60 seconds')
    stop = False
    def halt(*_: Any) -> None:
        nonlocal stop;stop=True
    signal.signal(signal.SIGINT,halt);signal.signal(signal.SIGTERM,halt)
    with process_lock(config.get('lock_path','var/keeper.lock')):
        # Wrap before construction: a live startup also validates signer/chain
        # state. Completed reads report progress; blocked I/O has no pulse thread.
        if watchdog.enabled:
            rpc = ProgressRPC(Rpc(config['rpc_urls'],positive(config['chain_id'],'chain_id')),watchdog)
            keeper = Keeper(config,live=args.live,rpc=rpc)
        else:
            keeper = Keeper(config,live=args.live)
        watchdog.pulse(force=True)
        keeper.stop_requested = lambda: stop
        if args.initialize_state:
            keeper.initialize_state();return
        if args.resolve_pending:
            keeper.resolve_pending(args.resolve_pending);return
        while not stop:
            watchdog.pulse(force=True)
            success = keeper.run_cycle()
            watchdog.pulse(force=True)
            if args.once and not success: raise SystemExit(1)
            if args.once: break
            delay = min(interval * 2**min(keeper.cycle_failures,3),max(interval,3600))
            for _ in range(delay):
                if stop: break
                watchdog.pulse()
                time.sleep(1)

if __name__ == '__main__':
    try: main()
    except Exception as exc:
        log('keeper_halted',**error_context(exc))
        raise SystemExit(1) from None
