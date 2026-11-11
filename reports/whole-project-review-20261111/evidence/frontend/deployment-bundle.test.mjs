import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';

const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),'..');
// Enumerate the local module graph without executing app.js, constructing a
// signer, changing configuration or touching the existing dist/Anvil overlay.
async function dependencies(entry,seen=new Set()){
  if(seen.has(entry))return seen;
  assert.match(entry,/^[a-z0-9-]+\.js$/);seen.add(entry);
  const source=await readFile(resolve(ROOT,entry),'utf8');
  const imports=/\b(?:import|export)\s+(?:[^'";]*?\s+from\s*)?['"](\.[^'"]+)['"]|\bimport\(\s*['"](\.[^'"]+)['"]\s*\)/g;
  for(const match of source.matchAll(imports)){
    const target=match[1]||match[2];
    assert.match(target,/^\.\/[a-z0-9-]+\.js$/);
    await dependencies(target.slice(2),seen);
  }
  return seen;
}
async function declared(source,pattern){
  const text=await readFile(resolve(ROOT,source),'utf8'),match=text.match(pattern);
  assert.ok(match,'Explicit public-file list not found in '+source);
  return new Set([...match[1].matchAll(/'([^']+\.js)'/g)].map(item=>item[1]));
}

test('demo build includes the complete configured read-profile module graph',async()=>{
  const required=await dependencies('app.js'),published=await declared('build.mjs',/const files\s*=\s*\[([\s\S]*?)\];/);
  assert.ok(required.has('deployment-source10.js'),'Current profiles must be reached by this regression');
  assert.deepEqual([...required].filter(name=>!published.has(name)).sort(),[],'A configured deployment would request missing build modules');
});

test('development server allows every browser module for configured profiles',async()=>{
  const required=await dependencies('app.js'),served=await declared('server.mjs',/const allowed\s*=\s*new Set\(\[([\s\S]*?)\]\);/);
  assert.deepEqual([...required].filter(name=>!served.has(name)).sort(),[],'A configured deployment would receive module404s');
});
