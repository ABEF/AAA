"""Typed confirmation drafts for the launcher-owned disposable Anvil only."""
import secrets
import time
from scripts.local_inputs import input_for, input_tx

UNIT = 10**18

class LocalWallet:
    def __init__(self, lab):
        self.lab = lab
        self.drafts = {}
        self.wrapped = set()

    def prepare(self, payload):
        lab = self.lab
        # Reuse the strict typed boundary; never accept arbitrary calldata.
        lab.validate_wallet_action(payload)
        if payload['action'] not in ('mint', 'activate', 'increase', 'claim', 'claim_all', 'transfer'):
            raise ValueError('This action is not a holder transaction')
        if lab.uncertain:
            raise ValueError('Submission state is uncertain; inspect records before restarting the lab')
        lab.sync()
        owner, action = payload['account'], payload['action']
        identifier = payload.get('id')
        if identifier:
            if identifier not in lab.ids() or lab.addr('nft', 'ownerOf(uint256)', identifier) != owner:
                raise ValueError('Selected local wallet does not own this NFT')
        details = []
        if action == 'mint':
            if lab.uint('nft', 'mintedCount()') >= 20:
                raise ValueError('Local fixture capped at 20 NFTs')
            draft = lab.preparer.prepare({'action': 'mint', 'wallet': owner})
            tx = {k:v for k,v in draft['transaction'].items() if k != 'chainId'}
        elif action in ('claim', 'claim_all'):
            candidates = [identifier] if action == 'claim' else [i for i in lab.ids() if lab.addr('nft','ownerOf(uint256)',i) == owner]
            claims = []
            count = 0
            for candidate in candidates:
                item = lab.api.nft(candidate)
                entries = [{'token_id':candidate,'asset':a['asset'],'royalty':scope=='royalties'}
                           for scope in ('lp','royalties') for a in item['claimable'][scope] if int(a['raw']) > 0]
                if entries:
                    if count == 10 or len(claims)+len(entries) > 32:break
                    claims.extend(entries);count+=1
            draft = lab.preparer.prepare({'action':'claim', 'wallet':owner, 'claims':claims})
            tx = {k:v for k,v in draft['transaction'].items() if k != 'chainId'}
            details = draft['claim_operations']
            action = 'claim'
        elif action == 'transfer':
            other = next(a for a in lab.accounts[1:] if a != owner)
            tx = {'from':owner, 'to':lab.contracts['nft'], 'value':'0x0',
                  'data':lab.encode('transferFrom(address,address,uint256)',owner,other,identifier)}
        else:
            protocol = lab.api.protocol()
            if not protocol['lifecycle']['new_economic_work_available_by_lifecycle']:
                raise ValueError('New contributions are unavailable in the current lifecycle')
            source=input_for(lab,payload.get('asset'))
            value=int(payload['amount']);amount=value*10**source['decimals']
            native=source['symbol']=='ETH'
            token=lab.weth if native else source['address']
            active = bool(lab.uint('vault','nftBucket(uint256)',identifier))
            if active != (action == 'increase'):
                raise ValueError('NFT activation state changed; refresh')
            wrap_key=(owner,identifier,payload['amount'])
            if native and wrap_key not in self.wrapped:
                if len(self.wrapped)>=32:raise ValueError('Finish a pending ETH contribution before wrapping more')
                action='wrap'
                tx={'from':owner,'to':token,'value':hex(amount),'data':lab.encode('deposit()')}
            elif lab.uint(token,'balanceOf(address)',owner) < amount:
                raise ValueError('Insufficient '+source['symbol']+' local balance')
            elif lab.uint(token,'allowance(address,address)',owner,lab.contracts['entry']) < amount:
                action = 'approve'
                # Reset a prior smaller allowance, then request exactly the selected input.
                allowance=lab.uint(token,'allowance(address,address)',owner,lab.contracts['entry'])
                approved=0 if allowance else amount
                tx = {'from':owner,'to':token,'value':'0x0',
                      'data':lab.encode('approve(address,uint256)',lab.contracts['entry'],approved)}
            else:
                tx = input_tx(lab,owner,identifier,value,action == 'increase',payload.get('asset'))
        tx, gas = lab.simulate(tx)
        # Bounded expiring drafts. Consumed IDs cannot be made live again.
        now = time.monotonic()
        self.drafts = {key:item for key,item in self.drafts.items() if item['deadline'] > now}
        if len(self.drafts) >= 32:
            raise ValueError('Too many outstanding confirmations; wait one minute')
        key = secrets.token_hex(16)
        result = {'draft_id':key, 'action':action, 'requested_action':payload['action'],
                  'account':owner, 'chain_id':31337, 'revision':lab.operations.revision,
                  'transaction':tx, 'network_gas':gas, 'claims':details,
                  'expires_in_seconds':60, 'contribution':payload.get('amount'),
                  'contribution_asset':source['symbol'] if payload['action'] in ('activate','increase') else None,
                  'approval_raw':str(approved) if action=='approve' else None,
                  'approval_asset':('WETH' if source['symbol']=='ETH' else source['symbol']) if action=='approve' else None,
                  'minimum_lp_usd_18':str(int(payload['amount'])*UNIT*99//100) if 'amount' in payload else None}
        self.drafts[key] = {'public':result, 'payload':dict(payload), 'deadline':now+60,
                            'chain_deadline':lab.clock()+60, 'used':False}
        return result

    def execute(self, payload):
        lab = self.lab
        item = self.drafts.get(payload['draft_id'])
        if not item or item['used']:
            raise ValueError('Confirmation is missing or already consumed; refresh')
        draft = item['public']
        if (payload['account'] != draft['account'] or lab.operations.revision != draft['revision']
                or time.monotonic() >= item['deadline'] or lab.clock() >= item['chain_deadline']):
            raise ValueError('Confirmation expired or account/state changed; prepare again')
        # A second owner check applies even to approval, whose calldata alone
        # would not reject a transferred NFT. No hidden approval+Entry sequence.
        identifier = item['payload'].get('id')
        if identifier and lab.addr('nft','ownerOf(uint256)',identifier) != payload['account']:
            raise ValueError('NFT ownership changed; refresh')
        item['used'] = True
        lab.send(draft['transaction'], 'website '+draft['action'], approved=True)
        key=(payload['account'],identifier,item['payload'].get('amount'))
        if draft['action']=='wrap':self.wrapped.add(key)
        elif draft['action'] in ('activate','increase'):self.wrapped.discard(key)
        if draft['action'] == 'mint':
            count = lab.uint('nft','mintedCount()')
            identifier = lab.uint('nft','tokenAtOrdinal(uint256)',count)
            lab.call(lab.vrf,'fulfill(uint256,uint256,uint256)',lab.uint('nft','requestOf(uint256)',identifier),count*721,12345)
            lab.call('nft','finalizeTraits(uint256)',identifier)
