"""Add the two pinned private fixture references without decoding or publishing them."""
from pathlib import Path
import hashlib,json,os,stat
BASE=Path(__file__).resolve().parent
PRIVATE=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/keeper-reconstruction-20261127/private/campaign-001')
sha=lambda raw:hashlib.sha256(raw).hexdigest()
expected={'references/keeper-config.json':{'bytes':5254,'sha256':'1c3d51343b990a2abc4a87cf9dd7049237f23a34a39708f945d98f228e3f5cb8'},
 'references/policy.json':{'bytes':2731,'sha256':'7e85ff8b6709803cb9f4e621150d05b08262599e94a2dccd9a23e01bb41452ba'}}
metadata=json.loads((PRIVATE/'export-002/EXPORT_METADATA.json').read_bytes());assert metadata['references']==expected
assert metadata['original_unchanged'] is True and metadata['signer_material_exported'] is False
for name,row in expected.items():
    path=PRIVATE/'export-002'/name
    for item in (*reversed(path.parents),path):
        st=item.lstat();assert not stat.S_ISLNK(st.st_mode) and not getattr(st,'st_file_attributes',0)&0x400
    before=path.lstat();assert before.st_size==row['bytes'] and before.st_nlink==1 and stat.S_ISREG(before.st_mode)
    key=lambda st:(st.st_dev,st.st_ino,st.st_size,st.st_nlink,st.st_mtime_ns)
    fd=os.open(path,os.O_RDONLY|getattr(os,'O_BINARY',0))
    with os.fdopen(fd,'rb') as stream:
        raw=stream.read(65537);assert key(os.fstat(stream.fileno()))==key(before)==key(path.lstat())
    assert len(raw)==row['bytes'] and sha(raw)==row['sha256']
    target=PRIVATE/'kit'/name;target.parent.mkdir(exist_ok=True)
    with target.open('xb') as stream:assert stream.write(raw)==len(raw);stream.flush();os.fsync(stream.fileno())
(PRIVATE/'proof').mkdir()
record={'schema':1,'references':expected,'raw_configuration_decoded_or_printed':False,
 'raw_configuration_or_policy_published':False,'expected_kit_members':49,
 'runtime_review_sha256':sha((PRIVATE/'export-002/RUNTIME_REVIEW.json').read_bytes()),
 'source_or_native_backup_format_changed':False}
with (BASE/'KIT_REFERENCE_ASSEMBLY.json').open('x',encoding='utf8') as stream:json.dump(record,stream,indent=2,sort_keys=True);stream.write('\n')
print(json.dumps({'references_copied':2,'expected_kit_members':49,'raw_configuration_disclosed':False}))
