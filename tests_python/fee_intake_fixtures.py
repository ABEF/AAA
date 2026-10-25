"""Synthetic LP-only inventory conversion; never actual release evidence."""
import copy

from zzz_ops import production_v2 as P


def lp_only_fixture(config):
    config = copy.deepcopy(config)
    config['fee_intake_version'] = 1
    chain = config['chains'][0]
    factory = chain['helpers'].pop('reward_receiver_factory', None)
    if factory is not None:
        # Synthetic runtime/evidence only; this fixture is not an actual deployment.
        factory['address'] = '0x' + format(1200,'040x')
        chain['helpers']['activation_assets_factory'] = factory
    chain['native_accounting']['canonical_schema'] = P.LP_ONLY_CANONICAL_SCHEMA
    bindings = P.expected_bindings(chain,
        range_policy_version=config.get('range_policy_version',0),fee_intake_version=1)
    for category, roles in bindings.items():
        for role, values in roles.items():
            chain[category][role]['observed_bindings'] = copy.deepcopy(values)
            if category == 'helpers':
                chain[category][role]['bindings'] = copy.deepcopy(values)
    return config
