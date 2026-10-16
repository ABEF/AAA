# Mixed-case migration-helper alias

Independent internal review, 2026-10-17. Severity: medium manifest-consistency
finding. This is not an on-chain custody exploit or deployment authorization.

The new migration helper address was normalized into a local variable but its
raw spelling remained in the copied manifest. Later creator-inbox separation
compared a normalized receiver against that raw helper address. A mixed-case
spelling of the receiver could therefore pass as a distinct helper.

A targeted read-only mutation of `external_fixture()` set `migration_budget.address`
to the uppercase hexadecimal spelling of the existing receiver and set
`observed_vault_helper` to its lowercase spelling. Before the fix, actual console
output was:

```text
baseline True
addresses 0x00000000000000000000000000000000000006aa 0x0000000000000000000000000000000000001e61
{'alias_mutation_ready': True, 'deployment_authorized': False, 'codes': []}
```

The checker now stores the validated normalized helper address in its private
deep-copied manifest before subsequent comparisons. The caller's original input
remains unchanged. The new regression requires `reward.custody` rejection for
this exact mutation. Three adjacent helper/module/mint-recipient alias tests
were run with it; [the scoped receipt](verification.json) and [raw output](tests.log)
bind the actual script/test dependencies before and after execution.

The offline validator establishes declared manifest consistency only. It does not
query a chain, authenticate evidence, prove a deployed runtime honest, or authorize
deployment. Exact Vault/helper/controller bindings, runtime pins and inventory
block identities must still be collected and independently reviewed.
