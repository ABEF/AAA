"""Synthetic schema9/direct Entry3 fixtures; no actual deployment evidence."""
import copy
from tests_python import production_v6_fixtures as H
from zzz_ops import production_v7 as P
NOW,COMMIT,RUNTIME=H.NOW,H.COMMIT,H.RUNTIME


def refresh_bindings(cfg):
    chain=cfg['chains'][0]
    for row in chain['portfolio']['observed']['pools']:
        row['control_fingerprint']=P.H.portfolio_control_fingerprint(chain,row)
    for group,records in P.expected_bindings(chain).items():
        for role,values in records.items():
            chain[group][role]['observed_bindings']=copy.deepcopy(values)
            if group=='helpers':chain[group][role]['bindings']=copy.deepcopy(values)


def fixture():
    cfg=H.fixture();cfg.update(P.VERSIONS);chain=cfg['chains'][0]
    del chain['helpers']['entry_v4_executor']
    for role,profile in P.SERVICE_PROFILES.items():
        chain['services'][role]['profile']=profile;chain['services'][role]['evidence']['profile']=profile
    refresh_bindings(cfg)
    return cfg


class RPC(H.RPC):
    def __init__(self,cfg):
        super().__init__(cfg);self.expected=P.expected_bindings(self.chain)
