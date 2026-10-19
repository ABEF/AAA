import {PALETTES,PATTERNS} from '/palette-system.js';
const $=s=>document.querySelector(s);
let state=null,session=null,busy=false,confirming=false,pending=null;
const pendingKey='popl-local-operation-v1';
const sumUSD=(a,b)=>a==null||b==null?null:(BigInt(a)+BigInt(b)).toString();
const dollars=raw=>raw===null?'Unavailable':new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'}).format(Number(BigInt(raw))/1e18);
const units=(raw,decimals=18)=>new Intl.NumberFormat('en-US',{maximumFractionDigits:8}).format(Number(BigInt(raw))/10**decimals);
const escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const balances=rows=>rows.filter(r=>BigInt(r.raw)>0n).map(r=>`${units(r.raw,r.decimals)} ${escape(r.symbol)}`).join(' + ')||'0';
function status(message,error=false){$('#status').textContent=message;$('#status').classList.toggle('error',error);}
function lock(value){busy=value;document.querySelectorAll('button,select,input').forEach(x=>x.disabled=value);}
async function request(path,body){const response=await fetch(path,{...(body?{method:'POST',headers:{'Content-Type':'application/json','X-Local-Token':session.token},body:JSON.stringify(body)}:{cache:'no-store'}),signal:AbortSignal.timeout(60000)});const result=await response.json();if(!response.ok){const error=new Error(result.error||'Local service unavailable');error.rejected=result.rejected===true;throw error;}return result;}
function forgetPending(){sessionStorage.removeItem(pendingKey);pending=null;}
async function settlePending(){
 try{const result=await request('/action',pending.envelope);if(result.status==='pending')throw new Error('Operation is unresolved. Inspect local operation records before continuing.');forgetPending();return result.status==='confirmed'?'Confirmed locally.':`Operation stopped: ${result.error}. ${result.transactions.length} transaction(s) confirmed; inspect receipts.`;}
 catch(error){if(error.rejected)forgetPending();throw error;}
}
function render(){
 const wallet=$('#account').value||state.accounts[0];
 $('#account').innerHTML=state.accounts.map((a,i)=>`<option value="${a}">${i?'Buyer':'Holder'} · ${a.slice(0,6)}…${a.slice(-4)}</option>`).join('');$('#account').value=wallet;
 const owned=state.nfts.filter(n=>n.owner===wallet);const lp=state.nfts.some(n=>n.position.current_lp_value.raw==null)?null:state.nfts.reduce((s,n)=>s+BigInt(n.position.current_lp_value.raw),0n).toString();const earned=state.earnings.all_time_usd_at_current_price_18;
 $('#metrics').innerHTML=`<div><span>Collection LP</span><strong>${dollars(lp)}</strong></div><div><span>Minted locally</span><strong>${state.nfts.length} / 1,000</strong></div><div><span>Funded LP fees</span><strong>${dollars(earned.lp_processed??null)}</strong></div><div><span>Your NFTs</span><strong>${owned.length}</strong></div>`;
 $('#snapshot').textContent=`Confirmed block ${state.nfts[0]?.provenance.block_number??'—'} · locally indexed`;
 $('#positions').innerHTML=owned.length?owned.map(n=>{
  const p=n.position,art=n.traits, palette=art?PALETTES[art.palette]:null, pattern=art?PATTERNS[art.pattern]:null;
  const image=art?`/assets/nfts/${palette.id}-${pattern.id}-${art.rarity.toLowerCase()}-${p.evolution}.svg`:null;
  const claims=n.previously_claimed.assets||[];const claimed=claims.filter(a=>BigInt(a.total_raw)>0n).map(a=>`${units(a.total_raw,a.decimals)} ${escape(a.symbol)}`).join(' + ')||'0';
  const any=[...n.claimable.lp,...n.claimable.royalties].some(x=>BigInt(x.raw)>0n);
  const history=n.earnings.all_time_usd_at_current_price_18;
  return `<article class="card"><div class="art">${image?`<img src="${image}" alt="${escape(palette.label+' '+art.rarity+' '+p.evolution)}">`:'Reveal pending'}</div><div class="body"><h3>Mint #${n.mint_ordinal}<span class="stage">${p.evolution}</span></h3><p class="traits">${art?`${art.rarity} · ${escape(palette.label)}<br>${escape(pattern.label)}`:'Original randomness request pending'}</p><div class="row principal"><span>LP attached · confirmed contract value</span><b>${dollars(p.current_lp_value.raw)}</b></div><div class="row"><span>LP fees to claim</span><b>${balances(n.claimable.lp)}</b></div><div class="row"><span>Royalties to claim · weight ×${p.royalty_weight}</span><b>${balances(n.claimable.royalties)}</b></div><div class="row"><span>Previously claimed · lifetime</span><b>${claimed}</b></div><div class="row"><span>LP fees earned · all time / 24h</span><b>${dollars(sumUSD(history.lp_individual,history.lp_collective))} / ${dollars(sumUSD(n.earnings.last_24h_usd_at_current_price_18.lp_individual,n.earnings.last_24h_usd_at_current_price_18.lp_collective))}</b></div><div class="contribute"><input aria-label="Test token contribution" type="number" min="100" max="99999" step="1" value="${p.activated?'1000':'100'}"><button data-action="${p.activated?'increase':'activate'}" data-id="${n.token_id}">${p.activated?'Add LP':'Activate'} ↗</button></div><div class="actions"><button data-action="claim" data-id="${n.token_id}" ${any?'':'disabled'}>Claim both</button><button class="secondary" data-action="transfer" data-id="${n.token_id}">Transfer →</button></div><p class="token-id" title="Full uint256 NFT identity">NFT ID ${n.token_id}</p></div></article>`;
 }).join(''):'<div class="empty">This wallet has no NFTs. Mint one or transfer a position from the other test wallet.</div>';
 $('#receipts').innerHTML=state.transactions.slice().reverse().map(t=>`<div class="receipt"><span>${escape(t.label)} · block ${t.block} · ${t.gas_used.toLocaleString()} gas</span><code>${t.hash}</code></div>`).join('');
}
async function refresh(){if(busy||confirming)return;lock(true);status('Reading confirmed contracts and indexed history…');try{session=await request('/session');pending=JSON.parse(sessionStorage.getItem(pendingKey)||'null');let message='Connected to the local test chain. No public funds are used.';if(pending&&pending.session!==session.token){forgetPending();message='New local session. Old operation was not replayed; earlier receipts remain in its session directory.';}if(pending)message=await settlePending();state=await request('/state');render();status(state.uncertain?'Submission outcome uncertain. Inspect saved receipts; new actions are stopped.':message,state.uncertain);}catch(e){status(e.message+' Refresh again to recover the same operation safely.',true);}finally{lock(false);if(state)render();}}
async function confirmAction(action){
 const messages={mint:['Mint a dormant NFT','Pay 0.05 test ETH. The local mock coordinator then reveals its fixed artwork.'],activate:['Activate this NFT','Approve the exact TEST-1 amount, then execute the real Activation Entry. At least 99% of the contribution must become LP; gas is separate.'],increase:['Add to attached LP','Approve the exact TEST-1 amount and add to the same shared LP allocation. Existing earnings stay attributed.'],claim:['Claim LP fees and royalties','Prepare and simulate one combined claim through the actual ClaimRouter. Payment goes to the current NFT owner.'],transfer:['Transfer to the other test wallet','The NFT, attached LP allocation and unclaimed fees/royalties move to the other disposable account.'],fund:['Fund both fee streams','The test operator funds 100 TEST-1 of local venue fees and 0.01 test ETH royalties. Real contracts allocate these amounts.'],rebalance:['Rebalance the shared LP','Advance the local test clock 10 minutes, change the approved range and rebalance once for the shared pool. NFT rights and unclaimed balances must persist.']};
 const [title,body]=messages[action];$('#confirm-title').textContent=title;$('#confirm-body').textContent=body;$('#confirm').returnValue='cancel';$('#confirm').showModal();return new Promise(resolve=>$('#confirm').addEventListener('close',()=>resolve($('#confirm').returnValue==='confirm'),{once:true}));
}
document.addEventListener('click',async e=>{
 const button=e.target.closest('[data-action]');if(!button||busy||confirming||!state||!session)return;
 if(pending){status('Refresh to recover the pending operation before starting another.',true);return;}
 if(state.uncertain){status('Inspect the uncertain submission records and restart the disposable lab.',true);return;}
 const action=button.dataset.action;const body={action,account:$('#account').value};if(button.dataset.id)body.id=button.dataset.id;
 if(action==='activate'||action==='increase'){const input=button.parentElement.querySelector('input');input.setCustomValidity(/^[1-9][0-9]{2,4}$/.test(input.value)?'':'Enter a whole amount from 100 to 99,999 without exponent notation.');if(!input.reportValidity())return;body.amount=input.value;}
 confirming=true;let accepted=false;try{accepted=await confirmAction(action);}finally{confirming=false;}if(!accepted)return;
 lock(true);status('Simulating and submitting local transactions…');
 try{pending={session:session.token,envelope:{operation_id:crypto.randomUUID().replaceAll('-',''),revision:state.revision,payload:body}};sessionStorage.setItem(pendingKey,JSON.stringify(pending));const message=await settlePending();state=await request('/state');render();status(message,message.startsWith('Operation stopped'));}
 catch(error){status(error.message+' Refresh to recover the outcome; do not submit a new action.',true);}
 finally{lock(false);if(state)render();}
});
$('#refresh').addEventListener('click',refresh);$('#account').addEventListener('change',()=>{if(state)render();});
await refresh();
