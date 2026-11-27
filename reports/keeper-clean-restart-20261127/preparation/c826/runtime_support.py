"""Reviewed external OS Python runtime, reused unchanged from c825."""

from pathlib import Path

import argparse,base64,hashlib,json,os,re,selectors,signal,stat,subprocess,sys,time,zlib

sha=lambda raw:hashlib.sha256(raw).hexdigest()

enc=lambda value:(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()

def need(value,code='fixed_c825_refused'):
    if not value:raise ValueError(code)

def read(path,maximum=1048576,owner=0):
    before=path.lstat();need(stat.S_ISREG(before.st_mode)and before.st_uid==owner and before.st_nlink==1
        and not before.st_mode&0o022 and before.st_size<=maximum,'file_metadata')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    try:
        raw=bytearray()
        while True:
            part=os.read(fd,min(65536,maximum+1-len(raw)))
            if not part:break
            raw.extend(part);need(len(raw)<=maximum,'file_bound')
        key=lambda st:(st.st_dev,st.st_ino,st.st_uid,st.st_mode,st.st_nlink,st.st_size,st.st_mtime_ns)
        need(key(before)==key(os.fstat(fd))==key(path.lstat())and len(raw)==before.st_size,'file_changed')
        return bytes(raw)
    finally:os.close(fd)

def runtime_tree(folder):
    allowed_links={'sitecustomize.py':'/etc/python3.12/sitecustomize.py',
        '_sysconfigdata__linux_x86_64-linux-gnu.py':'_sysconfigdata__x86_64-linux-gnu.py',
        'config-3.12-x86_64-linux-gnu/libpython3.12.so':'../../x86_64-linux-gnu/libpython3.12.so.1'}
    rows=[];total=0;visited=0;links=set();stack=[(folder,0)];end=time.monotonic()+20
    while stack:
        directory,depth=stack.pop();need(depth<=16 and time.monotonic()<end,'runtime_inventory_deadline')
        with os.scandir(directory)as entries:
            for entry in entries:
                visited+=1;need(visited<=8192 and time.monotonic()<end,'runtime_inventory_bound')
                if entry.name in('site-packages','dist-packages'):continue
                item=entry.stat(follow_symlinks=False);path=Path(entry.path)
                if stat.S_ISDIR(item.st_mode):stack.append((path,depth+1));continue
                if path.suffix not in('.py','.so','.pyc'):continue
                relative=str(path.relative_to(folder))
                if stat.S_ISLNK(item.st_mode):
                    need(relative in allowed_links and item.st_uid==0 and item.st_nlink==1,'runtime_link_metadata')
                    key=lambda st:(st.st_dev,st.st_ino,st.st_uid,st.st_mode,st.st_nlink,st.st_size,st.st_mtime_ns,st.st_ctime_ns)
                    target=os.readlink(path);need(target==allowed_links[relative]and key(item)==key(path.lstat()),'runtime_link_target')
                    need(os.readlink(path)==target and key(item)==key(path.lstat()),'runtime_link_changed')
                    rows.append(['symlink',relative,target,item.st_uid,stat.S_IMODE(item.st_mode),item.st_nlink]);links.add(relative);continue
                need(stat.S_ISREG(item.st_mode)and not item.st_mode&0o022,'runtime_file_metadata')
                raw=read(path,16777216);total+=len(raw);need(total<=134217728 and len(rows)<4096,'runtime_inventory_bound')
                rows.append(['file',relative,len(raw),sha(raw)])
    rows.sort()
    need(rows and links==set(allowed_links),'runtime_required_links')
    return{'files':len(rows)-len(links),'symlinks':len(links),'entries':len(rows),'bytes':total,'sha256':sha(enc(rows))}

def runtime_review():
    # Only OS stdlib imports. This explicitly supplies and records the external runtime.
    need(sys.flags.isolated==1 and sys.flags.no_site==1 and sys.dont_write_bytecode,'controller_python_isolation')
    import copy,datetime,decimal,fcntl,functools,http.client,math,secrets,shutil,socket,ssl,tempfile,typing,urllib.error,urllib.request,bz2,lzma
    stdlib=Path(os.__file__).resolve().parent;need(re.fullmatch('/usr/lib/python3\\.[0-9]+',str(stdlib))is not None,'OS_stdlib_path')
    executable=Path(sys.executable).resolve();need(re.fullmatch('/usr/bin/python3\\.[0-9]+',str(executable))is not None,'OS_interpreter_path')
    mapped=set()
    with Path('/proc/self/maps').open('rb')as stream:maps_raw=stream.read(65537)
    need(len(maps_raw)<=65536,'OS_maps_bound')
    for line in maps_raw.decode('utf8','strict').splitlines():
        part=line.split(None,5)
        if len(part)==6 and part[5].startswith('/'):
            candidate=Path(part[5]).resolve()
            if '.so'in candidate.name and not candidate.is_relative_to(stdlib):
                need(str(candidate).startswith('/usr/lib/x86_64-linux-gnu/'),'OS_library_scope');mapped.add(candidate)
    need(0<len(mapped)<=32,'OS_library_count')
    mounts=[{'source':str(executable),'target':'/usr/bin/python3'},
        {'source':str(stdlib),'target':str(stdlib)}]
    mounts.extend({'source':str(path),'target':str(path)}for path in sorted(mapped))
    loader=Path('/lib64/ld-linux-x86-64.so.2').resolve();need(loader in mapped,'OS_loader_not_mapped')
    mounts.append({'source':str(loader),'target':'/lib64/ld-linux-x86-64.so.2'})
    # Exact paths observed by the separate c824 loader/LDD diagnosis. These are
    # six file mounts in the NEW root, never a host library-directory mount.
    aliases={
        '/lib/x86_64-linux-gnu/libm.so.6':('/usr/lib/x86_64-linux-gnu/libm.so.6',952616,'5dcc4d25466e29ca390ed6fabb371c69b65dff6fa4e91c34561057a020d6994a'),
        '/lib/x86_64-linux-gnu/libz.so.1':('/usr/lib/x86_64-linux-gnu/libz.so.1.3',113000,'f61677c7bdb7c2aa2a243ea781bfd16afcb361cede7b4ef76127a9d8eb9a5242'),
        '/lib/x86_64-linux-gnu/libexpat.so.1':('/usr/lib/x86_64-linux-gnu/libexpat.so.1.9.1',186624,'286682ecbc5e59a638963b1a4e6351e65eb32fcf4bdcb9cb7569b6a61fe06a8d'),
        '/lib/x86_64-linux-gnu/libc.so.6':('/usr/lib/x86_64-linux-gnu/libc.so.6',2129424,'755a371e86cc9f564ab54f66140747700fb0a103f698f659f2060f707897e09a'),
        '/lib/x86_64-linux-gnu/libbz2.so.1.0':('/usr/lib/x86_64-linux-gnu/libbz2.so.1.0.4',78944,'cc08c9f50a8009ffd6391e0116a100369b11ca9238fa52392c019e6645b122a1'),
        '/lib/x86_64-linux-gnu/liblzma.so.5':('/usr/lib/x86_64-linux-gnu/liblzma.so.5.4.5',202904,'26b37d25f7ca2a2d348de8ecabacda12e921cd933b21fa069a179760db77219d')}
    alias_review={}
    for logical,(canonical,size,digest)in aliases.items():
        path=Path(logical);before=path.lstat();source=Path(canonical)
        need(before.st_uid==0 and before.st_nlink==1 and(stat.S_ISREG(before.st_mode)or stat.S_ISLNK(before.st_mode)),'OS_alias_metadata')
        need(path.resolve(strict=True)==source and source in mapped,'OS_alias_canonical')
        raw=read(source,16777216);need(len(raw)==size and sha(raw)==digest,'OS_alias_pin')
        key=lambda item:(item.st_dev,item.st_ino,item.st_uid,item.st_mode,item.st_nlink,item.st_size,item.st_mtime_ns,item.st_ctime_ns)
        need(key(path.lstat())==key(before)and path.resolve(strict=True)==source
            and(source.stat().st_dev,source.stat().st_ino)==(path.stat().st_dev,path.stat().st_ino),'OS_alias_changed')
        mounts.append({'source':canonical,'target':logical})
        alias_review[logical]={'source':canonical,'bytes':size,'sha256':digest,
            'host_uid':before.st_uid,'host_mode':stat.S_IMODE(before.st_mode),'host_link_count':before.st_nlink}
    files={}
    for row in mounts:
        if row['target']==str(stdlib):continue
        raw=read(Path(row['source']),16777216);files[row['target']]={'bytes':len(raw),'sha256':sha(raw)}
    return{'schema':1,'kind':'popl-c825-external-OS-runtime','version':sys.version,'stdlib':str(stdlib),
        'stdlib_tree':runtime_tree(stdlib),'stdlib_inventory_scope':'regular .py/.so/.pyc bytes including caches plus exactly3 reviewed link metadata; pruned site-packages/dist-packages; link targets never followed',
        'mounts':mounts,'files':files,'required_logical_aliases':alias_review,
        'site_packages_enabled':False,'OS_runtime_is_external':True,
        'OS_disaster_recovery_proved':False,'actual_second_host':False}
