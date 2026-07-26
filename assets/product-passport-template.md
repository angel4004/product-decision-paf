# Product passport

This is a compact human-readable view of the product Nexus. Nexus is the
domain model of maintained product knowledge, not the physical store. For
longitudinal work render this passport from the canonical workspace JSON; do
not edit it as an independent source of truth.

## State identity

- Workspace ID and revision:
- Product ref:
- Snapshot `as_of`:
- Revision-chain head:
- Proposal-history head:
- Last accepted persistence receipt ref:

## Active decision scope

- Active decision-scope ID:
- Actor and desired outcome:
- Baseline, target, and period:
- Decision to unlock:
- Prior scope and transition receipt ref:

## Decision owner

- Active owner-tenure ID and owner ref:
- Effective workspace revision:
- Prior tenure and transition receipt ref:

## Nexus

| Entry ID | Kind | Statement | Evidence IDs and freshness | Status | Decision authority | Supersedes |
|---|---|---|---|---|---|---|
|  | fact / interpretation / decision / unknown |  |  | supported / partial / contradictory / stale / missing | owner tenure, scope, subject hash, receipt, reversibility for decisions |  |

## Evidence ledger

| Evidence ID | Source and observation period | Method, segment, filters | Numerator/denominator | Summary | Status |
|---|---|---|---|---|---|
|  |  |  | canonical decimal strings or null |  |  |

## Product mechanism

- User problem and current workaround:
- Proposed behavior or value mechanism:
- Main alternative:
- Adoption, delivery, and business-model constraints:

## PAF hypothesis map

- Customer-need hypotheses:
- Value-proposition hypotheses:
- Solution hypotheses:
- Business-model hypotheses:
- Lifecycle contexts:
- Active focus hypothesis:
- Explicit co-tests:

## Claims and decision boundaries

- Active blocked claims derived from `claim_log`:
- Resolved or withdrawn claims and evidence:
- Proposed assumptions awaiting approval:
- Withdrawn or tenure-invalidated pending requests:
- Host/runtime coverage gaps:

## Post-release outcomes

This is the authoritative `outcome_log`, not an edit of closed cards.

| Event ID | Closed hypothesis and scope | Status | Current evidence | Summary / attribution note | Host receipt | Supersedes |
|---|---|---|---|---|---|---|
|  |  | observed / attribution_limited / verified / withdrawn |  |  | only for verified | latest prior event |

## Next checkpoint

- One hypothesis, artifact, or observation:
- Owner and time box:
- Expected evidence:
- Pass rule:
- Fail rule:
- Decision after the result:
