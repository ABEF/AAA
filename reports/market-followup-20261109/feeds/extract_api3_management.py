"""Extract literal public API3 catalog management entry; no executable site code."""
import ast,json,re
from pathlib import Path
P=Path(__file__).resolve().parent;s=(P/'discovery/api3-index-js.raw').read_text(encoding='utf8')
m=re.search(r"fve=JSON.parse\(('(?:[^'\\]|\\.)*')\)",s)
if m:
 rows=json.loads(ast.literal_eval(m.group(1)))
 eth='0x4554482f55534400000000000000000000000000000000000000000000000000'
 selected=[x for x in rows if x[0]==eth]
 result={'source':'discovery/api3-index-js.raw','total_rows':len(rows),'ETH_USD':selected}
 (P/'api3-management-selected.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
 print(json.dumps(result,indent=2))
else:
 print('Literal management JSON not located; no extraction inference.')
