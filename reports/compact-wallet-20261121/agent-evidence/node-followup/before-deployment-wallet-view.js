// Read-only compact wallet assembly. Never publishes an incomplete currency sum.
const gates=new Map();
const wait=(ms,signal)=>new Promise((resolve,reject)=>{
  const abort=()=>{clearTimeout(timer);signal?.removeEventListener('abort',abort);reject(Error('Wallet read cancelled'));};
  const timer=setTimeout(()=>{signal?.removeEventListener('abort',abort);resolve();},ms);
  if(signal?.aborted)abort();else signal?.addEventListener('abort',abort,{once:true});
});
export class WalletReadGate {
  constructor({clock=()=>performance.now(),sleep=wait}={}){this.clock=clock;this.sleep=sleep;this.next=0;this.tail=Promise.resolve();this.queued=0;}
  run(work,signal){
    if(this.queued>=32)return Promise.reject(Error('Too many wallet reads. Finish or cancel the current read.'));
    this.queued++;
    const job=this.tail.then(async()=>{
      if(signal?.aborted)throw Error('Wallet read cancelled');
      let now=this.clock();if(!Number.isFinite(now))throw Error('Wallet read clock unavailable');
      if(now<this.next)await this.sleep(this.next-now,signal);
      if(signal?.aborted)throw Error('Wallet read cancelled');
      now=this.clock();if(!Number.isFinite(now)||now<this.next)throw Error('Wallet read scheduler clock differs');
      this.next=now+1000;return work();
    }).finally(()=>{this.queued--;});
    this.tail=job.catch(()=>{});return job;
  }
}
export function sharedReadGate(key){
  if(!gates.has(key)){if(gates.size>=32)throw Error('Too many wallet service origins');gates.set(key,new WalletReadGate());}
  return gates.get(key);
}
const canonical=value=>JSON.stringify(Array.isArray(value)?value.map(ordered):ordered(value));
function ordered(value){return value&&typeof value==='object'&&!Array.isArray(value)?Object.fromEntries(Object.keys(value).sort().map(k=>[k,ordered(value[k])])):Array.isArray(value)?value.map(ordered):value;}
const digest=async values=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(values.join(','))))].map(v=>v.toString(16).padStart(2,'0')).join('');

