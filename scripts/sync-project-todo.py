"""Generate or verify the contract repository's TODO.md; no publication side effects."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STATUSES={'done':'Implemented','progress':'In progress','todo':'To do'}

def render():
    data=json.loads((ROOT/'docs/project-todo.json').read_text(encoding='utf-8-sig'))
    if data.get('schema')!=1:raise ValueError('Unsupported Todo schema')
    datetime.date.fromisoformat(data['reviewed'])
    ids=set();tasks=[]
    for area in data['areas']:
        if area['id'] in ids:raise ValueError('Duplicate area')
        ids.add(area['id'])
        for task in area['tasks']:
            if task['id'] in ids or task['status'] not in STATUSES or not task['title'] or not task['text']:raise ValueError('Invalid task')
            href=task.get('href')
            if not isinstance(href,str) or not href or any(c in href for c in '\n\r()<>'):raise ValueError('Task requires a related-file link')
            target=(ROOT/href.split('#',1)[0]).resolve()
            if not target.is_relative_to(ROOT) or not target.is_file():raise ValueError('Task link must resolve to a repository file')
            criteria=task.get('acceptance',[])
            if not isinstance(criteria,list) or any(not isinstance(item,str) or not item.strip() or '\n' in item or '\r' in item for item in criteria):raise ValueError('Acceptance criteria must be nonempty single-line strings')
            ids.add(task['id']);tasks.append(task)
    digest=hashlib.sha256(json.dumps(data,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
    counts={key:sum(t['status']==key for t in tasks) for key in STATUSES}
    md=f"# Project Todo\n\n**Reviewed {data['reviewed']} | Contracts undeployed | Not approved for production**\n\n"
    md+='The single task list for the whole PoPL project. Open a task\'s acceptance criteria for the detailed release requirements. There is no Todo page on the public website.\n\n'
    md+=f"**{counts['todo']} To do | {counts['progress']} In progress | {counts['done']} Implemented locally**\n\n"
    md+='Implemented means built and locally checked, not deployed or independently audited. This list includes the current local development candidate; some code changes still await their own publication. Publishing this checklist does not publish or qualify that code.\n\n'
    md+='[Feature and evidence reference](docs/IMPLEMENTATION_STATUS.md) | [Release approval record](docs/RELEASE_CHECKLIST.md) | [Update procedure](docs/TODO_WORKFLOW.md)\n\n'
    md+='[Smart contracts](#smart-contracts) | [Backend](#backend) | [Frontend](#frontend) | [Creator tasks](#creator-tasks--zzz-team) | [Testing](#testing--qualification) | [Security](#security--audit) | [Operations](#launch--operations) | [Future migration](#future-migration)\n\n'
    for area in data['areas']:
        md+=f"## {area['title']}\n\n{area['caption']}\n\n"
        for task in sorted(area['tasks'],key=lambda t:('todo','progress','done').index(t['status'])):
            md+=f"<a id=\"task-{task['id']}\"></a>\n\n"
            md+=f"- [{'x' if task['status']=='done' else ' '}] **[{task['title']}]({task['href']})** - {STATUSES[task['status']]}. {task['text']}\n\n"
            if task.get('acceptance'):
                md+='  <details>\n  <summary>Acceptance criteria</summary>\n\n'
                for item in task['acceptance']:md+=f'  - {item}\n'
                md+='\n  </details>\n\n'
        md+='\n'
    md+='---\n\nGenerated from [the task ledger](docs/project-todo.json). Update that ledger, then run `python scripts/sync-project-todo.py`; use `--check` to detect stale generated content.\n\n'
    md+=f'Snapshot SHA-256: `{digest}`.\n'
    return md

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    path=ROOT/'TODO.md';content=render()
    if args.check:
        if not path.is_file() or path.read_text(encoding='utf-8')!=content:raise SystemExit('TODO.md is stale; regenerate before publishing')
    else:path.write_text(content,encoding='utf-8',newline='\n')
    print('Project Todo '+('verified.' if args.check else 'generated.'))
if __name__=='__main__':main()
