"""Narrow source consistency checks. NOT a Solidity parser/compiler or security analyzer."""
import argparse,datetime,json,re,secrets,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from zzz_ops.evidence import Evidence
EXPECTED=['ZZZVault','ZZZNFT','ZZZLiquidityManager','ZZZRewards','ZZZMembership','ZZZFeeController','ZZZStrategy',
'ZZZCompounder','ZZZBuyback','ZZZMigration','ZZZAccessController',
'ZZZOracle','ZZZPoolRegistry',
'ZZZCanonicalHandoff','ZZZNFTCanonical','ZZZVaultCanonical','ZZZFeesCanonical']
HELPERS=['ZZZRoyaltyRewards','ZZZNFTMetadata','ZZZClaimRouter','ZZZActivationAssets','ZZZActivationEntry',
'ZZZMigrationBudget','ZZZCustodyValidation','ZZZRoyaltyFactory','ZZZActivationAssetsFactory','ZZZRoyaltyConverter','ZZZLPRewardConverter',
'ZZZV4RouteExecutor','ZZZContributionPricing','ZZZLPBalancer']
def sanitized(text):
    return re.sub(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
        lambda m:'\n'*m.group(0).count('\n')+' '*len(m.group(0)),text)
def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args(argv)
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')
    output=args.output or ROOT/'reports'/f'source-checks-{stamp}-{secrets.token_hex(4)}.json'
    with Evidence(output,kind='source_consistency_only') as evidence:
        errors=[];external=set();inventory=[]
        for name in EXPECTED+HELPERS:
            p=ROOT/'src'/f'{name}.sol'
            if not p.exists():errors.append(f'Missing required contract {name}')
        sources=sorted((ROOT/'src').rglob('*.sol'))
        for p in sources:
            text=p.read_text();clean=sanitized(text);stack=[];pairs={')':'(',']':'[','}':'{'}
            if 'pragma solidity 0.8.26;' not in text:errors.append(f'{p.name}: unpinned pragma')
            for c in clean:
                if c in '([{':stack.append(c)
                elif c in pairs:
                    if not stack or stack.pop()!=pairs[c]:errors.append(f'{p.name}: delimiter mismatch');break
            if stack:errors.append(f'{p.name}: unmatched delimiter')
            if re.search(r'\b(?:delegatecall|selfdestruct)\b|tx\.origin',clean):errors.append(f'{p.name}: dangerous primitive requires review')
            for target in re.findall(r'\bimport\s+(?:[\s\S]*?\bfrom\s+)?["\']([^"\']+)["\']\s*;',text):
                if target.startswith('.'):
                    if not (p.parent/target).resolve().is_file():errors.append(f'{p.name}: missing local import {target}')
                else:external.add(target)
            inventory.append({'file':p.relative_to(ROOT).as_posix(),'lines':len(text.splitlines())})
        report={'kind':'source_consistency_only','solidity_compiled':False,'security_audit_pass':False,'successful':not errors,
      'modules':len(EXPECTED),'standalone_helpers':HELPERS,'source_files':inventory,'external_imports':sorted(external),'errors':errors,
      'limitations':['Balanced delimiters do not prove valid Solidity','No type checking, EVM execution or exploit analysis']}
        evidence.finish(report)
    print(json.dumps({'source_files':len(sources),'errors':errors,'scope':'consistency only','output':str(output)}))
    return bool(errors)
if __name__=='__main__':sys.exit(main())
