# Artwork upload bundle and immutable publication

The 2026-10-15 preparation tool packages the approved existing artwork without
regenerating its texture. It verifies all 2,784 renderer filenames against the
contract's packed palette/pattern catalogue, source image SHA-256 hashes,
self-contained SVG resources and reference JSON image paths. It rejects processing instructions/DTDs, XML base, active/style/escaped resource
channels and duplicate/nonfinite JSON before packaging, then streams the resulting
archive back and verifies every member. This validates the approved static format;
it is not a general-purpose browser sanitizer. [Audit evidence](../reports/whole-project-execution-20261029/REVIEW.md). Existing output directories
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

## Current artwork revision

The 2026-10-20 Twin circuit routes revision replaces Vertical ribs in stable slot
`ribs` (index 3), preserving inventory and image paths. Any bundle prepared before
this revision contains the older artwork and must not be selected for the new
release. Prepare/verify the full bundle from the matching website commit, obtain
a new content root when publishing, and bind that root before sealing. Existing
historical bundles remain evidence for their original bytes, not this revision.
See [current artwork verification](../reports/twin-circuits/VERIFICATION.md).

Reference metadata now keeps intrinsic rarity weight1/2/3 distinct from activation
eligibility. The local website correction changes no SVGs, catalogue inventory or
manifest effective example-ledger fields.72historical references remain historical.
Do not select old reference JSON merely because the image hashes match; prepare
the bundle from the reviewed source revision. This source correction is not an
upload, CID, pin, immutable-base-URI decision or marketplace refresh verification.

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
- Rehearse Dormant/Activated/Enhanced/Singularity rendering, stale/outbound/parked
  valuation fallback and ERC-4906 refresh on the target marketplace/test deployment.

The prepared bundle deliberately reports `root_cid=null`, `uploaded=false` and
`pinned=false` until the publication steps actually happen. Provider selection
was deferred by the user. See the [IPFS importer guidance](https://docs.ipfs.tech/how-to/command-line-quick-start/)
and the [release approval record](RELEASE_CHECKLIST.md).
