"""Opt-in collective-exit delivery. No governance initiation, recipient or signer."""
import copy
import re

from zzz_ops.abi import address, calldata, decode_words, keccak256
from zzz_ops.rpc import RpcError

BATCH = 'distributePrincipal(uint256[])'
MAX_BATCH = 32
MAX_SUPPLY = 1000
PRIORITY = 'principal_distribution_first'


def encode_batch(ids):
    """Only one bounded uint256[] argument; no generic dynamic calldata path."""
    if (not isinstance(ids, (list, tuple)) or not 1 <= len(ids) <= MAX_BATCH or
            any(type(identifier) is not int or not 0 < identifier < 1 << 256 for identifier in ids) or
            len(set(ids)) != len(ids)):
        raise ValueError('Principal delivery requires one to32 distinct uint256 NFT IDs')
    return ('0x'+keccak256(BATCH.encode()).hex()[:8]+f'{32:064x}'+f'{len(ids):064x}'+
            ''.join(f'{identifier:064x}' for identifier in ids))


class PrincipalDistribution:
    def __init__(self, keeper):
        self.k = keeper
        self.enabled = False
        self.configured = False
        # New configuration must not strand recovery of an already-saved hash.
        if not keeper.state.get('pending'):
            self.configure()

    def configure(self):
        if self.configured:
            return
        keeper = self.k
        cfg = keeper.config.get('principal_distribution', {'enabled': False})
        if not isinstance(cfg,dict) or type(cfg.get('enabled')) is not bool:
            raise ValueError('Principal distribution requires explicit boolean enable control')
        self.enabled = cfg['enabled']
        if not self.enabled:
            if set(cfg) != {'enabled'}:
                raise ValueError('Disabled principal distribution accepts only its enable control')
            self.configured = True
            return
        if (keeper.accounting_version != 4 or
                not {'enabled','batch_size','nft'} <= set(cfg) <=
                    {'enabled','batch_size','nft','retry_interval_seconds'}):
            raise ValueError('Principal distribution requires explicit accounting4 and reviewed settings')
        self.batch = cfg['batch_size']
        if type(self.batch) is not int or not 1 <= self.batch <= MAX_BATCH:
            raise ValueError('Principal distribution batch must be one to32')
        self.retry_interval = cfg.get('retry_interval_seconds',3600)
        if type(self.retry_interval) is not int or not 60 <= self.retry_interval <= 86400:
            raise ValueError('Principal delivery retry interval must be60-86400 seconds')
        if type(keeper.state.get(PRIORITY,True)) is not bool:
            raise ValueError('Invalid saved principal-distribution priority; preserve and review the journal')
        pin = cfg['nft']
        if not isinstance(pin,dict) or set(pin) != {'address','code_hash'}:
            raise ValueError('Principal distribution requires a reviewed NFT runtime pin')
        self.nft = address(pin['address'])
        self.code_hash = pin['code_hash']
        if (not isinstance(self.code_hash,str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}',self.code_hash) or
                int(self.code_hash,16) == 0 or self.nft in keeper.contracts.values() and
                any(role not in ('nft','lp_nft','royalty_nft') and target == self.nft
                    for role,target in keeper.contracts.items())):
            raise ValueError('Principal-distribution NFT pin is invalid or collides with another module')
        self.code_hash = self.code_hash.lower()
        cursor = keeper.state.get('principal_distribution_cursor',1)
        if type(cursor) is not int or not 1 <= cursor <= MAX_SUPPLY:
            raise ValueError('Invalid saved principal-distribution cursor; preserve and review the journal')
        self.configured = True

    def _save_cursor(self, cursor):
        previous = self.k.state
        self.k.state = copy.deepcopy(previous)
        self.k.state['principal_distribution_cursor'] = cursor
        try:
            self.k.save()
        except BaseException:
            self.k.state = previous
            raise

    def prefer_first(self):
        """Alternate serial nonce priority durably, never payment truth."""
        first = self.k.state.get(PRIORITY,True)
        previous = self.k.state
        self.k.state = copy.deepcopy(previous)
        self.k.state[PRIORITY] = not first
        try:
            self.k.save()
        except BaseException:
            self.k.state = previous
            raise
        return first

    def _read(self, target, signature, *args, count=1):
        words = decode_words(self.k.rpc.eth_call(target,calldata(signature,*args)))
        if len(words) != count:
            raise RpcError('Principal-distribution ABI differs from its reviewed profile')
        return tuple(int(word,16) for word in words)

    def _bindings(self):
        k = self.k
        code = k.rpc.call('eth_getCode',[self.nft,'latest'])
        if (not isinstance(code,str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+',code) or
                '0x'+keccak256(bytes.fromhex(code[2:])).hex() != self.code_hash):
            raise RpcError('Principal-distribution NFT runtime differs')
        module = '0x'+keccak256(b'ZZZNFT').hex()
        if (k.view('access','module(bytes32)',module) != int(self.nft,16) or
                self._read(self.nft,'access()')[0] != int(k.contracts['access'],16)):
            raise RpcError('Principal-distribution NFT/controller binding differs')

    def run(self):
        """One ordinary budgeted submission. Ledger truth, never a local paid cache."""
        k = self.k
        if not self.enabled or k.state.get('pending'):
            return False
        if not k.lp_exit_started():
            return False
        self._bindings()
        phase = k.view('principal_exit','exitPhase()')
        if phase not in (1,2,3):
            raise RpcError('Unknown principal-distribution exit phase')
        if phase == 1:
            return False  # Only governance may close buckets; never use keeper authority.
        if phase == 3 and k.view('principal_exit','remainingETH()') == 0 and k.view('principal_exit','remainingZZZ()') == 0:
            return False  # Exact classified liabilities, never a guessed raw balance.
        count = k.view('principal_exit','exitMintedCount()')
        if not 1 <= count <= MAX_SUPPLY:
            raise RpcError('Collective-exit NFT inventory exceeds its reviewed bound')
        if phase == 2:
            cursor = k.view('principal_exit','allocationCursor()')
            if not 1 <= cursor <= count:
                raise RpcError('Collective-exit allocation cursor is inconsistent')
            return k.submit('principal_exit','allocatePrincipal(uint256)',(self.batch,),
                            f'principal_allocate:{cursor}')
        start = k.state.get('principal_distribution_cursor',1)
        if type(start) is not int or not 1 <= start <= count:
            raise RpcError('Principal-distribution cursor differs from the frozen inventory')
        end = min(start+self.batch,count+1)
        key = f'principal_distribute:{start}'
        _,now = k._head()
        last = k.state['last'].get(key,0)
        if type(last) is not int or not 0 <= last <= now < 1 << 64:
            raise RpcError('Principal-distribution retry clock is inconsistent')
        # A successful batch can defer EVERY receiver. Its canonical receipt
        # clocks the next attempt, never proves a holder was paid. Paid-revert
        # cooldowns remain enforced independently by the ordinary submit path.
        if key in k.state['last'] and now < last+self.retry_interval:
            self._save_cursor(1 if end > count else end)
            return False
        ids = []
        for ordinal in range(start,end):
            identifier = self._read(self.nft,'tokenAtOrdinal(uint256)',ordinal)[0]
            if (identifier == 0 or self._read(self.nft,'mintOrdinalOf(uint256)',identifier)[0] != ordinal):
                raise RpcError('Principal-distribution NFT ordinal identity differs')
            eth, zzz, allocated, paid = self._read(k.contracts['principal_exit'],
                'principalOf(uint256)',identifier,count=4)
            if allocated != 1 or paid not in (0,1):
                raise RpcError('Principal-distribution allocation is inconsistent')
            if not paid and (eth or zzz):
                ids.append(identifier)
        # Persist scan progress before submit() can journal or broadcast. A failed
        # receiver/transaction is not marked paid here and is retried next rotation.
        self._save_cursor(1 if end > count else end)
        if not ids:
            return False
        encode_batch(ids)  # Strictly validate before entering the signer path.
        return k.submit('principal_exit',BATCH,(ids,),key)
