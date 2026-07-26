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
| Fresh source retrieval | `not-supported-standalone` unless user supplies data | `host-required` successful connector/tool reads |
| Durable memory and retrieval | `not-supported-standalone` | `host-required`; Robin owns it |
| Permission and write approval | `not-supported-standalone` | `host-required`; runtime owns it |
| Trace lifecycle and receipts | `not-supported-standalone` | `host-required`; current receipt must be supplied |
| Retry and recovery state | Described only | `host-required` checkpoint mechanism |
| Sub-agent delegation | Optional host capability | Host-owned |
| Scheduler or proactive invocation | `not-supported-standalone` | Host-owned event runtime |
| External outcome verification | User-supplied evidence only | Host-required observation and attribution |

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
regressions and obvious publication hazards.