export async function readCompactWallet(api,owner,anchor,{signal,lifecycle}={},h){
  const {raw,fail,clone,integer,object,ADDRESS,HASH,DIGEST}=h,m=api.manifest,revision=api.revision;
  if(!ADDRESS.test(owner)||owner==='0x'+'0'.repeat(40)||!object(anchor)||anchor.accounting_version!==7)fail('Invalid compact wallet request');
  anchor=clone(anchor);lifecycle=lifecycle===undefined?undefined:clone(lifecycle);
  const assets=[...m.reward_assets].sort((a,b)=>a.address<b.address?-1:a.address>b.address?1:0),assetIds=assets.map(a=>a.address),assetDigest=await digest(assetIds);
  const controller=new AbortController(),abort=()=>controller.abort(),expires=(anchor.block_timestamp+m.max_age_seconds)*1000;
  if(signal?.aborted)controller.abort();else signal?.addEventListener('abort',abort,{once:true});
  const active=()=>{if(controller.signal.aborted||signal?.aborted||api.revision!==revision)fail('Wallet read cancelled or superseded');const now=api.clock();if(!Number.isFinite(now)||now>=expires||anchor.block_timestamp>Math.floor(now/1000)+30)fail('Confirmed wallet snapshot expired. Refresh holdings.');};
  let timer,first,earnings=null,earningsError=null,lp=0n,eth=0n,lpOk=true,ethOk=true,ids=[];
  const fields=['lp_individual','lp_collective','royalties'];
  try{
    active();timer=setTimeout(abort,expires-api.clock());await api.provenance(anchor);active();
    const page=async(offset,assetOffset)=>{
      active();let part;
      try{part=await api.request(`/v1/wallets/${owner}/view/${anchor.block_number}/${offset}/${assetOffset}`,undefined,controller.signal);}
      catch(error){if(assetOffset>0&&(error?.status===429||error?.status===503&&error.apiCode==='service_busy'))error.currencyReadUnavailable=true;throw error;}active();
      const p=part.provenance,history=part.history;
      if(part.schema!==1||part.kind!=='fixed_block_wallet_view_page'||part.available!==true||part.chain_id!==m.chain_id||part.wallet!==owner||part.nft_contract!==m.contracts.nft.address||!integer(part.count,0,1000)||part.offset!==offset||part.chunk_size!==16||!DIGEST.test(part.inventory_sha256)||!Array.isArray(part.token_ids)||part.token_ids.some((id,i)=>raw(id)===0n||i&&raw(part.token_ids[i-1])>=raw(id)))fail('Invalid compact wallet ownership');
      const size=Math.min(16,part.count-offset),next=offset+size<part.count?offset+size:null;
      if(size<0||offset>=part.count&&!(offset===0&&part.count===0)||part.token_ids.length!==size||part.verified_count!==size||part.complete!==(offset===0&&size===part.count)||part.next_offset!==next)fail('Incomplete compact NFT page');
      if(!object(p)||p.block_number!==anchor.block_number||p.block_hash!==anchor.block_hash||p.block_timestamp!==anchor.block_timestamp||p.configuration_sha256!==m.projection_sha256||p.accounting_version!==7||p.finality!=='confirmation_depth_only'||p.protocol_finalized!==false||p.eip1898_require_canonical!==true)fail('Compact wallet snapshot differs');
      if(!object(history)||history.available!==true||!integer(history.from_block,0,anchor.block_number)||!HASH.test(history.start_block_hash)||!HASH.test(history.start_parent_hash)||history.through_block!==anchor.block_number||history.block_hash!==anchor.block_hash||!integer(history.indexer_next_block,anchor.block_number+1,Number.MAX_SAFE_INTEGER))fail('Compact wallet history is incomplete');
      if(!object(part.lifecycle)||typeof part.lifecycle.new_economic_work_available_by_lifecycle!=='boolean'||lifecycle!==undefined&&canonical(part.lifecycle)!==canonical(lifecycle))fail('Compact wallet lifecycle differs');
      if(first&&(part.count!==first.count||part.inventory_sha256!==first.inventory_sha256||canonical(part.lifecycle)!==canonical(first.lifecycle)||history.from_block!==first.history.from_block||history.start_block_hash!==first.history.start_block_hash||history.start_parent_hash!==first.history.start_parent_hash))fail('Compact wallet inventory changed');
      const selected=assets.slice(assetOffset,assetOffset+4),assetNext=assetOffset+selected.length<assets.length?assetOffset+selected.length:null;
      if(part.asset_chunk_size!==4||part.asset_offset!==assetOffset||part.asset_count!==assets.length||part.asset_inventory_sha256!==assetDigest||canonical(part.asset_ids)!==canonical(assetIds)||canonical(part.selected_asset_ids)!==canonical(selected.map(a=>a.address))||part.next_asset_offset!==assetNext)fail('Compact currency inventory or cursor differs');
      const section=value=>{if(!object(value)||value.schema!==1||value.chain_id!==m.chain_id||value.wallet!==owner||value.nft_contract!==m.contracts.nft.address||value.count!==part.count||value.inventory_sha256!==part.inventory_sha256||value.offset!==offset||value.chunk_size!==16||value.next_offset!==next||canonical(value.token_ids)!==canonical(part.token_ids)||!object(value.provenance)||value.provenance.block_number!==anchor.block_number||value.provenance.block_hash!==anchor.block_hash||value.provenance.block_timestamp!==anchor.block_timestamp||value.provenance.configuration_sha256!==m.projection_sha256||canonical(value.lifecycle)!==canonical(part.lifecycle))fail('Compact financial section differs');};
      if(assetOffset===0){
        section(part.summary);
        if(!part.count&&[part.summary.lp_usd_18,part.summary.claimable_eth_wei].some(v=>v!==null&&raw(v)!==0n))fail('Empty wallet cannot have positive totals');
      }else if(part.summary!==null)fail('Repeated compact wallet totals');
      if(part.earnings!==null){
        section(part.earnings);
        for(const key of ['asset_chunk_size','asset_offset','asset_count','asset_inventory_sha256','asset_ids','selected_asset_ids','next_asset_offset'])if(canonical(part.earnings[key])!==canonical(part[key]))fail('Compact earnings currency identity differs');
        if(part.earnings_error!==null)fail('Contradictory compact earnings status');
        api.validateEarnings(part.earnings,'wallet_chunk',selected);
        if(!part.count&&['all_time','last_24h'].some(period=>part.earnings[period].some(row=>fields.some(k=>raw(row[k+'_raw'])!==0n))))fail('Empty wallet cannot have earnings');
      }else if(part.earnings_error!=='earnings_unavailable')fail('Missing compact earnings status');
      await api.provenance(p);active();return part;
    };
    first=await page(0,0);
    const pages=Math.max(1,Math.ceil(first.count/16)),tiles=Math.ceil(assets.length/4);
    // A lower bound only: preserve ownership/totals when complete earnings cannot
    // fit even ideal self-paced reads. Never publish a subset as complete history.
    const remaining=expires-api.clock(),fullPossible=(pages*tiles-1+16)*1000<remaining;
    if(!fullPossible)earningsError='Complete currency history exceeds this snapshot read window.';
    let offset=0;
    do{
      const initial=offset===0?first:await page(offset,0),selectedIds=initial.token_ids;
      ids.push(...selectedIds);
      if(initial.summary.lp_usd_18===null)lpOk=false;else lp+=raw(initial.summary.lp_usd_18);
      if(initial.summary.claimable_eth_wei===null)ethOk=false;else eth+=raw(initial.summary.claimable_eth_wei);
      let assetOffset=0,part=initial;
      do{
        if(canonical(part.token_ids)!==canonical(selectedIds))fail('NFT selection changed between currency pages');
        if(part.earnings===null)earningsError='Complete earnings are temporarily unavailable.';
        else if(!earningsError){
          if(!earnings)earnings={...clone(part.earnings),all_time:[],last_24h:[]};
          for(const period of ['all_time','last_24h'])for(const row of part.earnings[period]){
            const prior=earnings[period].find(r=>r.asset===row.asset);
            if(!prior)earnings[period].push(clone(row));
            else{if(canonical(prior.current_price)!==canonical(row.current_price))fail('Earnings prices changed between NFT pages');for(const field of fields)prior[field+'_raw']=(raw(prior[field+'_raw'])+raw(row[field+'_raw'])).toString();}
          }
        }
        assetOffset=fullPossible&&!earningsError?part.next_asset_offset:null;
        if(assetOffset!==null){
          try{part=await page(offset,assetOffset);}
          catch(error){active();if(error?.currencyReadUnavailable!==true)throw error;earningsError='Complete earnings are temporarily unavailable.';assetOffset=null;}
        }
      }while(assetOffset!==null);
      offset=initial.next_offset;
    }while(offset!==null);
    if(ids.length!==first.count||ids.some((id,i)=>i&&raw(ids[i-1])>=raw(id))||await digest(ids)!==first.inventory_sha256)fail('Incomplete compact wallet inventory');active();
    if(earningsError)earnings=null;
    if(earnings){
      for(const period of ['all_time','last_24h']){
        if(canonical(earnings[period].map(r=>r.asset).sort())!==canonical(assetIds))fail('Incomplete compact earnings currencies');
        const totals=Object.fromEntries(fields.map(k=>[k,0n]));
        for(const row of earnings[period])for(const field of fields){
          const amount=raw(row[field+'_raw']),price=row.current_price;
          const value=price.available?amount*raw(price.usd_per_token_18)/10n**BigInt(row.decimals):amount===0n?0n:null;
          row.usd_at_current_price_18[field]=value===null?null:value.toString();totals[field]=totals[field]===null||value===null?null:totals[field]+value;
        }
        earnings[period+'_usd_at_current_price_18']=Object.fromEntries(fields.map(k=>[k,totals[k]===null?null:totals[k].toString()]));
      }
      delete earnings.offset;delete earnings.next_offset;delete earnings.chunk_size;
      for(const key of ['asset_offset','asset_count','asset_chunk_size','asset_ids','selected_asset_ids','asset_inventory_sha256','next_asset_offset'])delete earnings[key];
      earnings.scope='wallet';earnings.token_ids=[...ids];
    }
    await api.provenance(anchor);active();await api.identity();active();
    return {inventory:{schema:2,chain_id:m.chain_id,available:true,wallet:owner,nft_contract:m.contracts.nft.address,count:ids.length,token_ids:ids,complete:true,inventory_sha256:first.inventory_sha256,provenance:first.provenance,history:first.history,lifecycle:first.lifecycle},
      totals:{available:true,count:ids.length,wallet:owner,lp_usd_18:lpOk?lp.toString():null,claimable_eth_wei:ethOk?eth.toString():null,provenance:anchor},earnings,earnings_error:earningsError};
  }finally{clearTimeout(timer);controller.abort();signal?.removeEventListener('abort',abort);}
}
