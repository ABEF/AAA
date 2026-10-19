// Generated from palette-system.mjs by export-inventory.mjs. Do not edit this copy.
/**
 * PoPL artwork catalogue, version 1.
 *
 * This browser-safe module defines visual traits only. Its seeded catalogue order
 * is an illustration/test fixture, never a source of production mint randomness.
 * Production trait draws must use the authenticated randomness implementation.
 */
export const VERSION = 1;
export const COLORS = Object.freeze([
  {id:'cyan', label:'Cyan', accent:'#27dff2'},
  {id:'blue', label:'Blue', accent:'#3e85ff'},
  {id:'violet', label:'Violet', accent:'#b178ff'},
  {id:'emerald', label:'Emerald', accent:'#35e6ac'},
  {id:'amber', label:'Amber', accent:'#ffbf59'},
  {id:'crimson', label:'Crimson', accent:'#ff5378'},
  {id:'ivory', label:'Ivory', accent:'#f2e9d8'},
  {id:'onyx', label:'Onyx', accent:'#171c24'},
].map(Object.freeze));
export const COLOR_STYLES = Object.freeze([
  {id:'monochrome', label:'Monochrome', colors:1, supply:200},
  {id:'bicolor', label:'Bicolor', colors:2, supply:500},
  {id:'tricolor', label:'Tricolor', colors:3, supply:300},
].map(Object.freeze));
export const PATTERNS = Object.freeze([
  {id:'arcs', label:'Flowing arcs'},
  {id:'panels', label:'Segmented panels'},
  {id:'orbits', label:'Orbital rings'},
  {id:'ribs', label:'Twin circuit routes'},
].map(Object.freeze));
export const RARITIES = Object.freeze([
  {id:'commun', label:'Commun', royaltyMultiplier:1, supply:600},
  {id:'rare', label:'Rare', royaltyMultiplier:2, supply:300},
  {id:'legendary', label:'Legendary', royaltyMultiplier:3, supply:100},
].map(Object.freeze));
export const EVOLUTIONS = Object.freeze([
  {id:'dormant', label:'Dormant', minimumCents:0},
  {id:'activated', label:'Activated', minimumCents:10000},
  {id:'enhanced', label:'Enhanced', minimumCents:100000},
  {id:'singularity', label:'Singularity', minimumCents:1000000},
].map(Object.freeze));
export const BICOLOR_ANCHORS = Object.freeze(['amber','crimson','ivory','onyx']);
export const TRICOLOR_ADDITIONS = Object.freeze(['amber','crimson','onyx']);
export const COLLECTION_SUPPLY = 1000;
export const PREVIEW_SEED = 'popl-artwork-catalogue-v1';
const colorById = new Map(COLORS.map(color => [color.id,color]));
const rank = new Map(COLORS.map((color,index) => [color.id,index]));
const styleBySize = new Map(COLOR_STYLES.map(style => [style.colors,style]));
const royaltyByRarity = new Map(RARITIES.map(rarity => [rarity.id,rarity]));

export function canonicalColors(ids) {
  if (!Array.isArray(ids) || ids.length < 1 || ids.length > 3 || new Set(ids).size !== ids.length
      || ids.some(id => !colorById.has(id))) throw new Error('A palette needs one to three distinct known colors.');
  return [...ids].sort((left,right) => rank.get(left)-rank.get(right));
}
export function isAllowedBicolor(ids) {
  return Array.isArray(ids) && ids.length === 2 && new Set(ids).size === 2
    && ids.every(id => colorById.has(id)) && ids.some(id => BICOLOR_ANCHORS.includes(id));
}
export function isAllowedTricolor(ids) {
  return Array.isArray(ids) && ids.length === 3 && new Set(ids).size === 3
    && ids.every(id => colorById.has(id)) && ids.some((id,index) =>
      TRICOLOR_ADDITIONS.includes(id) && isAllowedBicolor(ids.filter((_,other) => index !== other)));
}
function combinations(items,size,start=0,prefix=[]) {
  if (prefix.length === size) return [prefix];
  return items.slice(start).flatMap((item,offset) => combinations(items,size,start+offset+1,[...prefix,item]));
}
export const PALETTES = Object.freeze(COLOR_STYLES.flatMap(style =>
  combinations(COLORS.map(color => color.id),style.colors)
    .filter(ids => style.colors === 1 || (style.colors === 2 ? isAllowedBicolor(ids) : isAllowedTricolor(ids)))
    .map(ids => Object.freeze({
      id:ids.join('-'), colorStyle:style.id, colorIds:Object.freeze(ids),
      label:ids.map(id => colorById.get(id).label).join(' / '),
      accent:colorById.get(ids[0]).accent,
    }))));
