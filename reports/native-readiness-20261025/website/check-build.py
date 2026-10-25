from pathlib import Path
import subprocess,json,hashlib
SITE=Path(r'C:/Users/Ali/Desktop/2.x holas/Oto/aaa-website');HERE=Path(__file__).parent
NODE=r'C:/Users/Ali/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before={p.relative_to(SITE/'dist').as_posix():digest(p) for p in (SITE/'dist').rglob('*') if p.is_file()}
syntax=['deployment-api.js','deployment-native.js','deployment-view.js','tests/deployment-native.test.mjs','tests/deployment-native-view.test.mjs','tests/helpers/deployment-native-fixture.mjs','build.mjs']
checks=[]
for name in syntax:
    r=subprocess.run([NODE,'--check',name],cwd=SITE,capture_output=True,text=True)
    checks.append({'file':name,'exit':r.returncode});assert r.returncode==0,r.stderr
r=subprocess.run([NODE,'check.mjs'],cwd=SITE,capture_output=True,text=True)
assert r.returncode==0,r.stderr
build=HERE/'isolated-build';build.mkdir(exist_ok=True)
code=(SITE/'build.mjs').read_text(encoding='utf-8')
code=code.replace("'./artworks.js'",repr((SITE/'artworks.js').as_uri()))
old='copyFile(new URL(name,import.meta.url),new URL(`dist/${name}`,import.meta.url))'
assert code.count(old)==1
code=code.replace(old,'copyFile(new URL(name,'+repr(SITE.as_uri()+'/')+'),new URL(`dist/${name}`,import.meta.url))')
(build/'build.mjs').write_text(code,encoding='utf-8')
assert (build/'dist').resolve().is_relative_to(HERE.resolve())
r2=subprocess.run([NODE,str(build/'build.mjs')],capture_output=True,text=True)
assert r2.returncode==0,r2.stderr
after={p.relative_to(SITE/'dist').as_posix():digest(p) for p in (SITE/'dist').rglob('*') if p.is_file()}
assert before==after,'Existing dist repair overlay must be preserved'
applied=json.loads((HERE/'applied-site.json').read_text())
assert all(digest(SITE/n)==h for n,h in applied['sha256'].items())
assert all(digest(SITE/n)==h for n,h in applied['preserved_sha256'].items())
record={'syntax':checks,'asset_check':r.stdout.strip(),'isolated_build':r2.stdout.strip(),
 'source_sha256':applied['sha256'],'protected_sha256':applied['preserved_sha256'],
 'site_dist_files_preserved':len(before),'site_dist_manifest_sha256':hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),
 'build_files':len([p for p in (build/'dist').rglob('*') if p.is_file()]),'public_deployment':None,'services_changed':False}
(HERE/'build-result.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record))
