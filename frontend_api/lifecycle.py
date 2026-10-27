"""Read the pinned same-chain handoff ABI; never discover or trust peer code."""
from __future__ import annotations

from zzz_ops.abi import keccak256

STATES = ('operating', 'frozen', 'importing', 'retired', 'cancelled')
PHASES = ('idle', 'exporting', 'imported', 'retired', 'importing',
          'active_replacement', 'aborting', 'cancelled', 'settling')
VALID_PHASES = ({0, 5}, {1, 6, 8}, {2, 4}, {3}, {7})


def read_lifecycle(p, block):
    # Imported here to avoid an import cycle with Projection's boundary helpers.
    from frontend_api.service import ProjectionError, ZERO, _bool

    access = p.contracts['access'].address
    for role, label in (('handoff', 'ZZZCanonicalHandoff'), ('vault_canonical', 'ZZZVaultCanonical')):
        module_id = '0x' + keccak256(label.encode()).hex()
        if (p._addr('access', 'module(bytes32)', module_id, block=block) != p.contracts[role].address or
                p._addr(role, 'access()', block=block) != access):
            raise ProjectionError('Canonical module differs from sealed deployment pins')
    if (p._addr('access', 'canonicalHandoff()', block=block) != p.contracts['handoff'].address or
            p._addr('vault', 'canonicalModule()', block=block) != p.contracts['vault_canonical'].address or
            p._addr('vault_canonical', 'vault()', block=block) != p.contracts['vault'].address):
        raise ProjectionError('Canonical helper owner/binding mismatch')

    state = p._uint('access', 'canonicalState()', block=block)
    phase = p._uint('handoff', 'phase()', block=block)
    if state >= len(STATES) or phase not in VALID_PHASES[state]:
        raise ProjectionError('Unknown or inconsistent canonical lifecycle')
    preparation = _bool(p._call(access, 'preparationActive()', block=block)[0])
    paused = _bool(p._call(access, 'paused()', block=block)[0])
    settling = _bool(p._call(access, 'canonicalSettling()', block=block)[0])
    # This flag is temporary within a settlement transaction, never a valid
    # externally observable end-of-block state in the pinned implementation.
    if settling or state in (1, 3) and not preparation or state in (2, 4) and preparation:
        raise ProjectionError('Inconsistent canonical preparation/settlement state')

    source = p._addr('handoff', 'incomingSource()', block=block, native=True)
    destination = p._addr('handoff', 'destinationController()', block=block, native=True)
    origin_chain = p._uint('vault_canonical', 'originChain()', block=block)
    origin_vault = p._addr('vault_canonical', 'originVault()', block=block)
    if (source == access or destination == access or
            phase == 0 and source != ZERO or phase in (2, 4, 5, 7) and source == ZERO or
            state in (1, 3) and destination == ZERO or origin_chain != p.chain):
        raise ProjectionError('Inconsistent same-chain handoff lineage')
    if source == ZERO and origin_vault != p.contracts['vault'].address:
        raise ProjectionError('Original deployment has unexpected identity origin')

    operating = state == 0
    lp_exit = False
    lp_phase = 0
    if p.accounting_version == 4:
        lp_exit = _bool(p._call(access, 'lpExitStarted()', block=block)[0])
        lp_phase = p._uint('principal_exit', 'exitPhase()', block=block)
        if lp_phase > 3 or lp_exit != bool(lp_phase):
            raise ProjectionError('Collective exit phase differs from its irreversible lock')
        if lp_exit and (not operating or preparation):
            raise ProjectionError('Collective LP exit conflicts with canonical handoff')
    result = {
        'state': STATES[state], 'state_code': state,
        'handoff_phase': PHASES[phase], 'preparation_active': preparation, 'paused': paused,
        # An inert importer initially holds its constructor's own identity,
        # then receives the predecessor header. Do not present either partial
        # or cancelled import state as the activated collection's origin.
        'origin': {'chain_id': origin_chain, 'vault': origin_vault} if state not in (2, 4) else None,
        'origin_available': state not in (2, 4),
        'predecessor_controller': None if source == ZERO else source,
        # A cancelled handoff retains destinationController on the restored
        # source. Never advertise that stale proposal as an active successor.
        'successor_controller': destination if state == 3 else None,
        'handoff_destination_controller': destination if state in (1, 3) else None,
        'peer_deployments_verified': False,
        'claims_available_by_lifecycle': operating,
        'transfers_available_by_lifecycle': operating,
        'new_economic_work_available_by_lifecycle': operating and not preparation and not paused and not lp_exit,
        'scope': 'Confirmed same-chain lifecycle only. Flags are lifecycle permissions, not execution guarantees. '
                 'Peer addresses are source commitments; no peer code or cross-chain finality is verified.',
    }
    if p.accounting_version == 4:
        result['lp_exit_started'] = lp_exit
        result['lp_exit_phase_code'] = lp_phase
        result['lp_exit_phase'] = ('operating', 'closing', 'allocating', 'ready')[lp_phase]
    return result
