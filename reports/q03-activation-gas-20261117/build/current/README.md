# Adopted-source normal build

This directory contains the final **actual02** normal compilation, executed
18 November after the coordinated source port and restoration of the normal
configuration. It is the current source build for this campaign, not deployment
or release approval. The global-only allocator is selected; the envelope and
duplicate-counter alternatives remain separately recorded, unadopted experiments.

- The compiler input includes exactly 100 sources: 61 project and 39 dependencies.
- The actual raw source bytes match that input before and after compilation.
- The effective normal profile and all four required build-input files are
  checked; source, build inputs and compiler remain unchanged during the build.
- The input **and output** are byte-identical to global-only proposed01.
- All 48 normal runtime/initcode gates pass; all 48 public ABIs and semantic storage
  layouts match the accepted two-source validation build. Eight objects are
  internal libraries; the strict reference importer admits 40 concrete objects.
- Royalty runtime is 24551 bytes, leaving 25; Vault leaves 32 and Oracle 3. Access
  creation plus its 96 constructor-argument bytes uses 48404/49152 bytes.

`normal-size-evidence.json` is the actual final evidence. `ADMISSION_RESULT.json`
records successful strict import through the existing function-reference code.
`PREFLIGHT_RESULT.json` is the separate prospective schema check before compiler
launch; it is not future execution evidence. Original actual01 compilation was
successful but its metadata omitted the proper build-input inventory, so it was
not promoted. That attempt remains in `global-only-build/actual01` with its
explicit admission failure. The one corrected compilation fixes the producer;
it does not rerun unchanged tests or modify the compiler settings.

The private allocator API changes are coupled to the actual same-currency
liability. Original mapping-only storage is retained. The affected legacy test
harness now maintains an independent checked liability; its old test-method
bodies are unchanged and were not executed by this source/build work. Canonical
royalty records still flatten per-NFT rights. No raw-book transplantation or
hot-upgrade compatibility is claimed.

Whole-operation gas, markets, deployments and operating approval require their
separate evidence. These size/schema checks do not qualify 20M activation gas.
