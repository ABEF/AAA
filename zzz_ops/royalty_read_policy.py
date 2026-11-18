"""Payload5/6 activation ERC20 balance-read policy; observations are caller-pinned.

The fingerprint below is computed OFFLINE, not an on-chain getter. Existing
gasPolicy/gasFingerprint keep their historical four-word ABI and semantics.
The cap isolates activation enrollment reads, not ordinary sync/claim/canonical
balance reads. Currency faults and wider workload qualification remain separate.
"""
from zzz_ops.abi import address, keccak256
from zzz_ops.protocol_policy import observe as observe_policy

VERSION=1
MIN_GAS=10000
MAX_GAS=1000000
DOMAIN=keccak256(b'ZZZ_ROYALTY_BALANCE_READ_POLICY_V1')
SCOPE='computed_offline_policy_cap_and_gas_revision_v1'
VALUE_FIELDS=frozenset(('version','policy','balance_gas','gas_revision','fingerprint','fingerprint_scope'))
FIELDS=VALUE_FIELDS|{'observed','review_evidence'}


def fingerprint(policy,balance_gas,gas_revision):
    target=address(policy)
    if type(balance_gas)is not int or not MIN_GAS<=balance_gas<=MAX_GAS:
        raise ValueError('Royalty balance-read gas exceeds approved bounds')
    if type(gas_revision)is not int or not 0<gas_revision<2**64:
        raise ValueError('Royalty balance-read gas revision differs')
    raw=DOMAIN+int(target,16).to_bytes(32,'big')+balance_gas.to_bytes(32,'big')+gas_revision.to_bytes(32,'big')
    return '0x'+keccak256(raw).hex()


def precheck(chain):
    section=chain.get('royalty_read_policy')
    if not isinstance(section,dict) or set(section)!=FIELDS:
        raise ValueError('Use exact payload5/6 royalty-read policy section')
    if type(section['version'])is not int or section['version']!=VERSION or section['fingerprint_scope']!=SCOPE:
        raise ValueError('Unsupported royalty balance-read policy profile')
    if section['policy'] is not None:address(section['policy'])
    if section['balance_gas'] is not None and (type(section['balance_gas'])is not int or
            not MIN_GAS<=section['balance_gas']<=MAX_GAS):
        raise ValueError('Royalty balance-read gas exceeds approved bounds')
    if section['gas_revision'] is not None and (type(section['gas_revision'])is not int or
            not 0<section['gas_revision']<2**64):
        raise ValueError('Royalty balance-read gas revision differs')
    return section


def observe(read,*,policy,access):
    """Reuse the authenticated OLD gas tuple, then read the separate uint32 cap."""
    gas=observe_policy(read,policy=policy,access=access,domain='gas')
    raw=read(address(policy),'royaltyBalanceGas()',count=1)
    if (not isinstance(raw,list) or len(raw)!=1 or not isinstance(raw[0],str) or len(raw[0])!=64 or
            any(c not in '0123456789abcdefABCDEF' for c in raw[0])):
        raise ValueError('Malformed royalty balance-read policy response')
    cap=int(raw[0],16);revision=gas['revision']
    return dict(version=VERSION,policy=address(policy),balance_gas=cap,gas_revision=revision,
        fingerprint=fingerprint(policy,cap,revision),fingerprint_scope=SCOPE)


def validate(g,chain,path):
    from zzz_ops import production_v2 as V
    section=precheck(chain);p=path+'.royalty_read_policy'
    target=V._obj(V._obj(chain.get('helpers')).get('protocol_policy')).get('address')
    g.check(section.get('version')==VERSION and type(section.get('version'))is int,p,'royalty.read.version',
        'Use the explicit payload5/6 bounded balance-read profile.','bindings')
    g.check(V._equal(section.get('policy'),target),p,'royalty.read.binding','Bind the actual protocol policy.','bindings')
    g.check(section.get('fingerprint_scope')==SCOPE,p,'royalty.read.fingerprint_scope',
        'This fingerprint is computed offline; it is not a contract getter.','bindings')
    try:expected=fingerprint(section['policy'],section['balance_gas'],section['gas_revision'])
    except (ValueError,TypeError,KeyError):expected=None
    g.check(expected is not None and section.get('fingerprint')==expected,p,'royalty.read.fingerprint',
        'Recompute the exact reviewed gas cap and gas revision.','bindings')
    revision=V._obj(V._obj(chain.get('protocol_policy')).get('gas')).get('revision')
    g.check(type(section.get('gas_revision'))is int and section.get('gas_revision')==revision,p,
        'royalty.read.revision','Match the independently reviewed gas-policy revision.','bindings')
    wanted={key:section[key] for key in VALUE_FIELDS}
    g.check(V._equal(section.get('observed'),wanted),p,'royalty.read.observation',
        'Compare all actual same-block balance-read policy observations.','bindings')
    V._bound_proof(g,section.get('review_evidence'),p+'.review_evidence',chain,
        kind='royalty_balance_read_qualification',exact_block=True)
