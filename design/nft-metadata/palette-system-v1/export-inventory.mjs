import {writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {
  VERSION,PREVIEW_SEED,COLORS,COLOR_STYLES,PATTERNS,PALETTES,RARITIES,
  BICOLOR_ANCHORS,TRICOLOR_ADDITIONS,buildInventory,validateInventory,inventoryCodesByRarity,
} from './palette-system.mjs';
const inventory = buildInventory();
const data = {version:VERSION,kind:'fixed visual inventory; deterministic preview order, not production randomness',
  previewSeed:PREVIEW_SEED,colors:COLORS,colorStyles:COLOR_STYLES,patterns:PATTERNS,
  bicolorAnchors:BICOLOR_ANCHORS,tricolorAdditions:TRICOLOR_ADDITIONS,
  palettes:PALETTES,rarities:RARITIES,summary:validateInventory(inventory),inventory};
await writeFile(fileURLToPath(new URL('./inventory.json',import.meta.url)),`${JSON.stringify(data,null,2)}\n`);
const codes = inventoryCodesByRarity(inventory);
const hex = Object.fromEntries(Object.entries(codes).map(([rarity,entries]) =>
  [rarity,entries.map(code => code.toString(16).padStart(4,'0')).join('')]));
const sha256 = Object.fromEntries(Object.entries(hex).map(([rarity,value]) =>
  [rarity,createHash('sha256').update(Buffer.from(value,'hex')).digest('hex')]));
const packed = {version:VERSION,encoding:`uint16 big-endian; paletteIndex * ${PATTERNS.length} + patternIndex`,
  description:'Fixed finite visual inventory. Draw without replacement within each authenticated VRF-selected rarity. No seed-based mint randomness.',
  paletteOrder:PALETTES.map(palette => ({id:palette.id,colorIds:palette.colorIds,
    mask:palette.colorIds.reduce((mask,id) => mask | (1 << COLORS.findIndex(color => color.id === id)),0)})),
  patternOrder:PATTERNS.map(pattern => pattern.id),codes,hex,sha256};
await writeFile(fileURLToPath(new URL('./packed-catalog.json',import.meta.url)),`${JSON.stringify(packed,null,2)}\n`);
const moduleSource = await readFile(new URL('./palette-system.mjs',import.meta.url),'utf8');
await writeFile(fileURLToPath(new URL('./art-catalog.js',import.meta.url)),
  `// Generated from palette-system.mjs by export-inventory.mjs. Do not edit this copy.\n${moduleSource}`);
console.log(JSON.stringify(data.summary));
