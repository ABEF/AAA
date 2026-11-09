"""Synthetic mint2 gate and pinned-wire checks, not provider/operating approval."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from zzz_ops import production_v15 as P,production_v14 as OLD
from zzz_ops.production_observer_v15 import Observer
from zzz_ops import production_observer as O
from zzz_ops.abi import keccak256
from zzz_ops.opensea_drop import address_list_hash

ROOT=Path(__file__).resolve().parents[1]


def addr(n):return '0x'+f'{n:040x}'
def digest(n):return '0x'+f'{n:064x}'
def encoded(*values):return '0x'+''.join(f'{int(v,16) if isinstance(v,str) and v.startswith("0x") else int(v):064x}' for v in values)


class MintInventoryTests(unittest.TestCase):
    def setUp(self):
        self.config=json.loads((ROOT/'config/production.example.json').read_text(encoding='utf-8'))
        self.chain=self.config['chains'][0]
        for i,(role,row) in enumerate(self.chain['modules'].items(),1):row['address']=addr(i)
        for i,(role,row) in enumerate(self.chain['helpers'].items(),101):row['address']=addr(i)
        price=5*10**16
        self.chain['protocol_policy']['sale'].update(mint_price_wei=str(price),recipient=addr(999))
        section=self.chain['primary_mint'];c=section['mint_config']
        c.update(teamAllocation=20,allowlistAllocation=500,publicWalletLimit=10,feeBps=1000,maxBatch=4,
            teamStart=100,teamEnd=199,allowlistStart=200,allowlistEnd=299,publicStart=300,publicEnd=399,
            releaseUnusedTeamToPublic=False,merkleRoot=digest(10),feeRecipient=addr(998),allowedPayersHash=address_list_hash([]))
        section.update(allowed_payers=[],configuration_hash=digest(11),configuration_values_hash=digest(12),
            configuration_review_hash=digest(13),revision=1)
        section['configuration_hash'],section['configuration_values_hash']=P.configuration_hashes(self.chain,section)
        self.chain['canonical_handoff'].update(origin_chain_id=4663,origin_vault=self.chain['modules']['vault']['address'])
        helper=self.chain['helpers']['seadrop_mint']['address']
        def nftid(i):return int(P.V.identity([(4663,'uint256'),(self.chain['modules']['vault']['address'],'address'),(i,'uint256')]),16)
        rows=[dict(ordinal=i,reverse_ordinal=i,id=nftid(i),recipient=a,stage=stage,nft_original_recipient=a,nft_stage=stage)
            for i,(a,stage) in enumerate(((addr(700),1),(addr(701),2),(addr(700),3)),1)]
        section['observed']=dict(helper=helper,helper_version=1,sea_drop=section['sea_drop'],
            sea_drop_code_hash=section['sea_drop_runtime_hash'],runtime_hash=section['sea_drop_runtime_hash'],config=copy.deepcopy(c),
            configured=True,minting=False,revision=1,configuration_hash=section['configuration_hash'],configuration_values_hash=section['configuration_values_hash'],
            configuration_review_hash=digest(13),reviewed_mint_price=price,total_minted=3,nft_minted_count=3,vault_sequence=3,
            phase_minted=[1,1,1],current_phase=3,ordinals=rows,
            wallets=[dict(address=addr(700),lifetime=2,allowlist=0),dict(address=addr(701),lifetime=1,allowlist=1)],
            public_drop=dict(mintPrice=price,startTime=300,endTime=399,maxTotalMintableByWallet=10,feeBps=1000,restrictFeeRecipients=True),
            creator_payout=addr(999),allowlist_root=digest(10),allowed_fee_recipients=[addr(998)],allowed_payers=[],
            signer_count=0,token_gate_count=0,mint_end=399,mint_end_revision=1)
        vrf=self.chain['nft_inventory']['randomness']
        vrf.update(recovery_policy=dict(unserved_request='original_request_remains_valid',
            refund_or_expiry='cannot_invalidate_original_fulfillment',failed_callback='same_request_same_result',reroll='none'),
            integration_evidence=dict(fulfilled_request_id=1,recovery_request_id=1,original_result_sha256='1'*64,
                recovered_result_sha256='1'*64,request_selector=P.V.VRF_REQUEST_SELECTOR,callback_words_count=2,
                invalid_proof_rejection_sha256='2'*64,unauthenticated_callback_rejection_sha256='3'*64),
            funding=dict(source='external_subscription_reserve',owner=addr(702)))

    def gate(self):
        section=self.chain['primary_mint'];c=section['mint_config']
        def proof(_g,_record,_path,_chain,*,kind,**_kwargs):
            return dict(primary_drop_accepted=True,review_hash=section['configuration_review_hash'],allowlist_root=c['merkleRoot'],
                mint_price_wei=section['expected_mint_price_wei'],mint_config_sha256=P.V.configuration_hash(c),
                fee_bps=c['feeBps'],fee_recipient=c['feeRecipient'])
        g=P.V.Gate('1'*40)
        with patch.object(P.V,'_bound_proof',side_effect=proof):P.mint_integration(g,self.chain,'chains[0]')
        return g.issues

    def test_component_validates_original_recipients_not_current_owners(self):
        self.assertEqual([],self.gate())

    def test_each_core_book_or_control_mutation_is_rejected(self):
        baseline=copy.deepcopy(self.chain)
        changes=[('vault_sequence',4),('nft_minted_count',False),('total_minted',True),('phase_minted',[2,0,1]),
            ('minting',True),('allowlist_root',digest(44)),('allowed_payers',[addr(9)]),('signer_count',1),
            ('token_gate_count',1),('creator_payout',addr(9)),('mint_end',400),('configured',False),('current_phase',True)]
        for key,value in changes:
            with self.subTest(key=key):
                self.chain=copy.deepcopy(baseline);self.chain['primary_mint']['observed'][key]=value
                self.assertTrue(self.gate())

    def test_transfer_cannot_reset_lifetime_or_allowlist_limits(self):
        o=self.chain['primary_mint']['observed'];o['ordinals'][1]['nft_original_recipient']=addr(999)
        self.assertTrue(any(i['code']=='mint.ordinal' for i in self.gate()))
        self.setUp();o=self.chain['primary_mint']['observed'];o['wallets'][0]['lifetime']=1
        self.assertTrue(any(i['code']=='mint.lifetime' for i in self.gate()))

    def test_team_reservation_and_phase_caps_are_independent(self):
        self.chain['primary_mint']['mint_config']['teamAllocation']=0
        self.assertTrue(any(i['code']=='mint.phase_caps' for i in self.gate()))
        self.setUp();self.chain['primary_mint']['mint_config']['allowlistAllocation']=0
        self.assertTrue(any(i['code']=='mint.phase_caps' for i in self.gate()))

    def test_zero_supply_is_explicit_not_a_substitute_for_funded_history(self):
        o=self.chain['primary_mint']['observed']
        o.update(total_minted=0,nft_minted_count=0,vault_sequence=0,phase_minted=[0,0,0],ordinals=[],wallets=[])
        self.assertEqual([],self.gate())

    def test_default_template_remains_unqualified_and_old_gate_is_unchanged(self):
        fresh=json.loads((ROOT/'config/production.example.json').read_text(encoding='utf-8'))
        old=json.loads((ROOT/'config/production.schema16.example.json').read_text(encoding='utf-8'))
        result=P.validate(fresh,now=1794190000)
        self.assertFalse(result['ready']);self.assertFalse(result['deployment_authorized'])
        self.assertTrue(result['opensea_primary_mint_supported'])
        self.assertNotIn('mint.opensea_unsupported',[i['code'] for i in result['issues']])
        self.assertIn('mint.opensea_unsupported',[i['code'] for i in OLD.validate(old,now=1794190000)['issues']])
        self.assertEqual((17,2,20),(fresh['schema_version'],fresh['mint_integration_version'],len(P.HELPERS)))
        self.assertIsNone(fresh['chains'][0]['primary_mint']['onboarding_evidence'])

    def test_new_bindings_are_explicit_and_do_not_relabel_schema16(self):
        bindings=P.expected_bindings(self.chain)
        self.assertEqual(self.chain['helpers']['seadrop_mint']['address'],bindings['modules']['nft']['seaDropMint'])
        self.assertEqual(P.SCHEMA_HASH,bindings['modules']['canonical']['SCHEMA'])
        self.assertEqual(1,bindings['helpers']['seadrop_mint']['MINT_INTEGRATION_VERSION'])
        self.assertNotEqual(OLD.SCHEMA_HASH,P.SCHEMA_HASH)

    def test_cli_default_dispatch_rejects_historical16(self):
        spec=importlib.util.spec_from_file_location('popl_mint_gate_cli',ROOT/'scripts/validate-production-config.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        self.assertFalse(module.validate({'schema_version':16})['production_qualification_supported'])
        self.assertEqual(17,module.validate({'schema_version':16})['schema_version'])


class MintObserverWireTests(unittest.TestCase):
    """Actual pinned ABI wire consumer with synthetic RPC bytes; no live chain."""
    setUp=MintInventoryTests.setUp
    def observer(self,bad_boolean=False,with_nft=False):
        chain=self.chain;section=chain['primary_mint'];c=section['mint_config'];helper=chain['helpers']['seadrop_mint']['address']
        nft=chain['modules']['nft']['address'];vault=chain['modules']['vault']['address'];sd=section['sea_drop']
        royalty=chain['helpers']['royalty_rewards']['address'];block={'blockHash':digest(50),'requireCanonical':True}
        response={}
        def add(target,signature,values,*args):
            data='0x'+keccak256(signature.encode()).hex()[:8]+''.join(O._word(a) for a in args)
            response[(target,data)]=encoded(*values)
        add(helper,'mintConfig()',[c[k] for k in P.CONFIG_FIELDS])
        for method,value in dict(totalMinted=int(with_nft),MINT_INTEGRATION_VERSION=1,configured=2 if bad_boolean else 1,minting=0,
                revision=1,reviewedMintPrice=5*10**16,currentPhase=3).items():add(helper,method+'()',[value])
        for method,value in dict(seaDrop=sd,seaDropCodeHash=section['sea_drop_runtime_hash'],configurationHash=section['configuration_hash'],
                configurationValuesHash=section['configuration_values_hash'],configurationReviewHash=digest(13)).items():add(helper,method+'()',[value])
        add(nft,'mintedCount()',[int(with_nft)]);add(vault,'sequence()',[int(with_nft)])
        for phase in (1,2,3):add(helper,'phaseMinted(uint8)',[int(with_nft and phase==2)],phase)
        if with_nft:
            identifier=int(P.V.identity([(4663,'uint256'),(vault,'address'),(1,'uint256')]),16)
            add(nft,'tokenAtOrdinal(uint256)',[identifier],1)
            add(nft,'mintOrdinalOf(uint256)',[1],identifier)
            add(helper,'originalMintRecipient(uint256)',[addr(701)],1)
            add(helper,'mintStage(uint256)',[2],1)
            add(nft,'originalMintRecipient(uint256)',[addr(701)],identifier)
            add(nft,'mintStageOf(uint256)',[2],identifier)
            add(helper,'mintStats(address)',[1,1,1000],addr(701))
            add(helper,'allowlistMinted(address)',[1],addr(701))
        add(sd,'getPublicDrop(address)',[5*10**16,300,399,10,1000,1],nft)
        add(sd,'getCreatorPayoutAddress(address)',[addr(999)],nft)
        add(sd,'getAllowListMerkleRoot(address)',[digest(10)],nft)
        add(sd,'getAllowedFeeRecipients(address)',[32,1,addr(998)],nft)
        for name in ('getPayers','getSigners','getTokenGatedAllowedTokens'):add(sd,name+'(address)',[32,0],nft)
        add(royalty,'mintEnd()',[399]);add(royalty,'mintEndRevision()',[1])
        calls=[]
        class RPC:
            def call(self,method,params):
                calls.append((method,params))
                if params[-1]!=block:raise AssertionError('Unpinned mint read')
                if method=='eth_getCode':return '0x00'
                if method!='eth_call':raise AssertionError('Non-read method')
                return response[(params[0]['to'],params[0]['data'])]
        observer=Observer(RPC(),chain);observer.block=block
        return observer,calls

    def test_bounded_wire_capture_uses_only_the_same_confirmed_hash(self):
        observer,calls=self.observer();observer.primary_mint()
        self.assertEqual([],observer.errors)
        observed=self.chain['primary_mint']['observed']
        self.assertEqual((0,[],[]),(observed['total_minted'],observed['ordinals'],observed['wallets']))
        self.assertEqual(1,observed['helper_version'])
        self.assertLess(len(calls),60)
        self.assertTrue(all(method in ('eth_call','eth_getCode') for method,_ in calls))

    def test_noncanonical_bool_is_unavailable_never_a_guessed_false(self):
        observer,_=self.observer(bad_boolean=True);observer.primary_mint()
        self.assertIsNone(self.chain['primary_mint']['observed'])
        self.assertEqual([dict(path='primary_mint',code='mint.unavailable')],observer.errors)

    def test_nonempty_wire_preserves_original_recipient_and_lifetime_book(self):
        observer,_=self.observer(with_nft=True);observer.primary_mint()
        self.assertEqual([],observer.errors)
        observed=self.chain['primary_mint']['observed']
        self.assertEqual([dict(address=addr(701),lifetime=1,allowlist=1)],observed['wallets'])
        self.assertEqual((1,1,addr(701),2),tuple(observed['ordinals'][0][key] for key in ('ordinal','reverse_ordinal','recipient','stage')))


if __name__=='__main__':unittest.main()
