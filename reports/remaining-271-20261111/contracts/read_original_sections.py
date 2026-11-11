"""Extract exact baseline report sections referenced by the assigned records."""
import importlib.util,json,re,subprocess,hashlib
from pathlib import Path
s=importlib.util.spec_from_file_location('review',Path(__file__).with_name('build_review.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
a=json.loads(m.INPUT.read_text(encoding='utf-8'))['rows']; result=[]
for index,r in enumerate(a[:60]):
    record=r['original_record']; sources=list(record.get('historical_sources',[]))
    if isinstance(record.get('original'),dict):
        q=record['original'];sources.append(dict(path=q.get('path'),heading_line=q.get('heading_line',1),
            section=q.get('actual_heading','').lstrip('#').strip()))
    if not sources:
        for key in ('path','report','source','source_file','file'):
            p=record.get(key)
            if isinstance(p,str) and p.startswith('reports/') and p.endswith('.md'):
                sources.append({'path':p,'heading_line':record.get('line',1)})
    for source in sources:
        p=source.get('path')
        if not p or not p.endswith('.md'):continue
        mode='git_baseline'
        try:data=m.baseline_blob(p)
        except subprocess.CalledProcessError:
            mode='retained_untracked_original_not_git_baseline'
            data=(m.ROOT/p).read_bytes()
        lines=data.decode('utf-8-sig').splitlines()
        n=max(0,int(source.get('heading_line',1))-1)
        name=source.get('section','').lstrip('#').strip()
        if name:
            hits=[i for i,line in enumerate(lines) if re.sub(r'^#+\s*','',line).strip()==name]
            if hits:n=min(hits,key=lambda i:abs(i-n))
        if n>=len(lines):n=0
        match=re.match(r'^(#+)\s',lines[n]);level=len(match[1]) if match else 1
        end=len(lines)
        for i in range(n+1,len(lines)):
            h=re.match(r'^(#+)\s',lines[i])
            if h and len(h[1])<=level:end=i;break
        result.append(dict(index=index,id=r['id'],path=p,source_mode=mode,raw_sha256=hashlib.sha256(data).hexdigest(),line_start=n+1,line_end=end,
                           text='\n'.join(lines[n:end])+'\n'))
Path(__file__).with_name('original-sections.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(len(result),'exact sections extracted')
