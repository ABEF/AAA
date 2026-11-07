from pathlib import Path
import hashlib,json,posixpath,re,subprocess,time,uuid,tomllib
R=Path.cwd();E=Path(__file__).resolve().parent;D=E/('abi-all-'+uuid.uuid4().hex[:10]);D.mkdir()
settings=tomllib.loads((R/'foundry.toml').read_text())['profile']['default']
remaps=sorted((s.split('=',1) for s in settings['remappings']),key=lambda x:len(x[0]),reverse=True)
pattern=re.compile(r'''\bimport\s+(?:\{[^}]*\}\s*from\s*|(?:\*\s*as\s+\w+|\w+)\s*from\s*)?["']([^"']+)["']\s*;''',re.S)
sources={};hashes={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def collect(name):
 if name in sources:return
 p=(R/name).resolve();assert p.is_relative_to(R.resolve())
 sources[name]={'content':p.read_text(encoding='utf-8-sig')};hashes[name]=sha(p)
 for target in pattern.findall(sources[name]['content']):
  if target.startswith('.'):resolved=posixpath.normpath(posixpath.join(posixpath.dirname(name),target))
  else:
   prefix,destination=next((a,b) for a,b in remaps if target.startswith(a));resolved=destination+target[len(prefix):]
  collect(resolved)
for folder in ('src','test','script'):
 for p in sorted((R/folder).rglob('*.sol')):collect(p.relative_to(R).as_posix())
payload={'language':'Solidity','sources':sources,'settings':{'evmVersion':'cancun','viaIR':True,
 'optimizer':{'enabled':True,'runs':1,'details':{'yul':False}},'remappings':settings['remappings'],
 'outputSelection':{'*':{'*':['abi']}}}}
with (D/'input.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(payload,f,separators=(',',':'))
solc=E.parent/'toolchain-0.8.26/solc.exe';t=time.monotonic()
with (D/'input.json').open('rb') as stdin,(D/'output.json').open('xb') as out,(D/'stderr.txt').open('xb') as err:
 result=subprocess.run([str(solc),'--standard-json'],cwd=R,stdin=stdin,stdout=out,stderr=err,timeout=120)
body=json.loads((D/'output.json').read_text());errors=[x['formattedMessage'] for x in body.get('errors',[]) if x.get('severity')=='error']
status={'scope':'Whole tracked-source/test/script ABI type closure only; no runtime/EVM/deployment',
 'successful':result.returncode==0 and not errors,'source_count':len(hashes),'source_sha256':hashes,
 'source_unchanged':all(sha(R/n)==h for n,h in hashes.items()),'elapsed':time.monotonic()-t,'errors':errors}
with (D/'status.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(status,f,indent=2);f.write('\n')
print(json.dumps({'directory':str(D),'successful':status['successful'],'source_unchanged':status['source_unchanged'],'sources':len(hashes),'errors':len(errors)}))
for e in errors[:12]:print(e)
raise SystemExit(0 if status['successful'] and status['source_unchanged'] else 1)
