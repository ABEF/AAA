import {ARTWORKS} from './artworks.js';
import {dirname,resolve,relative} from 'node:path';
import {fileURLToPath} from 'node:url';
import {mkdir,copyFile,rm} from 'node:fs/promises';
const files = ['index.html','styles.css','app.js','domain.js','wallet.js','ui-state.js','preview-store.js','local-client.js','browser-client.js','browser-intent.js','browser-wallet.js','local-view.js','local-view.css','deployment-api.js','deployment-wallet-view.js','deployment-native.js','deployment-source9.js','deployment-source9-data.js','deployment-source9-prepare.js','deployment-source10.js','deployment-session.js', 'deployment-transactions.js','deployment-view.js','deployment-config.js','assets/audio/activation.mp4','assets/audio/evolution.mp4','assets/logo.jpg','assets/collec.jpg','assets/nft.jpg','assets/favicon.svg','assets/videos/popl-explainer-v7.mp4','assets/videos/popl-explainer-v7.png','artworks.js','palette-system.js','assets/nfts/manifest.json','assets/nfts/inventory.json',...ARTWORKS.flatMap(art => [art.src.slice(2),art.metadata.slice(2)])];
const projectPath=fileURLToPath(new URL('./',import.meta.url));
const outputPath=resolve(projectPath,'dist');
if(relative(projectPath,outputPath)!=='dist') throw new Error('Build output must stay in this project’s dist directory.');
await rm(outputPath,{recursive:true,force:true});
await mkdir(new URL('./dist/assets/',import.meta.url),{recursive:true});
for (const name of files) { await mkdir(new URL(`dist/${dirname(name)}/`,import.meta.url),{recursive:true}); await copyFile(new URL(name,import.meta.url),new URL(`dist/${name}`,import.meta.url)); }
console.log(`Static build complete: ${files.length} files in dist/. No dependency installation required.`);
