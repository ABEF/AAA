"""Explicit sampled-confirmation profile; reads never authorize a rebalance."""
from __future__ import annotations

import re
import time

from zzz_ops.abi import address, calldata, decode_words, keccak256
from zzz_ops.rpc import RpcError

CHECK_SECONDS = 240
# Accepted only when reading an existing schedule; new checks use four minutes.
LEGACY_CHECK_SECONDS = 300
STATE_NAMESPACE = 'observed_rebalance_v1'


class RebalanceConfirmation:
    def __init__(self,keeper):
        self.k=keeper
        self.version=keeper.config.get('rebalance_confirmation_version',0)
        if type(self.version) is not int or self.version not in (0,1,2):
            raise ValueError('Unsupported explicit rebalance confirmation profile')
        if self.version in (1,2):
            interval=keeper.config.get('interval_seconds')
            if type(interval) is not int or not 60<=interval<=CHECK_SECONDS:
                raise ValueError('Confirmation requires explicit interval_seconds 60-240; no historical default')
            if keeper.accounting_version != 4 or keeper.maintenance_policy_version != 2:
                raise ValueError('Rebalance confirmation requires accounting4 and maintenance2')
            if 'rebalance_confirmation' not in keeper.contracts:
                raise ValueError('Missing reviewed rebalance confirmation helper')
            pin=keeper.config.get('code_hashes',{}).get('rebalance_confirmation','')
            if not isinstance(pin,str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}',pin) or int(pin,16)==0:
                raise ValueError('Missing reviewed rebalance confirmation runtime')
            self.budget=address(keeper.config.get('idle_compounding_budget'))
            pin=keeper.config.get('code_hashes',{}).get('idle_compounding_budget','')
            if not isinstance(pin,str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}',pin) or int(pin,16)==0:
                raise ValueError('Confirmation requires the reviewed Vault Budget runtime')
        self.last_observation=None

    def validate(self):
        return self.status(0,with_candidate=False)

    def status(self,bucket,*,with_candidate=True):
        """Read policy, condition and candidate at one fresh canonical block."""
        from keeper.monitor import rpc_hash, rpc_quantity
        if self.version not in (1,2):raise ValueError('Confirmation profile is not enabled')
        k=self.k
        header=k.rpc.call('eth_getBlockByNumber',['latest',False])
        if not isinstance(header,dict):raise RpcError('Missing confirmation header')
        number=rpc_quantity(header.get('number'),'confirmation block number')
        stamp=rpc_quantity(header.get('timestamp'),'confirmation block timestamp',minimum=1)
        block={'blockHash':rpc_hash(header.get('hash'),'confirmation block hash'),'requireCanonical':True}
        if abs(time.time()-stamp)>600:raise RpcError('Stale confirmation snapshot')
        helper=k.contracts['rebalance_confirmation'];strategy=k.contracts['strategy'];access=k.contracts['access']
        def read(target,signature,*args,count=1):
            values=decode_words(k.rpc.call('eth_call',[{'to':target,'data':calldata(signature,*args)},block]))
            if len(values)!=count:raise RpcError('Malformed confirmation response')
            return [int(value,16) for value in values]
        try:
            for role,target in tuple((role,k.contracts[role]) for role in ('access','strategy','rebalance_confirmation','vault'))+(
                    ('idle_compounding_budget',self.budget),):
                code=k.rpc.call('eth_getCode',[target,block])
                pin=k.config.get('code_hashes',{}).get(role,'')
                if (not isinstance(code,str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+',code) or
                        not isinstance(pin,str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}',pin) or
                        '0x'+keccak256(bytes.fromhex(code[2:])).hex()!=pin.lower()):
                    raise RpcError('Confirmation runtime differs from the reviewed profile')
            for target,signature,value in ((strategy,'access()',int(access,16)),
                    (strategy,'rebalanceConfirmation()',int(helper,16)),
                    (strategy,'REBALANCE_CONFIRMATION_VERSION()',self.version),
                    (helper,'strategy()',int(strategy,16)),(helper,'access()',int(access,16)),
                    (helper,'REBALANCE_CONFIRMATION_VERSION()',self.version),
                    (k.contracts['vault'],'migrationBudget()',int(self.budget,16)),
                    (self.budget,'vault()',int(k.contracts['vault'],16)),
                    (self.budget,'access()',int(access,16)),(self.budget,'REBALANCE_CONFIRMATION_VERSION()',self.version)):
                if read(target,signature)!=[value]:raise RpcError('Confirmation helper binding or capability differs')
            if read(access,'module(bytes32)','0x'+keccak256(b'ZZZStrategy').hex())!=[int(strategy,16)]:
                raise RpcError('Confirmation Strategy module differs')
            if read(access,'module(bytes32)','0x'+keccak256(b'ZZZVault').hex())!=[int(k.contracts['vault'],16)]:
                raise RpcError('Confirmation Vault module differs')
            duration=read(helper,'duration()')[0];gap=read(helper,'maxObservationGap()')[0]
            revision=read(helper,'policyRevision()')[0];review=read(helper,'reviewHash()')[0]
            if (not 60<=duration<=604800 or not 0<=gap<=duration//2 or not 0<=revision<1<<64 or
                    (gap>0 and review==0)):
                raise RpcError('Confirmation policy exceeds reviewed bounds')
            policy={'version':self.version,'block_number':number,'block_hash':block['blockHash'],
                'block_timestamp':stamp,'duration_seconds':duration,'maximum_gap_seconds':gap,
                'policy_revision':revision,'review_hash':'0x'+f'{review:064x}'}
            if self.version==2:
                required=read(helper,'requireReferenceExit()')[0];reference_review=read(helper,'referenceReviewHash()')[0]
                if required not in (0,1) or not required and reference_review==0:
                    raise RpcError('Invalid independent-reference confirmation policy')
                policy.update(reference_exit_required=bool(required),reference_review_hash='0x'+f'{reference_review:064x}')
            if not with_candidate:return policy
            side,identity,manual=read(helper,'condition(uint256)',bucket,count=3)
            if self.version==2 and not manual:
                raw=read(strategy,'needsRebalance(uint256)',bucket)[0]
                if raw not in (0,1):raise RpcError('Invalid raw rebalance eligibility')
                if raw:
                    physical,reference=read(helper,'marketSides(uint256)',bucket,count=2)
                    if physical not in (1,2) or reference not in (0,1,2) or side!=(
                            0 if policy['reference_exit_required'] and physical!=reference else physical):
                        raise RpcError('Confirmation differs from independent-market evidence')
                    policy.update(physical_exit_side=physical,reference_exit_side=reference)
            old_identity,first,last,old_side=read(helper,'observations(uint256)',bucket,count=4)
            if side not in (0,1,2) or manual not in (0,1) or old_side not in (0,1,2):
                raise RpcError('Malformed confirmation condition')
            if (side!=0 and (manual or identity==0)) or (side==0 and identity!=0):
                raise RpcError('Contradictory confirmation condition identity')
            if (not 0<=first<=last<=stamp or last>=1<<64 or
                    (old_identity==0 and (first!=0 or last!=0 or old_side!=0)) or
                    (old_identity!=0 and (first==0 or old_side==0))):
                raise RpcError('Malformed confirmation observation')
            ready=read(strategy,'rebalanceReady(uint256)',bucket)[0]
            if ready not in (0,1) or read(helper,'ready(uint256)',bucket)!=[ready]:
                raise RpcError('Malformed or contradictory confirmation readiness')
            expected=bool(manual) or (gap!=0 and side!=0 and old_identity==identity and old_side==side and
                first!=0 and stamp-last<=gap and stamp-first>=duration)
            if bool(ready)!=expected:raise RpcError('Confirmation readiness differs from observed evidence')
            result={**policy,
                'side':side,'identity':'0x'+f'{identity:064x}','manual':bool(manual),'ready':bool(ready),
                'first_seen':first,'last_seen':last,
                'observation_identity':'0x'+f'{old_identity:064x}','observation_side':old_side}
            self.last_observation=result
            return result
        except (ValueError,TypeError,KeyError) as exc:
            raise RpcError('Confirmation capability is unavailable or differs') from exc

    @staticmethod
    def observation_due(record,now):
        if record['manual'] or record['maximum_gap_seconds']==0:return False
        if record['side']==0:return record['observation_identity']!='0x'+'0'*64
        # The caller already gates ordinary observations to four-minute checks.
        # A receipt a few seconds after the previous check must not suppress
        # this renewal and accidentally skip the next scheduled check.
        return True
