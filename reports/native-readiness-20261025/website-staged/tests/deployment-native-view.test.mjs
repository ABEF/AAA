import test from 'node:test';
import assert from 'node:assert/strict';
import {contributionPolicyText,reviewedContributionPolicy} from '../deployment-view.js';

test('legacy contribution presentation retains its original one-percent policy',()=>{
  assert.equal(contributionPolicyText({schema:1}),'At least 99% must become added LP; network gas is separate.');
  assert.equal(reviewedContributionPolicy({minimum_deployed_usd_18:'99000000000000000000'}),'');
});
test('native form describes an approved ceiling without claiming it is the captured limit',()=>{
  const text=contributionPolicyText({schema:2,limits:{maximum_contribution_loss_bps:200}});
  assert.match(text,/up to 2% execution loss or undeployed value/);
  assert.match(text,/review verifies the current limit and added LP/);
  assert.match(text,/network gas is separate/);
  assert.match(contributionPolicyText({schema:2,limits:{maximum_contribution_loss_bps:0}}),/up to 0%/);
});
test('native review displays captured policy and the verified marginal LP floor, with no fixed 99 percent',()=>{
  const html=reviewedContributionPolicy({execution_limit_bps:200,reviewed_maximum_loss_bps:200,minimum_deployed_usd_18:'98000000000000000000'});
  assert.match(html,/2%/);assert.match(html,/Minimum added LP/);assert.match(html,/\$98\.00/);
  const tighter=reviewedContributionPolicy({execution_limit_bps:100,reviewed_maximum_loss_bps:100,minimum_deployed_usd_18:'99000000000000000000'});
  assert.match(tighter,/1%/);assert.match(tighter,/\$99\.00/);
});
test('missing, mismatched or injected native policy is never rendered as an approved review',()=>{
  for(const cap of [undefined,-1,1001,true,'200'])assert.throws(()=>contributionPolicyText({schema:2,limits:{maximum_contribution_loss_bps:cap}}));
  for(const patch of [{execution_limit_bps:-1},{reviewed_maximum_loss_bps:201},{minimum_deployed_usd_18:'1e20'},{minimum_deployed_usd_18:'<script>'}]){
    assert.throws(()=>reviewedContributionPolicy({execution_limit_bps:200,reviewed_maximum_loss_bps:200,minimum_deployed_usd_18:'98000000000000000000',...patch}));
  }
});
