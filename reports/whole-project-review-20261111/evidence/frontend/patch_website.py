from pathlib import Path
import datetime,hashlib,json,subprocess,sys
W=Path('C:/Users/Ali/Desktop/2.x holas/Oto/aaa-website')
E=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,text):
 old=p.read_bytes() if p.exists() else b''
 p.write_bytes(text.replace('\r\n','\n').replace('\n','\r\n' if b'\r\n' in old else '\n').encode('utf-8'))
mode=sys.argv[1]
if mode=='prepare':
 status=subprocess.check_output(['git','-c','safe.directory='+str(W),'-C',str(W),'status','--porcelain'],text=True)
 assert not status.strip(),status
 originals=E/'originals';originals.mkdir(exist_ok=True)
 names=['build.mjs','server.mjs','package.json','browser-wallet.js','deployment-config.js','integration-config.js']
 record={'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'head':subprocess.check_output(['git','-c','safe.directory='+str(W),'-C',str(W),'rev-parse','HEAD'],text=True).strip(),
  'original':{n:sha(W/n) for n in names},'git_clean':True,'no_build_service_rollout':True}
 for n in names:(originals/n).write_bytes((W/n).read_bytes())
 (E/'START.json').write_text(json.dumps(record,indent=2)+'\n')
 test=(E/'deployment-bundle.test.mjs').read_text()
 target=W/'tests/deployment-bundle.test.mjs';assert not target.exists();write(target,test)
 p=W/'package.json';data=json.loads(p.read_text());assert 'tests/deployment-bundle.test.mjs' not in data['scripts']['test']
 data['scripts']['test']+=' tests/deployment-bundle.test.mjs';write(p,json.dumps(data,indent=2)+'\n')
 print('Added only graph regression and npm test registration; build/server unchanged for reproduction.')
elif mode=='fix':
 p=W/'build.mjs';s=p.read_text();old="'deployment-source9-prepare.js','deployment-session.js'";assert s.count(old)==1
 write(p,s.replace(old,"'deployment-source9-prepare.js','deployment-source10.js','deployment-session.js'"))
 p=W/'server.mjs';s=p.read_text();old="'deployment-api.js','deployment-session.js'";assert s.count(old)==1
 write(p,s.replace(old,"'deployment-api.js','deployment-native.js','deployment-source9.js','deployment-source9-data.js','deployment-source9-prepare.js','deployment-source10.js','deployment-session.js'"))
 print('Added exact required modules to the build list and explicit server allowlist; no dist/service change.')
else:raise SystemExit('Unknown mode')
