# Artwork upload bundle and immutable publication

The 2026-10-15 preparation tool packages the approved existing artwork without
regenerating its texture. It verifies all 2,784 renderer filenames against the
contract's packed palette/pattern catalogue, source image SHA-256 hashes,
self-contained SVG resources and reference JSON image paths. It then streams
the resulting archive back and verifies every member. Existing output directories
are never overwritten.

From the contract repository root, supply the actual website artwork directory
and a new output directory:

```sh
python scripts/prepare_ipfs_bundle.py --source path/to/aaa-website/assets/nfts --output path/to/new-ipfs-bundle
```

The output contains `popl-artwork-ipfs.tar.gz`, `SHA256-manifest.json` and
`bundle.json`. The archive's `content/` directory contains 2,784 SVGs, 2,784
reference metadata JSONs, the source manifest, packed contract catalogue and
checksum manifest: **5,571 files**. The contract generates live token metadata
on chain; these reference JSONs are not fixed per-token balances or fee history.

<a id="remaining-publication-steps"></a>

## Publication procedure

Track completion in the [metadata task](../TODO.md#task-metadata-ops). These are procedural instructions, not a second task-status list.

- Select a pinning provider and review its import/CAR support, retention and
  payment terms. No account, purchase, public upload or pin is supplied by this tool.
- Extract the verified archive, import the **contents of `content/`** as the
  root directory with a pinned Kubo/importer version and explicit UnixFS import
  settings. Record those settings and the resulting directory CID. Do not use a
  mutable IPNS name or assume the archive's SHA-256 is an IPFS directory CID.
- Independently verify every `ipfs://<CID>/<artwork-id>.svg` path and its
  bytes against the manifest. Use an independent importer or CAR verification,
  plus retrieval through the selected provider and another gateway.
- Pin the complete DAG redundantly and monitor retrieval. Content addressing
  prevents unnoticed replacement; it does not ensure someone keeps serving it.
- Configure and independently review `NFT_BASE_URI=ipfs://<CID>/` before
  freezing/sealing the collection, retaining its trailing slash and flat SVG paths.
  Budget actual constructor bytes as well as compiled NFT initcode size.
- Rehearse Dormant/Activated/Enhanced/Singularity rendering, stale/remote
  valuation fallback and ERC-4906 refresh on the target marketplace/test deployment.

The prepared bundle deliberately reports `root_cid=null`, `uploaded=false` and
`pinned=false` until the publication steps actually happen. Provider selection
was deferred by the user. See the [IPFS importer guidance](https://docs.ipfs.tech/how-to/command-line-quick-start/)
and the [release approval record](RELEASE_CHECKLIST.md).
