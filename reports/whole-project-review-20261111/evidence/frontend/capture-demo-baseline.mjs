import {writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import * as domain from 'file:///C:/Users/Ali/Desktop/2.x%20holas/Oto/aaa-website/domain.js';
const digest=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const events=[{type:'claim',ids:[444]}, {type:'mint'},
 {type:'activate',id:1001,amount:100,pool:'ZZZ/WETH',fundingAsset:'USDC'},
 {type:'increase',id:1001,amount:0.01,fundingAsset:'USDG'},
 {type:'claim',ids:[128],scope:'all'}];
const original=domain.buildDemoCollection(), replay=domain.replayEvents(events);
const record={initial_sha256:digest(original),legacy_events:events,legacy_replay_sha256:digest(replay),
 original_metrics:domain.getMetrics(original),legacy_metrics:domain.getMetrics(replay),storage_key:domain.STORAGE_KEY};
await writeFile(new URL('./demo-baseline.json',import.meta.url),JSON.stringify(record,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({initial_sha256:record.initial_sha256,legacy_replay_sha256:record.legacy_replay_sha256,storage_key:record.storage_key}));
