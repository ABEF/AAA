"""Reject incompatible fresh browser labs before filesystem/process/chain work.

Existing running legacy fixtures are not restarted or reconfigured here. Current
pricing-V2 core needs a separately reviewed native-V2 lab/configuration port.
"""
import json
from pathlib import Path
import re

from zzz_ops.abi import keccak256

ROOT = Path(__file__).resolve().parents[1]
MAX_ARTIFACT_BYTES = 8 * 1024 * 1024
UNSUPPORTED = ('This legacy browser-lab scaffold does not support current native/pricing V2. '
    'Fresh startup is blocked before state creation or Anvil execution. Preserve the existing '
    'running legacy fixture and its journals; a separately reviewed V2 fixture/configuration port is required.')


def _json(raw):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError('Duplicate local fixture artifact field')
            result[key]=value
        return result
    def constant(_value):raise ValueError('Nonfinite local fixture artifact value')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=constant)


def require_legacy_fixture_artifacts(artifacts):
    """Read only the explicitly named Oracle artifact and fixed repo source."""
    try:
        path=Path(artifacts)/'ZZZOracle.sol'/'ZZZOracle.json'
        with path.open('rb') as stream:raw=stream.read(MAX_ARTIFACT_BYTES+1)
        if len(raw)>MAX_ARTIFACT_BYTES:raise ValueError('Local fixture artifact exceeds bound')
        artifact=_json(raw)
        if not isinstance(artifact,dict):raise ValueError('Invalid local fixture artifact object')
        abi=artifact.get('abi')
        if not isinstance(abi,list) or len(abi)>512:raise ValueError('Invalid local fixture Oracle ABI')
        functions=[item for item in abi if isinstance(item,dict) and item.get('type')=='function']
        if any(item.get('name') in ('PRICING_VERSION','contributionPricing') for item in functions):
            raise RuntimeError(UNSUPPORTED)
        if not any(item.get('name')=='setFeed' and isinstance(item.get('inputs'),list) and
                [value.get('type') for value in item['inputs'] if isinstance(value,dict)]==['address','address','uint32']
                for item in functions):
            raise ValueError('Unsupported local fixture Oracle ABI')
        metadata=artifact.get('metadata')
        if not isinstance(metadata,dict):metadata=_json(artifact['rawMetadata'])
        expected=metadata['sources']['src/ZZZOracle.sol']['keccak256']
        if not isinstance(expected,str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}',expected):
            raise ValueError('Missing local fixture Oracle source pin')
        source=(ROOT/'src/ZZZOracle.sol').read_bytes()
        if '0x'+keccak256(source).hex()!=expected.lower():
            raise ValueError('Stale local fixture Oracle build; do not rebuild or restart an existing lab in place')
        if b'PRICING_VERSION' in source or b'contributionPricing' in source:
            raise RuntimeError(UNSUPPORTED)
        return 1
    except RuntimeError:
        raise
    except (OSError,UnicodeError,ValueError,KeyError,TypeError,RecursionError) as exc:
        raise ValueError('Missing, stale or incompatible local fixture Oracle artifact; fresh startup remains blocked') from exc
