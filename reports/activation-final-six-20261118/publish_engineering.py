"""Preserve finite engineering evidence losslessly, without executing tests."""
from pathlib import Path
import hashlib,io,json,lzma,tarfile

R=Path(__file__).resolve().parents[2]
P=Path(__file__).resolve().parent
O=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/activation-final-six-20261118')
sha=lambda raw:hashlib.sha256(raw).hexdigest()
directories=['oracle','pricing-marks01','pricing-basis01','feed-identity01','carry-sentinel',
 'royalty-final10-tests','royalty-cohorts01','royalty-cohorts02','royalty-cohorts03','royalty-cohort04',
 'royalty-status04','royalty-book04','royalty-all04','royalty-status-book05-aligned','royalty-status-book05-flag',
 'royalty-status-book06','royalty-status-book08-bounded','royalty-status-book08-gross','royalty-status-final07','royalty-final10','lp-canonical','build/final01']
names=['ROYALTY_ENGINEERING_INDEX.json','ROYALTY_FINAL10_REVIEW.md','ExactRoyaltyStatusBook20261118.t.sol','ADOPTION.json','SOURCE_FREEZE.json','LAYOUT_ACCEPTANCE.json']
paths=set()
for directory in directories:
    folder=O/directory
    assert folder.is_dir(),directory
    for p in folder.rglob('*'):
        if p.is_file() and not {'out','cache','__pycache__'}.intersection(p.relative_to(folder).parts):paths.add(p)
for name in names:
    assert (O/name).is_file(),name
    paths.add(O/name)
dest=P/'engineering';dest.mkdir(exist_ok=False)
manifest=[];total=0
archive=dest/'evidence.tar.xz'
with lzma.open(archive,'wb',filters=[{'id':lzma.FILTER_LZMA2,'dict_size':64*1024*1024,'preset':6}])as compressed:
    with tarfile.open(fileobj=compressed,mode='w|',format=tarfile.USTAR_FORMAT)as tar:
        for p in sorted(paths):
            name=p.relative_to(O).as_posix();raw=p.read_bytes()
            assert 0<=len(raw)<=64*1024*1024 and not name.startswith('/') and '..'not in Path(name).parts
            total+=len(raw);assert total<=768*1024*1024,'Finite engineering publication bound exceeded'
            row={'name':name,'bytes':len(raw),'sha256':sha(raw)};manifest.append(row)
            entry=tarfile.TarInfo(name);entry.size=len(raw);entry.mode=0o644;entry.mtime=0
            tar.addfile(entry,io.BytesIO(raw))
remaining={x['name']:x for x in manifest}
with tarfile.open(archive,'r|xz')as tar:
    for entry in tar:
        assert entry.isfile()and entry.name in remaining
        expected=remaining.pop(entry.name);assert entry.size==expected['bytes']
        stream=tar.extractfile(entry);assert stream is not None
        raw=stream.read(64*1024*1024+1)
        assert len(raw)==expected['bytes']and sha(raw)==expected['sha256']
assert not remaining
result={'schema':1,'archive':'evidence.tar.xz','archive_sha256':sha(archive.read_bytes()),'archive_bytes':archive.stat().st_size,
 'original_bytes':total,'files':manifest,'every_member_verified_without_extraction':True,
 'scope':'Finite isolated new/affected source probes; rejected variants and fixture/tool failures remain distinct. This archive does not run or approve anything.',
 'generated_forge_cache_and_out_directories_excluded':True,'production_approved':False}
(dest/'MANIFEST.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items()if k!='files'},indent=2))
