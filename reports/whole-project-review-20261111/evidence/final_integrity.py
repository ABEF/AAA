from pathlib import Path
import gzip,hashlib,json,re,subprocess,tarfile,urllib.parse
R=Path.cwd();W=R.parents[1]/'aaa-website';E=Path(__file__).resolve().parent;D=R/'reports/whole-project-review-20261111'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
start=json.loads((E/'START.json').read_text(encoding='utf-8'))
protected={n:sha(R/n)==h for n,h in start['protected_sha256'].items()}
original_report={n:sha(R/n)==h for n,h in start['archived_sha256'].items() if n.startswith('reports/composite-spot-price-20261109/')}
compiler=json.loads((E/'contracts/normal-final-ea7e55d22b/compiler-input.json').read_text(encoding='utf-8'))
source={n:sha(R/n)==hashlib.sha256(v['content'].encode()).hexdigest() for n,v in compiler['sources'].items() if n.startswith('src/')}
manifest=json.loads((D/'evidence/manifest.json').read_text(encoding='utf-8'));evidence=[]
for x in manifest['files']:
 p=D/x['published'];ok=sha(p)==x['stored_sha256']
 if x.get('sha256'):
  raw=gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes()
  ok &= hashlib.sha256(raw).hexdigest()==x['sha256']
 if x.get('source_snapshot'):
  with tarfile.open(p,'r:gz') as t:ok &= len(t.getmembers())>0
 evidence.append(ok)
changed=subprocess.check_output(['git','diff','--name-only','--','*.md'],text=True,cwd=R).splitlines()
changed += ['docs/POOL_SPOT_PRICE_SOURCE.md','reports/whole-project-review-20261111/REVIEW.md','reports/whole-project-review-20261111/VERIFICATION.md']
links=[];link_errors=[]
for n in changed:
 p=R/n;text=p.read_text(encoding='utf-8')
 text=re.sub(r'```[\s\S]*?```','',text)
 for m in re.finditer(r'\]\((<?[^\s)]+>?)(?:\s+"[^"]*")?\)',text):
  raw=m[1].strip('<>')
  if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',raw) or raw.startswith('#'):continue
  target=urllib.parse.unquote(raw.split('#')[0].split('?')[0])
  if not target:continue
  dest=(p.parent/target).resolve();links.append({'file':n,'target':raw})
  if not dest.exists():link_errors.append(links[-1])
signer=sha(W/'browser-wallet.js')
public_configs={n:(W/n).read_text(encoding='utf-8') for n in ('deployment-config.js','integration-config.js')}
null_configs={n:bool(re.search(r'(?:DEPLOYMENT|INTEGRATION_DEPLOYMENT)\s*=\s*null',text)) for n,text in public_configs.items()}
# Inspect changed source/evidence for credential literals; do not print matches.
names=subprocess.check_output(['git','diff','--name-only'],text=True,cwd=R).splitlines()
files=[R/n for n in names if n not in start['protected_sha256']]
files += [p for p in D.rglob('*') if p.is_file() and p.suffix not in {'.gz'}]
files += [R/'src/ZZZV4SpotPriceFeed.sol',R/'test/PoolSpotPriceFeed.t.sol',R/'docs/POOL_SPOT_PRICE_SOURCE.md']
secret_patterns=[r'-----BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY-----',r'(?i)(?:PRIVATE_KEY|PASSWORD|API_SECRET)\s*[=:]\s*[\x22\x27]?(?:0x)?[a-zA-Z0-9+/]{32,}',r'https?://[^/\s]+:[^/\s]+@']
secret_files=[]
for p in files:
 if not p.is_file():continue
 raw=p.read_text(encoding='utf-8',errors='replace')
 if any(re.search(x,raw) for x in secret_patterns):secret_files.append(p.relative_to(R).as_posix())
record={'protected_files_unchanged':protected,'prior_report_files_unchanged':original_report,'normal_project_sources_current':source,'evidence_files':len(evidence),'all_evidence_hashes_current':all(evidence),'local_link_count':len(links),'missing_local_link_targets':link_errors,'link_scope':'Changed current Markdown plus new review/reference, local file existence only; external links and dynamic GitHub anchor rendering are not verified.','shared_signer_sha256':signer,'shared_signer_unchanged':signer=='c8d9b9a96fb815be497e914e7f3054f3cd39bade73870396e36199495f07b106','public_config_null':null_configs,'possible_secret_literal_files':secret_files,'git_branch':subprocess.check_output(['git','branch','--show-current'],text=True,cwd=R).strip()}
(E/'final-integrity.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
summary={'protected':all(protected.values()),'prior_report':all(original_report.values()),'normal_sources':all(source.values()),'evidence':all(evidence),'link_count':len(links),'missing_links':link_errors,'signer_unchanged':record['shared_signer_unchanged'],'public_null':all(null_configs.values()),'secret_candidate_files':secret_files,'branch':record['git_branch']}
print(json.dumps(summary))
assert all(protected.values()) and all(original_report.values()) and all(source.values()) and all(evidence) and record['shared_signer_unchanged'] and all(null_configs.values())
assert not link_errors,link_errors
