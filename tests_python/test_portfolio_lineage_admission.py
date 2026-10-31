"""Fresh same-chain lineage admission; no RPC, database or signing is performed."""
import copy
import unittest

from frontend_api.lineage import SHARED_DEPENDENCY_ROLES
from frontend_api.service import Projection
from tests_python.test_frontend_api import addr
from tests_python.test_protocol_policy_v6 import fresh6_verifier


def configuration(version):
    rpc, _projection, _activation, _policy, current, _raw = fresh6_verifier()
    current = copy.deepcopy(current)
    if version == 5:
        current['accounting_version'] = 5
        current.pop('protocol_policy_version')
        current['contracts'].pop('protocol_policy')
    current['deployment_block'] = 20
    def history(config, label):
        return dict(database='var/unused-lineage-'+label+'.sqlite', start_block=1,
            start_parent_hash='0x'+'1'*64, max_events=100,
            contracts=[config['contracts'][role]['address'] for role in ('nft', 'rewards', 'royalties')])
    current['history'] = history(current, 'current')
    previous = copy.deepcopy(current)
    previous['deployment_block'] = 10
    for role, contract in previous['contracts'].items():
        if role not in SHARED_DEPENDENCY_ROLES:
            contract['address'] = addr(int(contract['address'], 16)+10000)
    previous['history'] = history(previous, 'previous')
    current['predecessors'] = [dict({key: previous[key] for key in
        ('accounting_version','deployment_block','deployment_block_hash','contracts','assets','history')},
        retirement_transaction_hash='0x'+'2'*64)]
    return current, rpc


class PortfolioLineageAdmissionTests(unittest.TestCase):
    def test_fresh5_and6_reuse_pinned_external_dependencies_without_reusing_protocol(self):
        for version in (5, 6):
            config, rpc = configuration(version)
            with self.subTest(version=version):
                p = Projection(config, rpc, clock=lambda: 1000)
                self.assertEqual(1, len(p.lineage.entries))
                old = p.lineage.entries[0].projection
                for role in SHARED_DEPENDENCY_ROLES:
                    self.assertEqual(p.contracts[role], old.contracts[role])
                self.assertNotEqual(p.contracts['vault'].address, old.contracts['vault'].address)

    def test_protocol_reuse_cross_role_collision_and_dependency_pin_change_are_rejected(self):
        for fault in ('protocol_reuse','cross_role','runtime_change'):
            config, rpc = configuration(6)
            previous = config['predecessors'][0]['contracts']
            if fault == 'protocol_reuse':
                previous['vault'] = copy.deepcopy(config['contracts']['vault'])
            elif fault == 'cross_role':
                previous['pool_manager'] = copy.deepcopy(config['contracts']['state_view'])
                previous['state_view']['address'] = addr(55555)
            else:
                previous['pool_manager']['code_hash'] = '0x'+'f'*64
            with self.subTest(fault=fault), self.assertRaisesRegex(ValueError,'conflicting deployment'):
                Projection(config, rpc, clock=lambda: 1000)


if __name__ == '__main__':
    unittest.main()
