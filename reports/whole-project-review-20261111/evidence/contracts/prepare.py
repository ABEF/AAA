from pathlib import Path
import hashlib,json,shutil
R=Path.cwd();V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9');E=Path(__file__).resolve().parent
original=E/'originals';original.mkdir()
files=['src/ZZZContributionPricing.sol','src/ZZZMembership.sol','src/ZZZMigrationBudget.sol','src/ZZZNFTMetadata.sol','src/base/ZZZRewardConverter.sol','src/ZZZLPRewardConverter.sol','test/NativeCustody.t.sol']
for name in files:
 dest=original/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/name,dest)
src=V/'composite-price-20261109-0acb123/run-spot-tests.py'
text=src.read_text().replace("B=V/'composite-price-20261109-0acb123'","B=Path(__file__).resolve().parent")
text=text.replace("add(R/'test/PoolSpotPriceFeed.t.sol')","for file in json.loads(sys.argv[1]):add(R/file)")
text=text.replace("'--match-contract','PoolSpotPriceFeedTest'","'--match-contract',sys.argv[2]")
text=text.replace("if len(sys.argv)>1:command+=['--match-test',sys.argv[1]]","if len(sys.argv)>3:command+=['--match-test',sys.argv[3]]")
text=text.replace("'only new adapter tests; no RPC/deployment or existing Anvil'","'focused changed contract paths; synthetic fixtures, no RPC/deployment/existing Anvil'")
(E/'run-tests.py').write_text(text,encoding='utf-8')
builder=(V/'composite-price-20261109-0acb123/build-closed.py').read_text()
(E/'build-closed.py').write_text(builder,encoding='utf-8')
(E/'START.json').write_text(json.dumps({'originals':{name:hashlib.sha256((R/name).read_bytes()).hexdigest() for name in files}},indent=2)+'\n')
print('Archived seven owned files and prepared isolated focused/normal builders.')
