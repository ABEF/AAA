"""Read-only reveal/drain status, not approval to replace contracts or move LP."""
from frontend_api.service import ProjectionError, _bool


def inspect(projection):
    p = projection
    header, head, block = p._snapshot()
    lifecycle = p._verify_deployment(block, allow_locked=True)
    if lifecycle['state_code'] in (2, 4):
        raise ProjectionError('Importing/cancelled NFT inventory is not canonical readiness')
    nft = p.contracts['nft'].address
    minted = p._uint('nft', 'mintedCount()', block=block)
    next_ordinal = p._uint('nft', 'nextToFinalize()', block=block)
    remaining = p._uint('nft', 'remainingToReveal()', block=block)
    if not 0 <= minted <= 1000 or not 1 <= next_ordinal <= minted+1 or remaining != 1001-next_ordinal:
        raise ProjectionError('Inconsistent reveal inventory')
    quotas = [p._uint('nft', 'rarityRemaining(uint256)', i, block=block) for i in range(3)]
    if sum(quotas) != remaining or any(n > cap for n, cap in zip(quotas, (600, 300, 100))):
        raise ProjectionError('Inconsistent remaining rarity quotas')
    configured = _bool(p._call(nft, 'randomnessConfigured()', block=block)[0])
    if not configured:
        raise ProjectionError('Sealed NFT randomness is not configured')
    coordinator = p._addr('nft', 'randomnessCoordinator()', block=block)
    pending = minted-next_ordinal+1
    oldest = None
    if pending:
        identifier = p._uint('nft', 'tokenAtOrdinal(uint256)', next_ordinal, block=block)
        if (p._uint('nft', 'mintOrdinalOf(uint256)', identifier, block=block) != next_ordinal or
                _bool(p._call(nft, 'traitsReady(uint256)', identifier, block=block)[0])):
            raise ProjectionError('Pending ordinal identity is inconsistent')
        request_id = p._uint('nft', 'requestOf(uint256)', identifier, block=block)
        epoch = p._uint('nft', 'requestEpochOf(uint256)', identifier, block=block)
        record = p._call(nft, 'canonicalRandomness(uint256)', identifier, block=block, words=5)
        if int(record[0], 16) != identifier or not _bool(record[3]) or request_id == 0:
            raise ProjectionError('Pending randomness provenance is inconsistent')
        fulfilled = _bool(record[4])
        oldest = {'token_id': str(identifier), 'mint_ordinal': next_ordinal,
                  'request_id': str(request_id), 'request_epoch': str(epoch),
                  'state': 'awaiting_finalization' if fulfilled else 'awaiting_randomness'}
    p._finish(header)
    return {'schema': 2, 'chain_id': p.chain, 'lifecycle': lifecycle,
            'nft': nft, 'coordinator': coordinator, 'minted': minted,
            'revealed': next_ordinal-1, 'unfinished_draws': pending, 'oldest_unfinished': oldest,
            'new_minting_stopped_by_lifecycle': not lifecycle['new_economic_work_available_by_lifecycle'],
            'collection_replacement_reveal_condition_met': pending == 0,
            'other_handoff_requirements_verified': False,
            'provider_funding_verified': False, 'provider_liveness_verified': False,
            'pending_since': None,
            'scope': 'Unfinished draws include fulfilled requests awaiting ordered finalization. '
                     'A single snapshot does not measure delay or qualify provider funding. '
                     'This reveal gate applies to collection-contract replacement, not ordinary LP pool migration.',
            'provenance': {'block_number': header['number'], 'block_hash': header['hash'],
                           'block_timestamp': header['timestamp'], 'observed_head': head,
                           'configuration_sha256': p.identity}}
