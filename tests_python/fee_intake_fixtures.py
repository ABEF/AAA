"""Synthetic LP-only inventory conversion; never actual release evidence."""
import copy

from zzz_ops import production_v2 as P


def lp_only_fixture(config):
    config = copy.deepcopy(config)
    config['fee_intake_version'] = 1
    config['accounting_version'] = 3
    chain = config['chains'][0]
    chain['native_accounting']['version'] = 3
    factory = chain['helpers'].pop('reward_receiver_factory', None)
    if factory is not None:
        # Synthetic runtime/evidence only; this fixture is not an actual deployment.
        factory['address'] = '0x' + format(1200,'040x')
        chain['helpers']['activation_assets_factory'] = factory
    chain['native_accounting']['canonical_schema'] = P.LP_ONLY_CANONICAL_SCHEMA
    governance = chain['governance']
    for field in ('proposers','executors','timelock_seconds'):
        governance.pop(field,None)
    governance['observed_roles'] = {'governance':governance['multisig'],'pending_governance':P.ZERO,
        'keeper':governance['keeper'],'keeper_enabled':True,'guardian':governance['guardian'],'guardian_enabled':True}
    governance['review_evidence']['configuration_sha256'] = P.configuration_hash(P.governance_configuration(chain))
    for role,profile in (('keeper','local_position_v3_governed_limits'),
            ('api','accounting_v3_routing_v2_pricing_v2_review_v1')):
        chain['services'][role]['profile'] = profile
        chain['services'][role]['evidence']['profile'] = profile
    bindings = P.expected_bindings(chain,
        range_policy_version=config.get('range_policy_version',0),fee_intake_version=1)
    for category, roles in bindings.items():
        for role, values in roles.items():
            chain[category][role]['observed_bindings'] = copy.deepcopy(values)
            if category == 'helpers':
                chain[category][role]['bindings'] = copy.deepcopy(values)
    return config
