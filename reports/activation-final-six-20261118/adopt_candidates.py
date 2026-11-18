"""Explicit reviewed source adoption; never touches an installed environment."""
from pathlib import Path
import hashlib,json

R=Path(__file__).resolve().parents[2]
V=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
O=V/'activation-final-six-20261118'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
baseline=json.loads((O/'baseline/MANIFEST.json').read_bytes())
rows={
 'src/ZZZOracle.sol':('oracle/normal02/ZZZOracle.candidate.sol','56b232b0b07a020e2e509f3d837495d57f73d6e72025053a7391211f44f6715e'),
 'src/libraries/ExactLPAllocation.sol':('carry-sentinel/proposed/ExactLPAllocation.sol','c61df39ae2bc2fa3af8126c9684c5842d14d5b385d8f9f6ae33a63eaca73a031'),
 'src/ZZZRoyaltyRewards.sol':('royalty-final10/src/ZZZRoyaltyRewards.sol','69c1933e166ac014580fc8b915d884e03b0922cfc164a49abf379da3b37e60cf'),
 'src/libraries/ExactRoyaltyAllocation.sol':('royalty-final10/src/libraries/ExactRoyaltyAllocation.sol','911d84afc1993168ae0a512175adba41158f2209a5e63d7b5085aca4c04988a9'),
 'src/ZZZContributionPricing.sol':('pricing-basis01/ZZZContributionPricing.candidate.sol','971a967c6d63951ea873889a8b9e2b221578f8dc21549884fbc27fac6d738707'),
 'src/ZZZV4SpotPriceFeed.sol':('feed-identity01/ZZZV4SpotPriceFeed.candidate.sol','e098d2c9c6b1f996fc0da69e602c0bc49e6b0d985eb25a7c0e24220e87a1031c'),
}
for name,(candidate,pin) in rows.items():
    assert sha((R/name).read_bytes())==baseline['sha256'][name],name
    assert sha((O/candidate).read_bytes())==pin,candidate
protected={
 'reports/source-checks.json':'049dca6943d06ba63de682dc8cdec2cf3935af1dc2e5479e9f3cf14e1af793c4',
 'scripts/run-fork-checks.py':'875d27fb56963d92e6e7ec25b9f296b5559b830e007ad411afb856f0f0226f1b',
 'tests_python/test_fork_runner.py':'6d50a612ec490ec0f3754d930ac6610173d96d0a684bbc5e4894eaedf4d9abc9',
 'tests_python/test_frontend_history.py':'361f6a56153a4b3041b5b6f7eaaf399fea063bae9f46299da71397a08540c7eb'}
assert all(sha((R/name).read_bytes())==pin for name,pin in protected.items())
record={'schema':1,'baseline_head':baseline['head'],'adopted_sources':{},'public_deployment_or_existing_state_change':False,'production_approved':False}
for name,(candidate,pin) in rows.items():
    (R/name).write_bytes((O/candidate).read_bytes())
    record['adopted_sources'][name]={'baseline_sha256':baseline['sha256'][name],'candidate_path':candidate,'adopted_sha256':pin}
normal=V/'activation-gas-20261118/build/final01'
freeze={'schema':1,'source_sha256':{p.relative_to(R).as_posix():sha(p.read_bytes())for p in(R/'src').rglob('*.sol')},
 'protected_sha256':protected,'foundry_toml_sha256':sha((R/'foundry.toml').read_bytes()),
 'fixture_sha256':sha((R/'test/RoyaltyRoundsCapacity20261118.t.sol').read_bytes()),
 'normal_build':{'build_id':'activation-final-six-20261118','baseline_input_sha256':sha((normal/'compiler-input.json').read_bytes()),
 'baseline_output_sha256':sha((normal/'compiler-output.json').read_bytes()),'approved_changed_source_sha256':{name:pin for name,(_,pin)in rows.items()}}}
assert len(freeze['source_sha256'])==61
for path,value in ((O/'ADOPTION.json',record),(O/'SOURCE_FREEZE.json',freeze)):
    with path.open('x',encoding='utf-8',newline='\n')as f:json.dump(value,f,indent=2);f.write('\n')
print('Adopted six exact reviewed source candidates; fresh closed normal verification remains required.')
