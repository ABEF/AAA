# Admission and captured valuation reuse

This candidate separates exact input admission from USD valuation. It preserves
the existing native/fixed-ZZZ identity, active-policy enabled flag, native hash
and18-decimal pin, nonzero ERC20 runtime/code-hash pin, and Oracle-versus-admitted
decimals match. `validateInput(address)` exposes those same read-only checks and
returns the admitted decimal precision; it does not admit an asset or change
state. Existing `value(token,0)` still returns0 before any admission/price read.

Entry currently obtains a public live lower-value quote and immediately captures
the full two-source transaction vector, rejecting inequality. Only STATIC reads
and local computation intervene. The candidate instead validates admission, uses
`beginEntryReviewed`'s authenticated lowerUSD return, then applies the same zero
and governed activation/growth minimum checks before any pull or approval. The
captured upperUSD, source/LP bounds, caller loss limit, policy fingerprint,
ownership/context binding and all final proofs remain intact.

For a rejected subminimum contribution, Pricing may transiently open its basis
before Entry reverts; EVM rollback removes it and returns native call value. This
does not create a stored partial review or funded operation. When several inputs
are invalid simultaneously, error precedence may change; no rejected input is
newly accepted. The API/storage of Entry remains unchanged. Assets adds one
read-only selector; its existing storage and write permissions remain unchanged.

Virtual probe01 uses the separately proposed derived-accounted fresh royalty
variant, not the later final optional-read candidate. Four selected objects pass
the original normal size limits: Assets6034, Entry9809, AssetsFactory7672 runtime
bytes, and Access48359+96constructor bytes =48455, leaving697 initcode bytes.
That probe is not source adoption, a complete48-object build or gas approval.
Final source, ABI and constructor provenance must be recorded after selection.
