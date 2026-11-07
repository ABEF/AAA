from pathlib import Path
R=Path.cwd();E=Path(__file__).parent
def edit(name,changes):
 p=R/name;raw=p.read_bytes();s=raw.decode().replace('\r\n','\n')
 dest=E/'originals'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
 for old,new in changes:
  assert s.count(old)==1,(name,old[:120],s.count(old))
  s=s.replace(old,new)
 p.write_bytes(s.replace('\n','\r\n').encode()if b'\r\n'in raw else s.encode())
edit('frontend_api/earnings_checkpoint.py',[
 ("def source_identity():\n    return {n: hashlib.sha256((ROOT/n).read_bytes().replace(b'\\r\\n', b'\\n')).hexdigest()\n            for n in SOURCE_FILES}","""EXACT_SOURCE_FILES = ('frontend_api/earnings_checkpoint_v2.py',
    'frontend_api/earnings_exact_lp.py', 'zzz_ops/exact_lp.py')


def schema(engine):
    p=engine.p
    require(p.lineage is None, 'Checkpoint profile does not support predecessor lineage')
    require(p.accounting_version in (6,7) and p.custody_version == 5 and p.fee_intake_version == 1,
            'Checkpoint requires explicit accounting6/7 custody5/fee-intake1')
    if p.accounting_version==7:
        require(royalty_profile(p)==4, 'Checkpoint2 requires exact original-currency royalty4')
        return 2
    return 1


def source_identity(version=1):
    require(type(version) is int and version in (1,2), 'Unknown checkpoint semantic profile')
    return {n: hashlib.sha256((ROOT/n).read_bytes().replace(b'\\r\\n', b'\\n')).hexdigest()
            for n in SOURCE_FILES+(EXACT_SOURCE_FILES if version==2 else ())}"""),
 ("    require(p.accounting_version!=7, 'Accounting7 exact-LP checkpoint2 is not implemented; use complete raw history')\n    require(p.lineage is None, 'Checkpoint profile does not support predecessor lineage')\n    require(p.accounting_version in (6,7) and p.custody_version == 5 and p.fee_intake_version == 1,\n            'Checkpoint requires explicit accounting6/custody5/fee-intake1')", "    version=schema(engine)"),
 ("        accounting=6, custody=5, fee_intake=1, royalty_settlement=royalty_profile(p),", "        accounting=p.accounting_version, custody=5, fee_intake=1, royalty_settlement=royalty_profile(p),\n        **({'lp_allocation':1} if version==2 else {}),"),
 ("    history: HistorySnapshot\n\n    def validate_history", "    history: HistorySnapshot\n    schema: int = 1\n\n    def validate_history"),
 ("        require(isinstance(model,Replay) and not model.minted and model.events==0,\n                'Checkpoint consumer is not a fresh earnings replay')", """        from frontend_api.earnings_exact_lp import ExactReplay
        require(isinstance(model,Replay) and not model.minted and model.events==0,
                'Checkpoint consumer is not a fresh earnings replay')
        require((self.schema==2 and isinstance(model,ExactReplay)) or
                (self.schema==1 and not isinstance(model,ExactReplay)),
                'Checkpoint schema differs from the earnings allocation model')"""),
 ("        model.day=defaultdict(int)\n", "        model.day=defaultdict(int)\n        if self.schema==2:\n            from frontend_api.earnings_checkpoint_v2 import restore\n            restore(model,self.payload['exact_lp'])\n"),
 ("                    and type(data['schema']) is int and data['schema']==1,\n                    'Unknown earnings checkpoint schema')\n            require(data['sources']==source_identity(), 'Earnings checkpoint semantic source changed')", "                    and type(data['schema']) is int and data['schema'] in (1,2),\n                    'Unknown earnings checkpoint schema')\n            require(data['schema']==schema(engine), 'Checkpoint2 is required for accounting7; historical schemas cannot be reinterpreted')\n            require(data['sources']==source_identity(data['schema']), 'Earnings checkpoint semantic source changed')"),
 ("        require(isinstance(v,dict) and set(v)=={'shared','accounts','collection','history','emitters','lp_assets','royalty_assets'},\n                'Incomplete earnings checkpoint state')", "        version=schema(engine)\n        fields={'shared','accounts','collection','history','emitters','lp_assets','royalty_assets'}\n        if version==2:fields.add('exact_lp')\n        require(isinstance(v,dict) and set(v)==fields, 'Incomplete earnings checkpoint state')"),
 ("        probe=Replay(anchor['timestamp'],track_all=True)\n        probe.begin(v['emitters'],v['lp_assets'],v['royalty_assets'],fee_intake_version=1,royalty_settlement_version=royalty_profile(engine.p))\n        seed=Seed('',anchor,{},v,None);seed.restore(probe);probe.finish()", """        if version==2:
            from frontend_api.earnings_exact_lp import ExactReplay
            from frontend_api.earnings_checkpoint_v2 import validate
            validate(v['exact_lp'],s,v['lp_assets'],v['accounts'])
            probe=ExactReplay(anchor['timestamp'],track_all=True)
        else:probe=Replay(anchor['timestamp'],track_all=True)
        probe.begin(v['emitters'],v['lp_assets'],v['royalty_assets'],fee_intake_version=1,royalty_settlement_version=royalty_profile(engine.p))
        seed=Seed('',anchor,{},v,None,version);seed.restore(probe);probe.finish()"""),
 ("        return Seed(self.digest,anchor,bound,payload,history)", "        return Seed(self.digest,anchor,bound,payload,history,data['schema'])"),
])
edit('frontend_api/earnings_checkpoint_build.py',[
 ('identity, source_identity, MAX_BYTES','identity, source_identity, schema, MAX_BYTES'),
 ("    sources=source_identity()", "    version=schema(engine)\n    sources=source_identity(version)"),
 ("    model=Replay(header['timestamp'],track_all=True)", "    if version==2:\n        from frontend_api.earnings_exact_lp import ExactReplay\n        model=ExactReplay(header['timestamp'],track_all=True)\n    else:model=Replay(header['timestamp'],track_all=True)"),
 ("        if royalty_profile(p) == 4:", "        if version==2:\n            require(p._uint('rewards','rewardBucket(uint256)',i,block=at)==bucket,\n                    'Checkpoint exact NFT LP bucket differs from chain')\n            for asset in lp:\n                actual=tuple(int(w,16) for w in p._call(p.contracts['rewards'].address,\n                    'claimableComponents(uint256,address)',i,asset,block=at,words=2))\n                require(actual==model.components(i,asset),'Checkpoint exact NFT LP components differ from chain')\n        if royalty_profile(p) == 4:"),
 ("    encoded=encode(state)", "    if version==2:\n        from frontend_api.earnings_checkpoint_v2 import capture\n        state['exact_lp']=capture(model)\n    encoded=encode(state)"),
 ("    require(source_identity()==sources, 'Checkpoint semantic source changed during construction')\n    payload=dict(schema=1,", "    require(source_identity(version)==sources, 'Checkpoint semantic source changed during construction')\n    payload=dict(schema=version,"),
])
print('Integrated explicit schema2 dispatch, exact model seeds and all-NFT on-chain reconciliation')
