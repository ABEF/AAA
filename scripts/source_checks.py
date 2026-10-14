"""Narrow source consistency checks. NOT a Solidity parser/compiler or security analyzer."""
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXPECTED=['ZZZVault','ZZZNFT','ZZZLiquidityManager','ZZZRewards','ZZZPower','ZZZFeeController','ZZZStrategy',
'ZZZCompounder','ZZZBuyback','ZZZMigration','ZZZBridgeAdapter','ZZZMigrationReceiver','ZZZAccessController',
'ZZZOracle','ZZZPoolRegistry','ZZZMigrationRegistry','ZZZBridgeRouter']
def sanitized(text):
    return re.sub(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
        lambda m:'\n'*m.group(0).count('\n')+' '*len(m.group(0)),text)
def main():
    errors=[];external=set();inventory=[]
    for name in EXPECTED:
        p=ROOT/'src'/f'{name}.sol'
        if not p.exists():errors.append(f'Missing required module {name}')
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
        inventory.append({'file':str(p.relative_to(ROOT)),'lines':len(text.splitlines())})
    report={'kind':'source_consistency_only','solidity_compiled':False,'security_audit_pass':False,
      'modules':len(EXPECTED),'source_files':inventory,'external_imports':sorted(external),'errors':errors,
      'limitations':['Balanced delimiters do not prove valid Solidity','No type checking, EVM execution or exploit analysis']}
    (ROOT/'reports').mkdir(exist_ok=True)
    (ROOT/'reports/source-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'source_files':len(sources),'errors':errors,'scope':'consistency only'}))
    return bool(errors)
if __name__=='__main__':sys.exit(main())
