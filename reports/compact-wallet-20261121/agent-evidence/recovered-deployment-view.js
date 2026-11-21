import {DeploymentAPI,isAccounting7Profile,ZERO,raw,exactUnits,positionClaimEntries} from './deployment-api.js';
import {DeploymentSession} from './deployment-session.js';
import {DeploymentTransactions} from './deployment-transactions.js';
import {escape as e,usd,units} from './local-client.js';
import {rewardHistoryUSD,royaltyTrait} from './local-view.js';
import {COLORWAYS,PATTERNS,findArtwork,paletteTrait,preloadEvolutions} from './artworks.js';
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const text=(s,v)=>{const n=$(s);if(n)n.textContent=v;};
const short=a=>a.slice(0,6)+'…'+a.slice(-4);
// Match NFTMetadata._stageFile(4): LP-exited is labelled explicitly while its
// image uses the existing activated variant. No fifth artwork is invented.
export const positionArtwork=n=>n.ui_artwork_pending_unconfirmed!==true&&n.traits_ready===true&&(n.position.evolution_value_available===true||n.position.activated===true)?findArtwork(`${COLORWAYS[n.traits.palette]?.id}-${PATTERNS[n.traits.pattern]?.id}-${n.traits.rarity.toLowerCase()}-${n.position.evolution_value_available!==true||n.position.evolution==='lp_exited'?'activated':n.position.evolution}`):null;
export function positionEvolutionLabel(n){
  if(n.ui_artwork_pending_unconfirmed===true)return 'Awaiting confirmed LP execution';
  const p=n.position;
  if(p.activated===false&&n.lifecycle?.lp_exit_started===true)return 'Dormant · activation closed';
  if(p.evolution_value_available!==true)return p.activated===true?'Valuation unavailable · Activated fallback':'Valuation unavailable';
  if(p.evolution!=='lp_exited')return p.evolution;
  const r=n.principal_return;
  if(r?.available!==true||!Number.isSafeInteger(r.phase_code)||r.phase!==['operating','closing','allocating','ready'][r.phase_code]||
    typeof r.allocated!=='boolean'||typeof r.paid!=='boolean')return 'LP exited';
  if([1,2].includes(r.phase_code)&&r.allocated===false&&r.paid===false)return 'LP exited · allocation pending';
  if(![2,3].includes(r.phase_code)||r.allocated!==true||!Array.isArray(r.assets)||r.assets.length!==2||
    !r.assets.every(a=>['allocated_raw','remaining_raw'].every(k=>typeof a?.[k]==='string'&&/^(0|[1-9][0-9]*)$/.test(a[k]))))return 'LP exited';
  if(r.phase_code===3&&r.paid===true&&r.assets.every(a=>a.remaining_raw==='0'))return r.assets.every(a=>a.allocated_raw==='0')?'LP exited · no principal to return':'LP exited · principal paid';
  if(r.paid===false&&r.assets.every(a=>a.remaining_raw===a.allocated_raw))return r.assets.every(a=>a.allocated_raw==='0')?'LP exited · no principal to return':r.phase_code===2?'LP exited · distribution not ready':'LP exited · payout pending';
  return 'LP exited';
}
// This marker is local presentation state. It is never an RPC/accounting field.
export function holdPendingArtwork(nfts,pending,previousNfts=[]){
  const target=pending?.context?.intent?.id;
  if(typeof target!=='string'||!target||!['activate','increase'].includes(pending.context.action))return nfts;
  const previous=previousNfts.find(n=>n.token_id===target);
  return nfts.map(n=>n.token_id!==target?n:previous||{...n,ui_artwork_pending_unconfirmed:true,
    position:{...n.position,current_lp_value:{...n.position.current_lp_value,available:false,raw:null},evolution_value_available:false}});
}
export function walletProgressLabel(stage){
  return ({checking:'Checking review…',wallet:'Confirm in your wallet',submitted:'Transaction submitted',confirming:'Checking confirmation…',confirmed:'Transaction confirmed',failed:'Transaction reverted',reconciling:'Refreshing confirmed balances…'})[stage]||'Checking transaction status…';
}
// Only the original explicitly reviewed local profiles may construct the signer.
// Future read profiles do not inherit that capability by being non-production.
export function supportsLocalSigning(m){
  return [1,2,3].includes(m?.schema)&&m.environment==='rehearsal'&&m.chain_id===31337&&new URL(m.rpc_url).protocol==='http:'&&new URL(m.rpc_url).hostname==='127.0.0.1';
}
// A manifest is an approved ceiling; the captured on-chain cap is shown in review.
export function contributionPolicyText(manifest){
  if(manifest.schema<2)return 'At least 99% must become added LP; network gas is separate.';
  const cap=manifest.limits.maximum_contribution_loss_bps;
  if(!Number.isSafeInteger(cap)||cap<0||cap>1000)throw Error('Invalid reviewed contribution ceiling');
  return 'The reviewed deployment permits up to '+(cap/100)+'% execution loss or undeployed value. Your review verifies the current limit and added LP; network gas is separate.';
}
export function reviewedContributionPolicy(review){
  if(review.execution_limit_bps===undefined)return '';
  const cap=review.execution_limit_bps;
  if(!Number.isSafeInteger(cap)||cap<0||cap>1000||review.reviewed_maximum_loss_bps!==cap||
    !/^(0|[1-9][0-9]*)$/.test(review.minimum_deployed_usd_18||''))throw Error('Invalid reviewed LP execution policy');
  return `<div>Maximum execution loss / undeployed value <b>${e((cap/100).toString())}%</b></div><div>Minimum added LP <b>${e(usd(review.minimum_deployed_usd_18))}</b></div>`;
}
export function nativeRewards(n,scope){
  const locked=[4,5].includes(n.royalty_reporting?.schema)&&n.royalty_reporting.opening?.claims_open!==true;
  const rows=(scope?[scope]:['lp','royalties']).filter(k=>k!=='royalties'||!locked).flatMap(k=>n.claimable[k]).filter(a=>a.asset===ZERO);
  if(!rows.length||rows.some(a=>a.raw===null||a.available===false))return null;
  return rows.reduce((s,a)=>s+raw(a.raw),0n).toString();
}
export const hasClaimableRewards=n=>positionClaimEntries(n).length>0;
export function royaltyOpeningNote(n){
  if(![4,5].includes(n.royalty_reporting?.schema)||n.position?.activated===false)return '';
  const o=n.royalty_reporting.opening;
  if(!o||typeof o.claims_open!=='boolean')return '<p class="small-note">Royalty window status unavailable.</p>';
  if(o.claims_open)return '';
  if(!o.configured)return '<p class="small-note">Royalty sale closing time is not configured. LP rewards are separate.</p>';
  const t=o.claims_open_at;
  if(!Number.isSafeInteger(t)||t<=0||t>8640000000000)return '<p class="small-note">Royalty opening time unavailable.</p>';
  const date=new Date(t*1000).toISOString();
  return '<p class="small-note">Royalty claims open <time datetime="'+e(date)+'">'+e(date.replace('T',' ').replace('.000Z',' UTC'))+'</time>. LP rewards remain separate.</p>';
}
export function claimCurrencyButtons(n,disabled=false){
  if(![3,4,5].includes(n.royalty_reporting?.schema))return '';
  const assets=[...new Set(positionClaimEntries(n).map(c=>c.asset))];
  if(assets.length<2)return '';
  return '<p class="small-note">You can review currencies separately if one payout fails.</p><div class="local-position-actions">'+assets.map(asset=>{
    const row=[...n.claimable.lp,...n.claimable.royalties].find(a=>a.asset===asset);
    return '<button class="button button-secondary" data-deployment-claim="'+e(n.token_id)+'" data-deployment-claim-asset="'+e(asset)+'" '+(disabled?'disabled':'')+'>Claim '+e(row.symbol||'ETH')+'</button>';
  }).join('')+'</div>';
}
export function reviewedClaimPayouts(review){
  if(review.action!=='claim')return '';
  if(!Array.isArray(review.claims)||!review.claims.length)throw Error('Missing reviewed claim payouts');
  return '<div class="small-note">Simulated payouts · original currencies'+review.claims.map(c=>
    '<div>NFT '+e(c.token_id)+' · '+(c.royalty?'Royalties':'LP rewards')+' · '+e(exactUnits(c.simulated_raw,c.decimals))+' '+e(c.symbol)+'</div>'
  ).join('')+'</div>';
}
export function reviewedClaimPlan(review){
  const plan=review.claim_plan;if(!plan)return '';
  return '<div class="small-note"><p>Claim batch review · every selected entry</p>'+plan.entries.map(row=>
    '<div>NFT '+e(row.token_id)+' · '+(row.royalty?'Royalties':'LP rewards')+' · <span class="mono">'+e(row.asset)+'</span> · '+e(row.status)+'</div>'
  ).join('')+'<p>'+plan.remaining_claims.length+' entries remain outside this batch. Refresh and prepare again after confirmation; nothing is queued or sent automatically.</p></div>';
}
export function pendingLPText(n){
  if(n.provenance?.accounting_version!==7)return 'Additional source-token rewards await conversion or verification.';
  const row=n.claimable.lp.find(a=>a.asset!==ZERO);
  return row?.raw!==null&&row?.available!==false?'Pending LP conversion: '+exactUnits(row.raw,row.decimals)+' '+row.symbol+'. The conversion worker must credit ETH before the normal ETH reward claim.':'Pending LP conversion balance unavailable. No ETH amount is inferred.';
}
export function principalReturnNote(n){
  const r=n.principal_return;if(!r||r.phase==='operating')return '';
  if(!r.available)return '<p class="small-note">Principal return unavailable. This is separate from rewards.</p>';
  return '<div class="small-note"><p>Collective LP exit · '+e(r.phase)+(r.paid?' · paid':'')+'</p>'+r.assets.map(a=>
    '<div>Principal remaining · '+e(a.symbol)+': '+(a.remaining_raw===null?'Not allocated yet':e(exactUnits(a.remaining_raw,a.decimals)))+'</div>'
  ).join('')+'<p>Principal is separate from rewards. Governance distributes it to the current NFT owner. Previously earned rewards and royalties remain separate.</p></div>';
}
export function renderPositionAmounts(n){
  const lp=`<div class="position-attached-lp"><span>LP attached</span><strong>${e(usd(n.position.current_lp_value.raw))}</strong></div>`;
  if(!n.position.activated)return lp;
  const history=`<div class="position-earnings">${[['last_24h','24h'],['all_time','all time']].map(([key,label])=>`<div><span>Fees generated · ${label}</span><span class="earnings-value">${e(usd(rewardHistoryUSD(n,key)))}</span></div>`).join('')}</div>`;
  const original=[3,4,5].includes(n.royalty_reporting?.schema);
  const amount=nativeRewards(n),pending=['lp',...(original?[]:['royalties'])].some(k=>n.claimable[k].some(a=>a.asset!==ZERO&&(a.raw===null||raw(a.raw)>0n)));
  const extra=original?n.claimable.royalties.filter(a=>a.asset!==ZERO&&(a.raw===null||a.available===false||raw(a.raw)>0n)).map(a=>(a.raw===null||a.available===false?'Unavailable':exactUnits(a.raw,a.decimals))+' '+a.symbol):[];
  const originalNote=extra.length?'<p class="small-note">Other royalties to claim: '+extra.map(x=>e(x)).join(' + ')+'. Paid in their original currency.</p>':'';
  return lp+history+principalReturnNote(n)+`<div class="position-reward-total"><span>Rewards to claim</span><strong>${amount===null?'Unavailable':e(units(amount))+' ETH'}</strong></div>`+originalNote+royaltyOpeningNote(n)+(pending?'<p class="small-note">'+e(pendingLPText(n))+'</p>':'');
}
export function earnedUSD(report,period,collection=false){
  const totals=report?.[period+'_usd_at_current_price_18'];
  const fields=collection?['lp_owner_allocated','lp_collective_allocated','royalties_allocated']:['lp_individual','lp_collective','royalties'];
  if(!report?.available||!totals||fields.some(k=>totals[k]===null||totals[k]===undefined))return null;
  return fields.reduce((sum,k)=>sum+raw(totals[k]),0n).toString();
}
// Independent fixed-inventory financial branches: one request at a time each.
export async function loadWalletFinancials(api,inventory,{signal,onTotals,onEarnings}={}){
  const run=async(method,publish)=>{
    let value=null,error=null,failed=false;
    try{if(signal?.aborted)throw Error('Wallet financial read was cancelled');value=await api[method](inventory,{signal});}
    catch(reason){failed=true;error=reason;}
    if(!signal?.aborted)publish?.({value,error});
    if(failed)throw error;return value;
  };
  return Promise.allSettled([run('walletTotals',onTotals),run('walletEarnings',onEarnings)]);
}
export function createDeploymentView(config){
  const link=document.createElement('link');link.rel='stylesheet';link.href='./local-view.css';document.head.append(link);
  const bar=document.createElement('div');bar.className='container local-status';bar.innerHTML='<span role="status">Checking reviewed deployment…</span><button type="button" class="text-link" data-deployment-refresh>Refresh ↻</button>';document.querySelector('main').before(bar);
  const status=(message,error=false)=>{bar.querySelector('span').textContent=message;bar.classList.toggle('is-error',error);};
  // Configuration failures never fall back to invented portfolio data.
  let api;try{api=new DeploymentAPI(config);}catch(error){
    document.querySelector('main').innerHTML='<section class="container app-view"><h1>Deployment configuration unavailable</h1><p>Account data and transaction preparation are disabled.</p></section>';
    status(error.message,true);$$('[data-connect]').forEach(b=>b.disabled=true);
    const noop=()=>{};return {updateWallet:noop,renderPortfolio:noop,renderMetrics:noop,renderCollection:noop,openWallet:noop,refresh:noop,setProviders:noop,renderMint:noop,failed:true};
  }
  const m=api.manifest,dialog=document.createElement('dialog');dialog.className='dialog local-confirm';dialog.setAttribute('aria-label','Unsigned transaction review');document.body.append(dialog);
  let providers=[],snapshot=null,readiness=null,page=0,sequence=0,busy=false,preparing=false,error=null,quoteSequence=0;
  let store=null;try{store=sessionStorage;}catch{}
  let transactions=null,review=null,stage=null,reviewTimer=null;
  const localSigning=supportsLocalSigning(m);
  const session=new DeploymentSession({storage:store,key:'popl-deployment-address:'+m.id,onChange:()=>{
    sequence++;quoteSequence++;page=0;totalController?.abort();totalController=null;totals=null;totalBusy=false;earnings=null;earningsBusy=false;renderMetrics();review=null;api.cancel();snapshot=null;busy=false;preparing=false;error=null;dialog.close();$('#nft-dialog').close();render();
    if(!session.busy&&session.account)void refresh();
  }});
  if(localSigning)transactions=new DeploymentTransactions(api,session,{onChange:()=>render(),onProgress:value=>{
    stage=value.stage;
    const messages={checking:'Checking the reviewed transaction…',wallet:'Confirm in your selected wallet.',submitted:'Transaction sent. Waiting for confirmation…',confirming:'Checking the saved transaction on-chain…',confirmed:'Transaction confirmed. Refreshing confirmed balances…',failed:'Transaction reverted. No LP change was applied.',reconciling:'Transaction confirmed. Checking confirmed balances…'};
    status(messages[value.stage]||'Checking transaction status…');
    text('.local-confirm [data-deployment-progress]',messages[value.stage]||'Checking transaction status…');
    const send=dialog.querySelector('[data-deployment-send]');if(send){send.textContent=walletProgressLabel(value.stage);send.hidden=['submitted','confirming','confirmed','failed','reconciling'].includes(value.stage);}
    render();
  }});
  const recovery=document.createElement('button');recovery.type='button';recovery.className='text-link';recovery.dataset.deploymentRecover='';recovery.textContent='Recover saved transaction ↻';recovery.hidden=true;bar.append(recovery);
  const network=document.createElement('button');network.type='button';network.className='text-link';network.dataset.deploymentNetwork='';network.textContent='Switch to '+m.chain_name;network.hidden=true;bar.append(network);
  function pending(){if(!transactions||!session.account||!session.provider)return null;try{return transactions.pending();}catch(err){status(err.message,true);return {invalid:true};}}
  const stale=()=>!snapshot||Math.floor(Date.now()/1000)-snapshot.protocol.provenance.block_timestamp>m.max_age_seconds;
  const blocked=()=>busy||preparing||transactions?.busy||Boolean(pending())||session.busy||!session.account||stale();
  text('.network-tag',m.chain_name+(localSigning?' · local wallet rehearsal':' · read & review'));text('.demo-label',localSigning?'LOCAL ANVIL':'UNSIGNED REVIEW');
  text('.demo-banner-copy',localSigning?'Local Anvil transactions only. No public assets move.':'Confirmed contract data and unsigned preparation. Signing is not enabled.');
  text('[data-view="my-nfts"] .page-heading .eyebrow','YOUR PERMANENT POSITIONS');
  text('[data-view="my-nfts"] .page-heading p:last-of-type','Your confirmed holdings, attached LP and funded rewards.');
  text('#portfolio-disconnected > p:last-of-type','Connect a wallet to read its public holdings on '+m.chain_name+'. No signature or transaction is requested.');
  text('#wallet-dialog > .small-note',localSigning?'Connect your account; every local transaction requires a separate wallet confirmation.':'Only your public account is authorized. This deployment profile cannot sign or send transactions.');
  text('#nft-dialog .eyebrow','CONFIRMED POSITION');
  text('.portfolio-footnote p','Each card shows its confirmed snapshot. Earnings include LP and royalties at reviewed current prices; unavailable prices are not zero.');
  $('#reset-demo').hidden=true;$('#demo-wallet').hidden=true;
  // Collection-wide aggregation is not supplied by the wallet-ID endpoint. Do
  // not disguise the current eight-card page as the entire collection/wallet.
  $$('#portfolio-connected .metric-grid,.collection-analytics,.collection-filters,[data-view="collection"] .pagination,#collection-activity-summary').forEach(n=>n.hidden=true);
  const pager=document.createElement('div');pager.className='local-actions';pager.innerHTML='<button class="button button-secondary" data-deployment-page="-1">Previous</button><span role="status"></span><button class="button button-secondary" data-deployment-page="1">Next</button>';$('#owned-nfts').after(pager);
  function walletOptions(){
    $('#wallet-providers').innerHTML=providers.map((p,i)=>`<button class="wallet-option" data-deployment-provider="${i}" ${session.busy?'disabled':''}><span>◇</span><span>${e(p.name)}</span><span>→</span></button>`).join('')+(session.options.length>1?'<p>Select the account to view:</p>'+session.options.map(a=>`<button class="wallet-option local-id" data-deployment-account="${a}">${a}</button>`).join(''):'');
    text('#wallet-message',session.busy?'Authorize address access in your wallet.':session.account?'Selected: '+session.account:providers.length?'Choose a wallet, then select an authorized account.':'No wallet detected. Enable an Ethereum-compatible wallet extension.');
    $('#wallet-connected-actions').hidden=!session.account;
    text('#connected-wallet-description',session.account||'');
  }
  function updateWallet(){
    $$('[data-connect]').forEach(b=>b.textContent=session.account?short(session.account):'Connect wallet ↗');
    renderMint();if($('#wallet-dialog').open)walletOptions();
  }
  function renderMint(){
    const button=$('#mint-submit');if(!button)return;
    if(isAccounting7Profile(m)||m.environment==='production'){button.type='button';button.disabled=true;button.textContent='Mint on OpenSea';text('#mint-message','Minting takes place on OpenSea. Collection eligibility and the verified mint link are not configured here.');return;}
    button.type='button';button.disabled=busy||preparing||transactions?.busy||Boolean(pending())||session.busy||Boolean(readiness?.new_minting_stopped)||readiness?.minted>=1000;
    button.textContent=transactions?.busy?(review?.requested_action==='mint'?(stage==='wallet'?'Confirm mint in wallet…':'Checking mint confirmation…'):'Wallet operation in progress…'):preparing?'Preparing review…':busy?'Reading confirmed state…':session.account?(localSigning?'Review mint ↗':'Review unsigned mint ↗'):'Connect wallet ↗';
    text('#mint-message','0.05 ETH mint price. Network gas is separate. '+(localSigning?'Local Anvil only; confirm each send in your wallet.':'This profile does not submit transactions.'));
    if(readiness){text('#mint-supply',readiness.minted+' / 1,000');text('#mint-remaining',(1000-readiness.minted)+' remaining');}
  }
  let totals=null,totalController=null,totalBusy=false,earnings=null,earningsBusy=false,collection=null,collectionBusy=false,collectionController=null,collectionSequence=0,collectionPositions=null,collectionPositionsBusy=false,collectionProgress='',collectionPage=0,collectionDetailSequence=0;
  const totalsFrame=document.createElement('div');totalsFrame.className='metric-grid deployment-wallet-totals';
  totalsFrame.innerHTML='<article><span class="stat-label">LP ATTACHED · ALL YOUR NFTs</span><strong data-wallet-total="lp">Unavailable</strong><span data-wallet-total-note></span></article><article class="claim-metric"><span class="stat-label">READY TO CLAIM · ETH</span><strong data-wallet-total="eth">Unavailable</strong><span>LP rewards + royalties · source tokens excluded</span></article>';
  totalsFrame.insertAdjacentHTML('beforeend','<article><span class="stat-label">EARNINGS · LAST 24H</span><strong data-wallet-earned="last_24h">Unavailable</strong><span>LP rewards + royalties · current prices</span></article><article><span class="stat-label">EARNINGS · ALL TIME</span><strong data-wallet-earned="all_time">Unavailable</strong><span>History of currently held NFTs, including past owners</span></article>');
  $('#portfolio-connected .portfolio-account').after(totalsFrame);
  const collectionFrame=document.createElement('div');collectionFrame.className='metric-grid deployment-collection-earnings';
  collectionFrame.innerHTML='<article><span class="stat-label">HOLDER ALLOCATIONS · LAST 24H</span><strong data-collection-earned="last_24h">Unavailable</strong></article><article><span class="stat-label">HOLDER ALLOCATIONS · ALL TIME</span><strong data-collection-earned="all_time">Unavailable</strong></article><p class="small-note" data-collection-earned-note></p>';
  $('[data-view="collection"] .collection-filters').before(collectionFrame);
  const collectionTotals=document.createElement('div');collectionTotals.className='metric-grid';
  collectionTotals.innerHTML='<article><span class="stat-label">TOTAL ATTACHED LP</span><strong data-collection-total>Unavailable</strong><span>Current on-chain value · all NFTs</span></article><article><span class="stat-label">ACTIVATED / MINTED</span><strong data-collection-count>Unavailable</strong><span data-collection-snapshot></span></article>';
  for(const frame of [collectionTotals,collectionFrame])frame.style.gridTemplateColumns='repeat(auto-fit,minmax(min(100%,260px),1fr))';
  const allocationNote=collectionFrame.querySelector('[data-collection-earned-note]');
  $('[data-view="collection"] .positions-section').before(collectionTotals,collectionFrame,allocationNote);
  text('[data-view="collection"] .page-heading > a','Mint preview ↗');
  const collectionPager=document.createElement('div');collectionPager.className='local-actions';collectionPager.innerHTML='<button class="button button-secondary" data-collection-page="-1">Previous</button><span role="status"></span><button class="button button-secondary" data-collection-page="1">Next</button>';
  $('#positions-body').closest('.table-scroll').after(collectionPager);
  $('[data-view="collection"] > .metric-grid').hidden=true;$('.collection-filters').hidden=false;
  const columns=$$('[data-view="collection"] thead th');['NFT / STATUS','OWNER','ATTACHED LP','EVOLUTION','View position'].forEach((v,i)=>columns[i].textContent=v);
  $('#sort-positions option[value="fees"]').disabled=true;
  for(const selector of ['#nft-search','#status-filter','#sort-positions','#rarity-filter','#color-filter','#color-style-filter'])$(selector).addEventListener(selector==='#nft-search'?'input':'change',()=>{collectionPage=0;renderCollection();});
  function renderMetrics(){
    $$('[data-metric]').forEach(n=>n.textContent='Unavailable');
    for(const period of ['all_time','last_24h'])text(`[data-wallet-earned="${period}"]`,earningsBusy?'Reading earnings…':usd(earnedUSD(earnings,period)));
    text('[data-wallet-total="lp"]',totalBusy?'Reading all holdings…':usd(totals?.lp_usd_18??null));
    text('[data-wallet-total="eth"]',totalBusy?'Reading all holdings…':totals?.claimable_eth_wei!=null?units(totals.claimable_eth_wei)+' ETH':'Unavailable');
    text('[data-wallet-total-note]',totals?`${totals.count} NFTs · confirmed block ${totals.provenance.block_number}`:'Complete confirmed wallet snapshot required');
  }
  async function refreshTotals(data,current,owner){
    totalController?.abort();totalController=new AbortController();const controller=totalController;totalBusy=true;totals=null;earnings=null;earningsBusy=true;renderMetrics();
    const currentRead=()=>totalController===controller&&current===sequence&&owner===session.account&&!controller.signal.aborted;
    if(data.financials){
      if(currentRead()){totals=data.financials.totals;earnings=data.financials.earnings;totalBusy=false;earningsBusy=false;renderMetrics();}return;
    }
    await loadWalletFinancials(api,data.inventory,{signal:controller.signal,
      onTotals:({value})=>{if(currentRead()){totals=value;totalBusy=false;renderMetrics();}},
      onEarnings:({value})=>{if(currentRead()){earnings=value;earningsBusy=false;renderMetrics();}}});
  }
  async function refreshCollection(){
    collectionController?.abort();const controller=new AbortController(),revision=++collectionSequence;collectionController=controller;collectionBusy=true;collection=null;collectionPositions=null;collectionPositionsBusy=true;collectionProgress='';collectionPage=0;collectionDetailSequence++;renderCollection();
    const earningsRead=(async()=>{try{const result=await api.collectionEarnings({signal:controller.signal});if(revision===collectionSequence&&!controller.signal.aborted)collection=result;}catch{}finally{if(revision===collectionSequence){collectionBusy=false;renderCollection();}}})();
    try{const result=await api.collectionPositions({signal:controller.signal,onProgress:(done,total)=>{if(revision===collectionSequence&&!controller.signal.aborted){collectionProgress=`${done} / ${total} confirmed positions`;renderCollection();}}});if(revision===collectionSequence&&!controller.signal.aborted)collectionPositions=result;}
    catch{if(revision===collectionSequence)collectionProgress='Collection unavailable. Refresh to read a complete confirmed snapshot.';}
    finally{if(revision===collectionSequence){collectionPositionsBusy=false;renderCollection();}}
    await earningsRead;
  }
  function renderCollection(){
    for(const period of ['all_time','last_24h'])text(`[data-collection-earned="${period}"]`,collectionBusy?'Reading allocations…':usd(earnedUSD(collection,period,true)));
    text('[data-collection-earned-note]',collection?`LP holder + collective allocations and allocated royalties at current prices · block ${collection.provenance.block_number}. Includes ledger rounding dust; excludes compounding, buyback and quarantined funds. Earnings already claimed remain included.`:'Complete confirmed history and reviewed prices required.');
    text('[data-collection-total]',collectionPositionsBusy?'Reading collection…':usd(collectionPositions?.lp_usd_18??null));
    text('[data-collection-count]',collectionPositions?`${collectionPositions.activated} / ${collectionPositions.count}`:'Unavailable');
    text('[data-collection-snapshot]',collectionPositions?`${collectionPositions.dormant} dormant · block ${collectionPositions.provenance.block_number}`:collectionProgress);
    let rows=collectionPositions?.positions||[];
    const q=$('#nft-search').value.trim().slice(0,78).replace(/^#/,'').toLowerCase(),filter=selector=>$(selector).value;
    rows=rows.filter(n=>{const art=n.traits_ready?findArtwork(`${COLORWAYS[n.traits.palette]?.id}-${PATTERNS[n.traits.pattern]?.id}-${n.traits.rarity.toLowerCase()}-dormant`):null;
      return (!q||String(n.mint_ordinal).includes(q)||n.token_id.includes(q))&&(filter('#status-filter')==='all'||(filter('#status-filter')==='active')===n.position.activated)&&(filter('#rarity-filter')==='all'||n.traits?.rarity.toLowerCase()===filter('#rarity-filter'))&&(filter('#color-style-filter')==='all'||art?.colorStyle.toLowerCase()===filter('#color-style-filter'))&&(filter('#color-filter')==='all'||COLORWAYS[n.traits?.palette]?.colors.some(c=>c.toLowerCase()===filter('#color-filter')));});
    const mode=filter('#sort-positions');rows.sort((a,b)=>mode==='liquidity'?a.position.current_lp_value.raw===null&&b.position.current_lp_value.raw===null?a.mint_ordinal-b.mint_ordinal:a.position.current_lp_value.raw===null?1:b.position.current_lp_value.raw===null?-1:raw(a.position.current_lp_value.raw)>raw(b.position.current_lp_value.raw)?-1:raw(a.position.current_lp_value.raw)<raw(b.position.current_lp_value.raw)?1:a.mint_ordinal-b.mint_ordinal:mode==='newest'?b.mint_ordinal-a.mint_ordinal:a.mint_ordinal-b.mint_ordinal);
    const pages=Math.max(1,Math.ceil(rows.length/16));collectionPage=Math.min(collectionPage,pages-1);
    $('#positions-body').innerHTML=rows.slice(collectionPage*16,collectionPage*16+16).map(n=>{const art=artFor(n);return `<tr><td><button class="text-link" data-collection-id="${n.token_id}">${art?`<img src="${e(art.src)}" alt="" width="42" height="42" loading="lazy">`:''} PoPL #${n.mint_ordinal}</button><span class="small-note">${e(n.position.status)}</span></td><td><span class="mono" title="${e(n.owner)}">${e(short(n.owner))}</span></td><td>${e(usd(n.position.current_lp_value.raw))}</td><td>${e(positionEvolutionLabel(n))}</td><td><button class="icon-button" data-collection-id="${n.token_id}" aria-label="View PoPL #${n.mint_ordinal}">↗</button></td></tr>`;}).join('')||`<tr><td colspan="5">${e(collectionPositionsBusy?collectionProgress||'Reading the confirmed collection…':collectionPositions?'No matching positions.':collectionProgress||'Collection unavailable.')}</td></tr>`;
    text('#result-count',collectionPositions?`${rows.length} matching / ${collectionPositions.count} NFTs`:collectionProgress||'Collection not loaded');
    collectionPager.hidden=!collectionPositions||rows.length<=16;collectionPager.querySelector('span').textContent=`Page ${collectionPage+1} of ${pages}`;
    collectionPager.querySelector('[data-collection-page="-1"]').disabled=collectionPage===0;
    collectionPager.querySelector('[data-collection-page="1"]').disabled=collectionPage+1>=pages;
  }
  async function collectionDetails(id){
    const row=collectionPositions?.positions.find(n=>n.token_id===id);if(!row)return;
    const revision=++collectionDetailSequence;status('Reading the current confirmed position…');
    try{const n=await api.nft(id,row.owner,collectionController?.signal);if(revision!==collectionDetailSequence||location.hash!=='#collection')return;
      $('#nft-dialog-content').innerHTML=`<h2>PoPL #${n.mint_ordinal}</h2><p class="small-note">${e(positionEvolutionLabel(n))}</p><div class="nft-card-traits">${traits(n)}</div><p class="small-note">Owner ${e(n.owner)} · confirmed block ${n.provenance.block_number}</p>${renderPositionAmounts(n)}`;
      $('#nft-dialog').showModal();status('Current confirmed position loaded.');
    }catch{if(revision===collectionDetailSequence)status('Position changed or could not be verified. Refresh the collection.',true);}
  }
  const artFor=positionArtwork;
  function traits(n){const art=artFor(n);return n.traits_ready?`<strong>${e(n.traits.rarity)}</strong><span>${e(art?.colorStyle||'')}</span>${paletteTrait(COLORWAYS[n.traits.palette].colors)}${royaltyTrait(n)}`:'<span>Awaiting verified reveal</span>';}
  function renderPortfolio(){
    $('#portfolio-disconnected').hidden=Boolean(session.account);$('#portfolio-connected').hidden=!session.account;
    text('#portfolio-address',session.account?short(session.account):'');text('#portfolio-label',busy?'READING CONFIRMED STATE':localSigning?'LOCAL ANVIL':'UNSIGNED REVIEW');
    text('.portfolio-account .small-note',snapshot?'Holdings at block '+snapshot.inventory.provenance.block_number:'Confirmed holdings unavailable');
    const items=snapshot?.nfts||[];
    text('#my-count',snapshot?`${snapshot.inventory.count} NFTs owned · showing ${items.length} on this page`:'');
    $('#owned-nfts').innerHTML=items.map(n=>{const art=artFor(n);if(art)preloadEvolutions(art);return `<article class="nft-card"><div class="nft-card-art">${art?`<button class="art-image-button" data-deployment-id="${n.token_id}" aria-label="View PoPL #${n.mint_ordinal}"><img class="nft-artwork" src="${art.src}" alt="${e(art.colorLabel+' '+art.rarityLabel+' '+positionEvolutionLabel(n))}" width="1024" height="1024" loading="lazy"></button>`:'<div class="local-art-unavailable">Artwork state unavailable</div>'}</div><div class="nft-card-body"><div class="nft-card-title"><h3>PoPL #${n.mint_ordinal}</h3><span>${e(positionEvolutionLabel(n))}</span></div><div class="nft-card-traits">${traits(n)}</div>${renderPositionAmounts(n)}<div class="local-position-actions">${n.position.activated?`<button class="button" data-deployment-claim="${n.token_id}" ${blocked()||!hasClaimableRewards(n)?'disabled':''}>Review claim</button>`:''}<button class="button button-secondary" data-deployment-id="${n.token_id}" data-deployment-grow ${blocked()||!n.traits_ready||isAccounting7Profile(m)&&(!snapshot.protocol.lifecycle.new_economic_work_available_by_lifecycle||!['active','dormant'].includes(n.position.status))?'disabled':''}>${n.position.activated?'Grow attached LP':'Activate'}</button></div><p class="small-note">Confirmed block ${n.provenance.block_number}</p></div></article>`;}).join('')||`<p class="local-empty">${e(busy?'Reading your confirmed positions…':error||'No NFTs owned by this address.')}</p>`;
    $('#claim-all').disabled=blocked()||!items.some(n=>hasClaimableRewards(n));text('#claim-all','Review claims on this page ↗');
    pager.hidden=!snapshot||snapshot.inventory.count<=8;pager.querySelector('span').textContent=`Page ${page+1}`;
    pager.querySelector('[data-deployment-page="-1"]').disabled=busy||page===0;
    pager.querySelector('[data-deployment-page="1"]').disabled=busy||!snapshot||(page+1)*8>=snapshot.inventory.count;
  }
  function render(){updateWallet();renderPortfolio();recovery.hidden=!pending();recovery.disabled=Boolean(transactions?.busy);network.hidden=!localSigning||!session.account;network.disabled=Boolean(transactions?.busy)||Boolean(pending());}
  async function refresh({keepDialog=false}={}){
    if(transactions?.busy)return;const current=++sequence,owner=session.account;api.cancel();totalController?.abort();totalController=null;totals=null;totalBusy=false;earnings=null;earningsBusy=false;renderMetrics();busy=true;error=null;if(!keepDialog){review=null;dialog.close();}render();
    try{
      const ready=[1,2,3].includes(m.schema)&&m.environment==='rehearsal'?await api.readiness():null;if(current!==sequence)return;readiness=ready;
      const data=owner?await api.portfolio(owner,page):(await api.protocol(),null);
      if(current!==sequence||owner!==session.account)return;// A refresh must not publish a pending contribution's new artwork before
      // its canonical Entry receipt and LP position have been reconciled.
      if(data)data.nfts=holdPendingArtwork(data.nfts,pending(),snapshot?.nfts||[]);
      snapshot=data;if(data&&!pending())void refreshTotals(data,current,owner);status(pending()?'A saved transaction needs recovery. Check its status before a new review.':localSigning?'Confirmed data loaded. Local Anvil wallet ready.':'Confirmed data loaded. Review only; no transactions can be sent.');
    }catch(err){if(current!==sequence)return;error=err.message;snapshot=null;status(error,true);}
    finally{if(current===sequence){busy=false;render();}}
  }
  function openWallet(){text('#wallet-title','Connect to view your holdings.');text('#wallet-dialog .dialog-intro','Choose a wallet and account. Reads use the reviewed '+m.chain_name+' deployment.');walletOptions();if(!$('#wallet-dialog').open)$('#wallet-dialog').showModal();}
  async function connect(index){if(session.busy)return;const p=providers[index];if(!p)return;try{await session.connect(p);if(session.account)$('#wallet-dialog').close();}catch(err){text('#wallet-message',err.code===4001?'Connection cancelled. No transaction was requested.':err.message);status('Wallet connection was not completed.',true);}}
  async function quote(form){
    const generation=++quoteSequence,current=sequence;form.elements.amount.value='';form.elements.consent.checked=false;form.querySelector('button[type=submit]').disabled=true;
    text('#nft-dialog [data-deployment-feedback]','Reading the reviewed activation price…');
    try{const result=await api.activationAmount(form.elements.asset.value);if(generation!==quoteSequence||current!==sequence||!form.isConnected||!$('#nft-dialog').open)return;
      form.elements.amount.value=result.amount;form.querySelector('button[type=submit]').disabled=false;text('#nft-dialog [data-deployment-feedback]',(result.minimum_activation_usd_18?'Reviewed activation target '+usd(result.minimum_activation_usd_18):'$100 in value')+', rounded up only to the smallest token unit. Rechecked during preparation.');
    }catch(err){if(generation===quoteSequence&&form.isConnected)text('#nft-dialog [data-deployment-feedback]',err.message);}
  }
  function details(id,grow=false){
    if(blocked())return void refresh();const n=snapshot.nfts.find(n=>n.token_id===id);if(!n)return;
    if(grow&&isAccounting7Profile(m)&&(!snapshot.protocol.lifecycle.new_economic_work_available_by_lifecycle||!['active','dormant'].includes(n.position.status)))return;
    quoteSequence++;const action=n.position.activated?'increase':'activate',assets=m.input_assets.filter(a=>a.enabled);
    const balance=scope=>{const amount=nativeRewards(n,scope);return amount===null?'Unavailable':units(amount)+' ETH';};
    $('#nft-dialog-content').innerHTML=`<h2 id="nft-details-title">PoPL #${n.mint_ordinal}</h2><p class="small-note">${e(positionEvolutionLabel(n))}</p><div class="nft-card-traits">${traits(n)}</div>${renderPositionAmounts(n)}${!grow&&n.position.activated?`<div class="breakdown-rows"><div>LP rewards <span>${e(balance('lp'))}</span></div><div>Royalties <span>${e(balance('royalties'))}</span></div></div>`:''}${!grow&&n.position.activated?claimCurrencyButtons(n,blocked()):''}${grow?`<form data-deployment-contribution="${id}" data-action="${action}" class="liquidity-form"><label class="input-label">Contribution asset<select name="asset">${assets.map(a=>`<option value="${a.symbol}">${a.symbol}</option>`).join('')}</select></label><label class="input-label">Token amount<input class="amount-input" name="amount" type="text" inputmode="decimal" autocomplete="off" required ${action==='activate'?'readonly':''}></label><p class="small-note">${isAccounting7Profile(m)?'The current governed and pool minimums are checked in your review.':action==='activate'?'Activate with $100 in value.':'Add at least $5 in value.'} ${e(contributionPolicyText(m))}</p><label class="checkbox-label"><input name="consent" type="checkbox" required><span>I understand this funds LP attached to the NFT and the principal cannot be redeemed.</span></label><button type="submit" class="button" ${assets.length?'':'disabled'}>${localSigning?'Review':'Prepare unsigned'} ${action==='activate'?'activation':'LP addition'} ↗</button><p class="form-message" data-deployment-feedback role="status"></p></form>`:''}`;
    $('#nft-dialog').showModal();const form=$('[data-deployment-contribution]');if(grow&&action==='activate'&&assets.length)void quote(form);
  }
  async function prepare(intent,{afterApproval=false}={}){
    if(preparing||transactions?.busy)return;if(!session.account)return openWallet();if(pending())return void recover();if(stale()&&!afterApproval)return void refresh();
    preparing=true;updateWallet();const current=sequence;
    try{
      const permission=await session.verify();const draft=transactions?await transactions.prepare({...intent,account:permission.account},{afterApproval}):await api.prepare({...intent,account:permission.account,...(isAccounting7Profile(m)&&intent.action==='claim'?{plan:true}:{})});await session.verify();
      if(current!==sequence||permission.revision!==session.revision||permission.account!==session.account)return;
      const labels={mint:'Mint',claim:'Claim rewards in original currencies',approve:'Approve exact contribution',activate:'Activate NFT',increase:'Grow attached LP'};
      review=draft;stage=null;const context=draft.liquidity_context;
      if(!draft.transaction){dialog.innerHTML='<h2>Claim review</h2>'+reviewedClaimPlan(draft)+'<p>No executable transaction was prepared. Nothing is sent.</p><button type="button" class="button button-secondary" data-deployment-close>Close</button>';dialog.showModal();status('Claim selection reviewed; no executable batch.');return;}
      dialog.innerHTML=`<h2>${e(labels[draft.action])}</h2><p class="eyebrow">${localSigning?'LOCAL WALLET REVIEW':'UNSIGNED REVIEW'} · ${e(m.chain_name)}</p><p>${localSigning?'Nothing is sent until you confirm in the selected wallet.':'This profile cannot send transactions. Nothing has been approved or transferred.'}</p><div class="nft-detail-rewards"><div>Account <b class="local-id">${e(permission.account)}</b></div><div>Destination <b class="local-id">${e(draft.transaction.to)}</b></div>${draft.source?`<div>Contribution <b>${e(exactUnits(draft.source.amount_raw,api.asset(intent.asset).decimals))} ${e(intent.asset)}</b></div>`:`<div>Native value <b>${e(exactUnits(BigInt(draft.transaction.value).toString(),18))} ETH</b></div>`}${reviewedContributionPolicy(draft)}${reviewedClaimPayouts(draft)}${reviewedClaimPlan(draft)}${draft.simulated_lp_added_usd_18?`<div>Simulated LP added <b>${e(usd(draft.simulated_lp_added_usd_18))}</b></div>`:''}<div>Network gas · separate review limit <b>${e(exactUnits(draft.network_gas.max_cost_wei,18))} ETH</b></div></div>${draft.action==='approve'?'<p>Approval alone adds no liquidity. After a confirmed approval, the complete Entry operation must be prepared again.</p>':''}${context?.in_range===false?'<p class="is-error">The LP is outside its active trading range. '+e(String(context.rebalance?.explanation||'Next eligible rebalance unavailable.').slice(0,600))+' Next keeper execution is not guaranteed.</p>':''}<p role="status" data-deployment-expiry>Review expires at ${e(new Date(draft.expires_at*1000).toLocaleTimeString())}.</p><details><summary>Exact unsigned calldata</summary><code>${e(draft.transaction.data)}</code></details><p role="status" data-deployment-progress></p>${draft.signing_enabled?'<button type="button" class="button" data-deployment-send>Confirm in your wallet</button>':''}<button type="button" class="button button-secondary" data-deployment-close>Close</button>`;
      clearTimeout(reviewTimer);dialog.showModal();const timer=setTimeout(()=>{if(dialog.open&&!transactions?.busy){text('[data-deployment-expiry]','This review has expired. Prepare again using current confirmed state.');const send=dialog.querySelector('[data-deployment-send]');if(send)send.disabled=true;}},Math.max(0,draft.expires_at*1000-Date.now()));reviewTimer=timer;dialog.addEventListener('close',()=>clearTimeout(timer),{once:true});
      status(localSigning?'Review ready. Confirm in your wallet to send the local transaction.':'Unsigned review prepared. Signing remains disabled.');
    }catch(err){if(current===sequence){status(err.message,true);text('#nft-dialog [data-deployment-feedback]',err.message);}}
    finally{if(current===sequence){preparing=false;updateWallet();}}
  }
  function resultDialog(result){
    clearTimeout(reviewTimer);
    const complete=result.reconciled,confirmed=result.status==='confirmed';
    const title=complete?(confirmed?'Transaction confirmed':'Transaction reverted'):confirmed?'Confirmed · balances catching up':result.reason==='nonce_gap'?'Transaction waiting for earlier activity':result.reason==='review_nonce_changed'?'Wallet changed the transaction number':'Check transaction status';
    const message=result.error||(complete?(confirmed?'Confirmed contract state is ready to refresh.':'The operation reverted; network gas may have been spent.'):'Check the same saved transaction. Do not submit it again.');
    dialog.innerHTML=`<h2>${e(title)}</h2><p role="status" data-deployment-progress>${e(message)}</p>${result.hash?`<p class="local-id">Transaction: ${e(result.hash)}</p>`:''}${!complete&&!result.hash?'<label>Transaction hash from your wallet<input class="amount-input" data-deployment-hash autocomplete="off" placeholder="0x…"></label>':''}${complete?'':'<button class="button" data-deployment-recover>Recover status</button>'}<button class="button button-secondary" data-deployment-close>Close</button>`;
    if(!dialog.open)dialog.showModal();
  }
  async function finish(result,current){
    if(current!==sequence)return;
    if(result.status==='none'){dialog.close();await refresh();return;}
    if(result.reconciled&&result.status==='confirmed'&&result.action==='approve'){
      // Keep the dialog open, but ask for a fresh complete Entry review. No send.
      dialog.innerHTML='<h2>Approval confirmed</h2><p>Preparing the LP transaction. Approval alone adds no liquidity.</p><button class="button button-secondary" data-deployment-close>Close</button>';
      await prepare(result.intent,{afterApproval:true});return;
    }
    resultDialog(result);
    if(result.reconciled){review=null;$('#nft-dialog').close();await refresh({keepDialog:true});}
  }
  async function submit(){
    if(!transactions||!review||transactions.busy)return;const current=sequence,selected=review;clearTimeout(reviewTimer);text('[data-deployment-send]',walletProgressLabel('checking'));text('[data-deployment-progress]','Checking the reviewed transaction…');
    dialog.querySelectorAll('button').forEach(b=>b.disabled=!b.matches('[data-deployment-close]'));
    try{await finish(await transactions.submit(selected),current);}
    catch(err){if(current!==sequence)return;status(err.message,true);
      if(pending())resultDialog({status:'unresolved',hash:pending()?.hash,error:err.message});
      else {review=null;dialog.innerHTML=`<h2>${err.rejected?'Transaction cancelled':'Transaction not sent'}</h2><p>${e(err.message)}</p><p>Refresh balances before preparing a new review.</p><button class="button button-secondary" data-deployment-close>Close</button>`;}}
    finally{stage=null;render();}
  }
  async function recover(){
    if(!transactions||transactions.busy||!session.account)return;const current=sequence;
    const hashInput=dialog.querySelector('[data-deployment-hash]')?.value.trim();
    dialog.querySelectorAll('button').forEach(b=>b.disabled=!b.matches('[data-deployment-close]'));
    try{await finish(await transactions.recover(hashInput||undefined),current);}
    catch(err){if(current===sequence){status(err.message,true);resultDialog({status:'unresolved',hash:pending()?.hash,error:err.message});}}
    finally{stage=null;render();}
  }
  async function switchNetwork(){try{await transactions?.switchNetwork();status('Selected network verified. Refresh and prepare a new review.');await refresh();}catch(err){status(err.code===4001?'Network switch cancelled.':err.message,true);}}
  document.addEventListener('click',event=>{
    const b=event.target.closest('button');if(!b||!b.matches('[data-collection-page],[data-collection-id],[data-connect],[data-deployment-provider],[data-deployment-account],[data-deployment-refresh],[data-deployment-id],[data-deployment-claim],[data-deployment-page],[data-deployment-close],[data-deployment-send],[data-deployment-recover],[data-deployment-network],#mint-submit,#disconnect-wallet,#claim-all,#demo-wallet,#reset-demo'))return;
    event.preventDefault();event.stopImmediatePropagation();
    if(b.matches('[data-deployment-send]'))return void submit();
    if(b.matches('[data-deployment-recover]'))return void recover();
    if(b.matches('[data-deployment-network]'))return void switchNetwork();
    if(b.matches('[data-connect]'))return openWallet();
    if(b.matches('[data-deployment-provider]'))return void connect(Number(b.dataset.deploymentProvider));
    if(b.matches('[data-deployment-account]'))return void session.select(b.dataset.deploymentAccount).then(()=>$('#wallet-dialog').close()).catch(err=>status(err.message,true));
    if(b.matches('[data-collection-page]')){collectionPage=Math.max(0,collectionPage+Number(b.dataset.collectionPage));return renderCollection();}
    if(b.matches('[data-collection-id]'))return void collectionDetails(b.dataset.collectionId);
    if(b.matches('[data-deployment-refresh]')){if(location.hash==='#collection')void refreshCollection();return void refresh();}
    if(b.matches('[data-deployment-close]')){review=null;dialog.close();return;}
    if(b.matches('[data-deployment-id]'))return details(b.dataset.deploymentId,b.hasAttribute('data-deployment-grow'));
    if(b.matches('[data-deployment-claim]')){$('#nft-dialog').close();return void prepare({action:'claim',ids:[b.dataset.deploymentClaim],...(b.dataset.deploymentClaimAsset?{claim_assets:[b.dataset.deploymentClaimAsset]}:{})});}
    if(b.matches('[data-deployment-page]')){page+=Number(b.dataset.deploymentPage);return void refresh();}
    if(b.id==='disconnect-wallet'){session.disconnect();$('#wallet-dialog').close();return;}
    if(b.id==='mint-submit'){if(!session.account)return openWallet();if(!$('#mint-form').reportValidity())return;return void prepare({action:'mint'});}
    if(b.id==='claim-all')return void prepare({action:'claim',ids:(snapshot?.nfts||[]).filter(n=>hasClaimableRewards(n)).map(n=>n.token_id)});
  },true);
  document.addEventListener('submit',event=>{const f=event.target;if(!f.matches('[data-deployment-contribution]'))return;event.preventDefault();event.stopImmediatePropagation();if(!f.reportValidity())return;void prepare({action:f.dataset.action,id:f.dataset.deploymentContribution,amount:f.elements.amount.value,asset:f.elements.asset.value});},true);
  document.addEventListener('change',event=>{const f=event.target.closest('[data-deployment-contribution]');if(!f||event.target.name!=='asset')return;f.elements.consent.checked=false;if(f.dataset.action==='activate')void quote(f);});
  window.addEventListener('hashchange',()=>{if(location.hash==='#collection')void refreshCollection();else {collectionSequence++;collectionDetailSequence++;collectionController?.abort();collectionController=null;collection=null;collectionPositions=null;collectionBusy=false;collectionPositionsBusy=false;collectionProgress='';renderCollection();}quoteSequence++;review=null;dialog.close();$('#nft-dialog').close();});
  window.addEventListener('pagehide',()=>{sequence++;api.cancel();totalController?.abort();collectionSequence++;collectionController?.abort();dialog.close();});
  if(location.hash==='#collection')void refreshCollection();
  return {updateWallet,renderPortfolio,renderMetrics,renderCollection,renderMint,openWallet,refresh,setProviders:items=>{providers=items;walletOptions();void session.restore(items);}};
}
