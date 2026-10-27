"""Profile-4 collective principal return; never reward or earnings income."""
from frontend_api.service import ProjectionError, ZERO, _bool

PHASES = ('operating', 'closing', 'allocating', 'ready')


def read(p, identifier, status, shares, owner, lifecycle, block):
    phase = lifecycle['lp_exit_phase_code']
    if phase >= len(PHASES) or bool(phase) != lifecycle['lp_exit_started']:
        raise ProjectionError('Collective exit phase differs from the irreversible lifecycle')
    zzz = p._addr('principal_exit', 'currentZZZ()', block=block)
    if zzz not in p.assets or zzz == ZERO:
        raise ProjectionError('Fixed principal-return token lacks a reviewed descriptor')
    row = p._call(p.contracts['principal_exit'].address, 'principalOf(uint256)', identifier, block=block, words=4)
    eth, token = int(row[0], 16), int(row[1], 16)
    allocated, paid = _bool(row[2]), _bool(row[3])
    if ((not allocated and (eth or token or paid)) or (phase < 2 and allocated) or
            (phase == 3 and not allocated) or (paid and phase != 3) or
            (shares == 0 and (eth or token)) or (status == 5 and phase == 0) or
            (phase >= 2 and shares != 0 and status != 5)):
        raise ProjectionError('Inconsistent NFT principal-return accounting')
    ready = phase == 3
    remaining = (0, 0) if paid else (eth, token)
    if ready:
        raw = p._call(p.contracts['principal_exit'].address, 'claimablePrincipal(uint256)', identifier,
                      block=block, words=2)
        if tuple(int(x, 16) for x in raw) != remaining:
            raise ProjectionError('Principal claim view differs from the allocation ledger')
    return {'available': True, 'phase': PHASES[phase], 'phase_code': phase,
            'allocated': allocated, 'paid': paid, 'beneficiary': owner,
            'holder_claim_available_by_lifecycle': ready and not paid and bool(eth or token),
            'automatic_payout_available_by_lifecycle': ready and not paid and bool(eth or token),
            'assets': [dict(asset=asset, symbol=p.assets[asset].symbol, decimals=p.assets[asset].decimals,
                            allocated_raw=str(amount) if allocated else None,
                            remaining_raw=str(owed) if allocated else None,
                            claimable_raw=str(owed) if ready else None)
                       for asset, amount, owed in ((ZERO, eth, remaining[0]), (zzz, token, remaining[1]))],
            'scope': 'Principal returned by the governance-triggered collective exit. '
                     'Separate from LP fees, royalties, earnings and reward claims. '
                     'Unpaid rights follow current NFT ownership; payout success is not guaranteed by a read.'}