const paletteById = new Map(PALETTES.map(palette => [palette.id,palette]));
export const getColor = id => colorById.get(id);
export const getPalette = id => paletteById.get(id);
export const getRarity = id => royaltyByRarity.get(id);
export function paletteForColors(ids) { return getPalette(canonicalColors(ids).join('-')); }

// Explicitly noncryptographic, for stable fixture construction and UI previews.
function hashSeed(value) {
  let hash = 2166136261;
  for (const char of String(value)) { hash ^= char.codePointAt(0); hash = Math.imul(hash,16777619); }
  return hash >>> 0;
}
function randomFor(seed) {
  let state = hashSeed(seed) || 0x9e3779b9;
  return () => { state ^= state << 13; state ^= state >>> 17; state ^= state << 5; return (state >>> 0) / 4294967296; };
}
function shuffled(items,seed) {
  const result = [...items]; const random = randomFor(seed);
  for (let index=result.length-1; index>0; index--) {
    const other = Math.floor(random()*(index+1));
    [result[index],result[other]] = [result[other],result[index]];
  }
  return result;
}

/**
 * A balanced, finite 1,000-entry visual inventory. Each style has 60/30/10
 * rarity composition; every palette and pattern can appear in every rarity.
 * The same complete palette/pattern/rarity appears at most four times.
 * The seed changes fixture order and remainder assignment, not economic rights.
 */
export function buildInventory(seed=PREVIEW_SEED) {
  if (typeof seed !== 'string' || !seed.length) throw new Error('A nonempty fixture seed is required.');
  const result = [];
  for (const style of COLOR_STYLES) {
    const available = PALETTES.filter(palette => palette.colorStyle === style.id);
    for (const rarity of RARITIES) {
      const count = style.supply*rarity.supply/COLLECTION_SUPPLY;
      const balanced = shuffled(available,`${seed}:${style.id}:${rarity.id}:palette-order`);
      for (let index=0; index<balanced.length; index++) {
        const palette = balanced[index];
        const paletteCount = Math.floor(count/balanced.length)+(index < count%balanced.length ? 1 : 0);
        const patterns = shuffled(PATTERNS,`${seed}:${palette.id}:${rarity.id}:patterns`);
        for (let copy=0; copy<paletteCount; copy++) {
          const pattern = patterns[copy%patterns.length];
          result.push({rarity:rarity.id, colorStyle:style.id, paletteId:palette.id,
            colorIds:[...palette.colorIds], pattern:pattern.id});
        }
      }
    }
  }
  return shuffled(result,`${seed}:token-order`).map((traits,index) => ({tokenId:index+1,...traits}));
}
const defaultInventory = buildInventory();
export function traitsForTokenId(tokenId,inventory=defaultInventory) {
  if (!Number.isSafeInteger(tokenId) || tokenId < 1 || tokenId > COLLECTION_SUPPLY) {
    throw new Error('Token ID must be an integer from 1 to 1,000.');
  }
  const entry = inventory[tokenId-1];
  if (!entry || entry.tokenId !== tokenId) throw new Error('Inventory must be ordered by token ID.');
  return {...entry,colorIds:[...entry.colorIds]};
}
export function baseDesignId(traits) { return `${traits.paletteId}-${traits.pattern}-${traits.rarity}`; }
/** Fixed production-catalogue entry code; color assignment still requires VRF draws without replacement. */
export function encodeArtworkTraits(traits) {
  const paletteIndex = PALETTES.findIndex(palette => palette.id === traits.paletteId);
  const patternIndex = PATTERNS.findIndex(pattern => pattern.id === traits.pattern);
  if (paletteIndex < 0 || patternIndex < 0) throw new Error('Cannot encode unknown palette or pattern.');
  return paletteIndex*PATTERNS.length+patternIndex;
}
export function decodeArtworkTraits(code) {
  if (!Number.isSafeInteger(code) || code < 0 || code >= PALETTES.length*PATTERNS.length) throw new Error('Invalid artwork trait code.');
  const palette = PALETTES[Math.floor(code/PATTERNS.length)];
  return {paletteId:palette.id,colorStyle:palette.colorStyle,colorIds:[...palette.colorIds],pattern:PATTERNS[code%PATTERNS.length].id};
}
export function inventoryCodesByRarity(inventory=defaultInventory) {
  validateInventory(inventory);
  return Object.fromEntries(RARITIES.map(rarity => [rarity.id,
    inventory.filter(entry => entry.rarity === rarity.id).map(encodeArtworkTraits)]));
}
export function artworkId(traits,evolution) {
  if (!EVOLUTIONS.some(state => state.id === evolution)) throw new Error('Unknown evolution.');
  return `${baseDesignId(traits)}-${evolution}`;
}
export function metadataAttributes(traits,evolution='dormant') {
  const palette = getPalette(traits.paletteId);
  const rarity = getRarity(traits.rarity);
  const style = COLOR_STYLES.find(item => item.id === traits.colorStyle);
  const pattern = PATTERNS.find(item => item.id === traits.pattern);
  const state = EVOLUTIONS.find(item => item.id === evolution);
  if (!palette || !rarity || !style || !pattern || !state || palette.colorStyle !== style.id
      || JSON.stringify(palette.colorIds) !== JSON.stringify(traits.colorIds)) throw new Error('Invalid artwork traits.');
  return [
    {trait_type:'Rarity',value:rarity.label},
    {trait_type:'Color style',value:style.label},
    {trait_type:'Palette',value:palette.label},
    ...palette.colorIds.map((id,index) => ({trait_type:`Color ${index+1}`,value:getColor(id).label})),
    {trait_type:'Circuit pattern',value:pattern.label},
    {trait_type:'Evolution',value:state.label},
  ];
}

