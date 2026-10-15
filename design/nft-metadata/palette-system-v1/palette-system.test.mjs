import test from 'node:test';
import assert from 'node:assert/strict';
import {
  COLORS,COLOR_STYLES,PATTERNS,RARITIES,PALETTES,PREVIEW_SEED,
  BICOLOR_ANCHORS,TRICOLOR_ADDITIONS,isAllowedBicolor,isAllowedTricolor,
  canonicalColors,paletteForColors,buildInventory,validateInventory,
  traitsForTokenId,baseDesignId,artworkId,metadataAttributes,
  encodeArtworkTraits,decodeArtworkTraits,inventoryCodesByRarity,
} from './palette-system.mjs';

test('fixed eight-color catalogue preserves existing hues and names warm neutral colors',() => {
  assert.equal(COLORS.length,8);
  assert.equal(COLORS.find(color => color.id === 'amber').accent,'#ffbf59');
  assert.equal(COLORS.find(color => color.id === 'crimson').accent,'#ff5378');
  assert.equal(COLORS.find(color => color.id === 'ivory').accent,'#f2e9d8');
  assert.equal(COLORS.find(color => color.id === 'onyx').accent,'#171c24');
  assert.deepEqual(PATTERNS.map(pattern => pattern.id),['arcs','panels','orbits','ribs']);
});
test('canonical catalogue contains eight mono, 22 bicolor and 28 tricolor unordered palettes',() => {
  assert.deepEqual(COLOR_STYLES.map(style => PALETTES.filter(palette => palette.colorStyle === style.id).length),[8,22,28]);
  assert.equal(new Set(PALETTES.map(palette => palette.id)).size,58);
  for (const palette of PALETTES) assert.deepEqual(palette.colorIds,canonicalColors(palette.colorIds));
  assert.equal(paletteForColors(['crimson','cyan']).id,paletteForColors(['cyan','crimson']).id);
});
test('every distinct pair with Ivory, Amber, Crimson or Onyx is allowed; no other pair is silently admitted',() => {
  for (const left of COLORS) for (const right of COLORS) {
    const expected = left.id !== right.id && [left.id,right.id].some(id => BICOLOR_ANCHORS.includes(id));
    assert.equal(isAllowedBicolor([left.id,right.id]),expected);
    if (left.id !== right.id) assert.equal(Boolean(paletteForColors([left.id,right.id])),expected);
  }
  assert.equal(isAllowedBicolor(['cyan','blue']),false);
  assert.equal(isAllowedBicolor(['unknown','amber']),false);
});
test('tricolor is exactly an allowed pair plus a distinct Amber, Crimson or Onyx',() => {
  const derived = new Set();
  for (const pair of PALETTES.filter(palette => palette.colorStyle === 'bicolor')) {
    for (const extra of TRICOLOR_ADDITIONS) if (!pair.colorIds.includes(extra)) {
      derived.add(canonicalColors([...pair.colorIds,extra]).join('-'));
    }
  }
  assert.deepEqual([...derived].sort(),PALETTES.filter(palette => palette.colorStyle === 'tricolor').map(palette => palette.id).sort());
  assert.equal(isAllowedTricolor(['cyan','ivory','amber']),true);
  assert.equal(isAllowedTricolor(['cyan','blue','amber']),false);
  assert.equal(isAllowedTricolor(['cyan','amber','amber']),false);
  assert.equal(isAllowedTricolor(['cyan','ivory','onyx']),true);
});
test('fixed inventory has exact rarity/style quotas, 542 finished looks and at most four identical artworks',() => {
  const inventory = buildInventory();
  assert.deepEqual(validateInventory(inventory),{
    supply:1000,rarities:{commun:600,rare:300,legendary:100},
    styles:{monochrome:200,bicolor:500,tricolor:300},uniqueBaseDesigns:542,maximumIdenticalArtwork:4,
  });
  const legend = inventory.filter(entry => entry.rarity === 'legendary');
  assert.equal(new Set(legend.map(baseDesignId)).size,100);
});
test('balanced palette access and duplicate guarantees survive 64 different fixture seeds',() => {
  for (let seed=0; seed<64; seed++) assert.equal(validateInventory(buildInventory(`fixture-${seed}`)).supply,1000);
});
test('fixture generation is repeatable, seed-sensitive and never labelled cryptographic randomness',() => {
  assert.deepEqual(buildInventory(),buildInventory(PREVIEW_SEED));
  assert.notDeepEqual(buildInventory(),buildInventory('another-fixture'));
  assert.throws(() => buildInventory(''),/seed/);
});
test('stable NFT traits survive all four visual evolution states without adding minted tokens',() => {
  const traits = traitsForTokenId(1);
  for (const stage of ['dormant','activated','enhanced','singularity']) {
    const attributes = metadataAttributes(traits,stage);
    assert.equal(attributes.find(item => item.trait_type === 'Rarity').value,RARITIES.find(item => item.id === traits.rarity).label);
    assert.equal(attributes.find(item => item.trait_type === 'Evolution').value.toLowerCase(),stage);
    assert.ok(artworkId(traits,stage).endsWith(stage));
    assert.equal(attributes.filter(item => item.trait_type.startsWith('Color ')).length,traits.colorIds.length+1);
  }
  assert.throws(() => artworkId(traits,'elite'),/evolution/);
});
test('callers cannot modify default inventory through returned color arrays',() => {
  const traits = traitsForTokenId(1); const original = [...traits.colorIds];
  traits.colorIds[0] = 'unknown';
  assert.deepEqual(traitsForTokenId(1).colorIds,original);
  for (const id of [0,1001,-1,1.5,NaN]) assert.throws(() => traitsForTokenId(id),/Token ID/);
});
test('validation rejects unknown traits, repeated colors, invalid supply and quota tampering',() => {
  assert.throws(() => canonicalColors(['cyan','cyan']),/distinct/);
  assert.throws(() => canonicalColors(['purple']),/known/);
  assert.throws(() => validateInventory(buildInventory().slice(1)),/supply/);
  for (const modification of [
    entry => entry.rarity='unknown', entry => entry.colorStyle='tricolor',
    entry => entry.colorIds=['cyan','cyan'], entry => entry.pattern='none',
    entry => entry.tokenId=999,
  ]) {
    const inventory = buildInventory(); modification(inventory[0]);
    assert.throws(() => validateInventory(inventory));
  }
});
test('complete-artwork duplicate protection catches a fifth identical look',() => {
  const inventory = buildInventory();
  const counts = new Map();
  for (const entry of inventory) counts.set(baseDesignId(entry),(counts.get(baseDesignId(entry))||0)+1);
  const duplicate = inventory.find(entry => counts.get(baseDesignId(entry)) === 4);
  const source = inventory.find(entry => entry.rarity === 'commun' && baseDesignId(entry) !== baseDesignId(duplicate));
  Object.assign(source,{...duplicate,tokenId:source.tokenId,colorIds:[...duplicate.colorIds]});
  assert.throws(() => validateInventory(inventory),/repetition/);
});
test('all 232 packed palette/pattern codes round-trip without collisions',() => {
  const codes = new Set();
  for (const palette of PALETTES) for (const pattern of PATTERNS) {
    const traits = {paletteId:palette.id,pattern:pattern.id};
    const code = encodeArtworkTraits(traits); codes.add(code);
    const decoded = decodeArtworkTraits(code);
    assert.equal(decoded.paletteId,palette.id);
    assert.equal(decoded.pattern,pattern.id);
    assert.deepEqual(decoded.colorIds,palette.colorIds);
  }
  assert.equal(codes.size,232);
  for (const bad of [-1,232,NaN,1.5]) assert.throws(() => decodeArtworkTraits(bad),/code/);
  assert.throws(() => encodeArtworkTraits({paletteId:'none',pattern:'arcs'}),/unknown/);
});
test('per-rarity production catalogue exactly preserves the fixed visual inventory',() => {
  const inventory = buildInventory(); const codes = inventoryCodesByRarity(inventory);
  for (const rarity of RARITIES) {
    assert.equal(codes[rarity.id].length,rarity.supply);
    const source = inventory.filter(entry => entry.rarity === rarity.id);
    for (let index=0; index<source.length; index++) assert.equal(codes[rarity.id][index],encodeArtworkTraits(source[index]));
  }
});
