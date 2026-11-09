"""Authenticated reads shared by typed, unsigned governance management adapters."""
from __future__ import annotations

import re

from frontend_api.service import _bool
from zzz_ops.abi import keccak256
from zzz_ops.errors import RpcError
from zzz_ops.manual_lp_review import Reader, UnsupportedGovernanceEnvelope


class ManagementBlocked(ValueError):
    """A local, non-sensitive blocker with a stable operator-facing code."""
    def __init__(self, code, message):
        self.code, self.message = code, message
        super().__init__(message)


class ManagementReader(Reader):
    def base(self, governance, *, paused, phase, allow_preparation=False):
        p=self.p;c=self.targets
        life=p._verify_deployment(self.block,allow_locked=True)
        for role,item in self.extra.items():p._code(item['address'],item['code_hash'],self.block)
        for role,label in [('oracle','ZZZOracle'),('fees','ZZZFeeController')]:
            if self.uint('access','module(bytes32)','0x'+keccak256(label.encode()).hex())!=int(c[role],16):
                raise ManagementBlocked('module_binding_changed','A reviewed module binding changed.')
            self.binding(role,'access()','access')
        for role,method,expected in [('principal_exit','validation()','custody_validation'),
                ('custody_validation','migration()','principal_exit'),('custody_validation','access()','access'),
                ('pools','activationAssets()','activation_assets'),('activation_assets','registry()','pools'),
                ('activation_assets','access()','access'),('oracle','contributionPricing()','contribution_pricing'),
                ('contribution_pricing','oracle()','oracle'),('contribution_pricing','access()','access')]:
            self.binding(role,method,expected)
        for role in ('principal_exit','vault','budget','portfolio_policy','contribution_pricing'):
            if self.uint(role,'RESIDUAL_REINVEST_VERSION()')!=1:
                raise ManagementBlocked('capability_changed','A reviewed management capability changed.')
        if self.uint('fees','FEE_INTAKE_VERSION()')!=1:
            raise ManagementBlocked('fee_profile_changed','The fee accounting profile changed.')
        if (not self.flag('access','isSealed()') or life['state_code']!=0 or
                self.uint('access','canonicalState()')!=0):
            raise ManagementBlocked('canonical_locked','The deployment is not sealed and canonically operating.')
        observed_pause=self.flag('access','paused()')
        if paused is not None and observed_pause is not paused:
            raise ManagementBlocked('pause_state_mismatch','This operation requires a different pause state.')
        preparation=self.flag('access','preparationActive()')
        if preparation and not allow_preparation:
            raise ManagementBlocked('preparation_active','Finish or cancel preparation before this operation.')
        actual_phase=self.uint('principal_exit','exitPhase()')
        if actual_phase!=phase or self.flag('access','lpExitStarted()') is not bool(phase):
            raise ManagementBlocked('exit_phase_mismatch','This operation does not match the collective-exit phase.')
        if self.uint('access','governance()')!=int(governance,16):
            raise ManagementBlocked('governance_changed','The reviewed wallet is not current governance.')
        if not (allow_preparation and preparation) and not self.flag('access','canConfigure(address)',governance):
            raise ManagementBlocked('governance_unavailable','Current governance cannot authorize this operation.')
        code=p.rpc.call('eth_getCode',[governance,self.block])
        if not isinstance(code,str) or re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*',code) is None:
            raise RpcError('Malformed governance runtime code')
        if code!='0x':
            raise UnsupportedGovernanceEnvelope('unsupported_contract_wallet_envelope: direct empty-code governance EOA required')
        zzz=self.uint('principal_exit','currentZZZ()')
        if zzz==0 or self.uint('activation_assets','zzz()')!=zzz:
            raise ManagementBlocked('fixed_token_mismatch','The fixed contribution and exit token identities differ.')
        asset='0x'+f'{zzz:040x}'
        if asset not in p.assets:
            raise ManagementBlocked('fixed_token_unreviewed','The fixed ZZZ lacks a reviewed runtime descriptor.')
        p._code(asset,p.assets[asset].code_hash,self.block)
        # Raw closure/distribution never consult USD feeds, token decimals,
        # automatic swap catalogues or ordinary operations-enabled flags.
        return {'governance':governance,'governance_code':code,'paused':observed_pause,
            'canonical_state':0,'exit_phase':actual_phase,'preparation_active':preparation,
            'preparation_nonce':str(self.uint('access','preparationNonce()')),
            'preparation_hash':'0x'+self.read('access','preparationHash()')[0],
            'fixed_zzz':asset,'governance_wallet_scope':'direct_empty_code_governance_eoa_only'}
