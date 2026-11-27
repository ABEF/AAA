"""One-off c824 OS metadata diagnostic: fixed stdlib tree, no file-body reads."""
from pathlib import Path
import json,os,stat,time

ROOT=Path('/usr/lib/python3.12')
MAX_SECONDS=20
MAX_ENTRIES=8192
MAX_DEPTH=16
MAX_PROBLEMS=16
MAX_TARGET_CHARS=512


def main():
    began=time.monotonic();end=began+MAX_SECONDS
    visited=selected=0;problems=[];stack=[(ROOT,0)];bound=None
    try:
        while stack:
            directory,depth=stack.pop()
            if depth>MAX_DEPTH:bound='depth';break
            if time.monotonic()>=end:bound='seconds';break
            with os.scandir(directory)as entries:
                for entry in entries:
                    if visited>=MAX_ENTRIES:bound='entries';break
                    if time.monotonic()>=end:bound='seconds';break
                    visited+=1
                    if entry.name in('site-packages','dist-packages'):continue
                    path=Path(entry.path)
                    if entry.is_dir(follow_symlinks=False):
                        stack.append((path,depth+1));continue
                    if path.suffix not in('.py','.so','.pyc'):continue
                    item=entry.stat(follow_symlinks=False)
                    selected+=1
                    if stat.S_ISREG(item.st_mode)and item.st_uid==0 and item.st_nlink==1 and not item.st_mode&0o022:
                        continue
                    kind=('symlink'if stat.S_ISLNK(item.st_mode)else
                        'regular'if stat.S_ISREG(item.st_mode)else
                        'fifo'if stat.S_ISFIFO(item.st_mode)else
                        'socket'if stat.S_ISSOCK(item.st_mode)else
                        'character'if stat.S_ISCHR(item.st_mode)else
                        'block'if stat.S_ISBLK(item.st_mode)else'other')
                    row={'relative_path':str(path.relative_to(ROOT)),'type':kind,'uid':item.st_uid,
                        'mode':stat.S_IMODE(item.st_mode),'link_count':item.st_nlink}
                    if kind=='symlink':
                        target=os.readlink(path)
                        if len(target)>MAX_TARGET_CHARS:raise ValueError('symlink_target_bound')
                        row['symlink_target']=target
                    problems.append(row)
                    if len(problems)>=MAX_PROBLEMS:bound='problems';break
                if bound is not None:break
        result={'schema':1,'kind':'popl-c824-OS-runtime-metadata-only','root':str(ROOT),
            'visited_entries':visited,'selected_entries':selected,'problem_entries':problems,
            'stopped_at_bound':bound,'complete_selected_scan':not stack and bound is None,
            'maximum_seconds':MAX_SECONDS,'maximum_entries':MAX_ENTRIES,'maximum_depth':MAX_DEPTH,
            'maximum_problems':MAX_PROBLEMS,'maximum_target_characters':MAX_TARGET_CHARS,
            'file_bodies_opened':0,'symlink_targets_opened':0,'application_imports':0,
            'configuration_or_journal_or_signer_files_accessed':False}
    except Exception as exc:
        result={'schema':1,'kind':'popl-c824-OS-runtime-metadata-only','refused':True,
            'error_type':type(exc).__name__,'visited_entries':visited,'selected_entries':selected,
            'problem_entries':problems,'file_bodies_opened':0,'symlink_targets_opened':0}
    raw=(json.dumps(result,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
    if len(raw)>16384:
        print('{"refused":true,"reason":"metadata_output_bound"}')
        return 1
    print(raw.decode('utf8'),end='')
    return 0 if not result.get('refused')else 1


if __name__=='__main__':raise SystemExit(main())
