import os,stat,json
paths=['/opt','/opt/zzz-keeper-staging','/opt/zzz-keeper-staging/bin','/opt/zzz-keeper-staging/bin/anvil','/opt/zzz-keeper-staging/bin/cast','/usr/bin/python3']
rows=[]
for p in paths:
 s=os.stat(p);rows.append({'path':p,'uid':s.st_uid,'gid':s.st_gid,'mode':oct(stat.S_IMODE(s.st_mode))})
print(json.dumps({'read_only':True,'paths':rows}))
