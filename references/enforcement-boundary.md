# Enforcement boundary

## Status vocabulary

| Status | Meaning |
|---|---|
| `enforced` | The active host mechanically prevents or gates the behavior and produced current evidence |
| `script-checked` | A deterministic local script checked package structure or static content |
| `instruction-supported` | The skill tells the model what to do, but no mechanism guarantees behavior |
| `host-required` | Robin, Codex, CI, permissions, connectors, or another runtime must provide the mechanism and evidence |
| `not-supported-standalone` | Standalone skill use cannot provide the required mechanism |

## Boundary matrix

| Function | Standalone | Embedded host |
|---|---|---|
| PAF reasoning and claim review | `instruction-supported` | `instruction-supported`, plus host eval if run |
| Package structure, links, eval inventory, secret-pattern scan | `script-checked` by `scripts/quick_validate.py` | Same or CI-enforced |
| State schemas, scope/tenure lineage, revision/lifecycle, exact Nexus-decision authority, current upstream lineage, pending-request resolution, append-only Nexus/evidence/claim/outcome history, metric-result gates, revision chain, and proposal-attempt chain | `script-checked` by `scripts/hypothesis_state.py` when invoked | Host must enforce the same contract or a stronger one |
| Fresh source retrieval | `not-supported-standalone` unless user supplies data | `host-required` successful connector/tool reads |
| Durable hypothesis persistence | Optional explicit single-host file adapter writes one atomic current-state plus incremental-history bundle against an absolute external local-FS root; never automatic skill memory. Accepted proves exact readback; power-loss durability is host-dependent | `host-required`; Robin owns storage and retrieval |
| Permission and write approval | `not-supported-standalone` | `host-required`; runtime owns it |
| Persistence receipts | File adapter emits and verifies local receipts after authorized commit | `host-required`; current Robin receipt must be supplied |
| Retry and recovery state | Explicit load plus verified local checkpoint; token-and-dead-PID-bound lock recovery; exit `6` requires `outcome_unknown` reconciliation | `host-required` checkpoint and retry mechanism |
| Sub-agent delegation | Optional host capability | Host-owned |
| Scheduler or proactive invocation | `not-supported-standalone` | Host-owned event runtime |
| External outcome verification | Closure snapshot plus explicit append-only outcome events from user-supplied evidence | Host-required observation, evidence freshness, attribution, and receipt authenticity |
| Owner identity / external approval authenticity | `not-supported-standalone`; file adapter checks only safe ref, owner-ref equality, revision, and subject hash | `host-required` identity and receipt verification |
| Privacy | Bounded sensitive-pattern scan only; not proof of complete privacy review | `host-required` structured privacy, retention, and access policy |

## Readiness rule

Do not call the standalone skill `quality-ready`, `production-ready`, or
`pass-eligible` because its critical behavioral boundaries are instructions.
Static validation can establish package integrity only.

An embedded host may make a stronger claim only when it supplies current evidence
for the relevant source reads, behavioral evals, permission gates, and outcome
receipts. Missing optional evidence should be labelled, but missing
decision-critical evidence blocks the corresponding strong claim.

## What the validator does not prove

`scripts/quick_validate.py` does not execute a model, validate truth, inspect live
sources, enforce approvals, or verify external impact. It detects package
regressions and obvious publication hazards. `scripts/hypothesis_state.py`
validates and persists only the supplied local state proposal; it does not prove
that the hypothesis, evidence, decision, or external outcome is true.
Its revision chain also needs a trusted external anchor before it can provide
tamper evidence against an actor able to rewrite and rehash the complete
bundle.