/** Throws if supply, exact quotas, valid traits or visual repetition limits fail. */
export function validateInventory(inventory) {
  if (!Array.isArray(inventory) || inventory.length !== COLLECTION_SUPPLY) throw new Error('Inventory supply must be 1,000.');
  const rarities = Object.fromEntries(RARITIES.map(item => [item.id,0]));
  const styles = Object.fromEntries(COLOR_STYLES.map(item => [item.id,0]));
  const combinations = new Map(); const styleRarity = new Map(); const palettes = new Map();
  for (let index=0; index<inventory.length; index++) {
    const entry = inventory[index];
    if (entry.tokenId !== index+1) throw new Error('Token IDs must be unique and sequential.');
    metadataAttributes(entry);
    rarities[entry.rarity]++; styles[entry.colorStyle]++;
    const key = baseDesignId(entry);
    combinations.set(key,(combinations.get(key)||0)+1);
    const count = combinations.get(key);
    if (count > 4 || (entry.rarity === 'legendary' && count > 1)) throw new Error('Artwork repetition limit exceeded.');
    const styleKey = `${entry.colorStyle}:${entry.rarity}`;
    styleRarity.set(styleKey,(styleRarity.get(styleKey)||0)+1);
    const paletteKey = `${entry.paletteId}:${entry.rarity}`;
    palettes.set(paletteKey,(palettes.get(paletteKey)||0)+1);
  }
  for (const rarity of RARITIES) if (rarities[rarity.id] !== rarity.supply) throw new Error('Exact rarity quota violated.');
  for (const style of COLOR_STYLES) {
    if (styles[style.id] !== style.supply) throw new Error('Color-style quota violated.');
    const available = PALETTES.filter(palette => palette.colorStyle === style.id);
    for (const rarity of RARITIES) {
      const expected = style.supply*rarity.supply/COLLECTION_SUPPLY;
      if (styleRarity.get(`${style.id}:${rarity.id}`) !== expected) throw new Error('Color style must not change rarity odds.');
      const counts = available.map(palette => palettes.get(`${palette.id}:${rarity.id}`)||0);
      if (Math.min(...counts) < 1 || Math.max(...counts)-Math.min(...counts) > 1) {
        throw new Error('Every palette must be balanced and available in each rarity.');
      }
    }
  }
  return {supply:inventory.length,rarities,styles,uniqueBaseDesigns:combinations.size,
    maximumIdenticalArtwork:Math.max(...combinations.values())};
}
