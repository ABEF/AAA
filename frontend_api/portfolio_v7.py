"""Explicit accounting7 physical portfolio; never relabel accounting6 replies."""
from frontend_api.portfolio_v6 import ROLES
from frontend_api import portfolio_v6 as geometry


def verify_profile(p,block):
    geometry.verify_profile(p,block,accounting_version=7)
    if p._uint('rewards','LP_ALLOCATION_VERSION()',block=block)!=1:
        from frontend_api.service import ProjectionError
        raise ProjectionError('Accounting7 exact LP allocation capability differs')


def read_bucket(p,bucket,block):
    return geometry._read_bucket_proof(p,bucket,block,accounting_version=7)[0]


def contribution_context(p,*args,**kwargs):
    return geometry.contribution_context(p,*args,**kwargs,accounting_version=7)
