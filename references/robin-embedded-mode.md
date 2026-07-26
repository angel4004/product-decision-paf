# Robin embedded mode

## Ownership

Robin remains the root agent. Robin owns identity, user profile, durable memory,
source routing, permissions, approvals, budgets, tool execution, retries,
delivery, and receipts. This skill owns only the bounded product-decision
analysis for the current task.

## Input contract

Robin should pass:

- `task`: the user's product-decision request;
- `goal_context`: actor, outcome, baseline, period, and decision if known;
- `source_evidence`: bounded facts and safe refs from successful reads;
- `constraints`: privacy, permissions, budget, deadline, and requested output;
- `runtime_evidence`: which checks or host mechanisms actually ran;
- `state_context` when continuity matters: workspace ID and revision, bounded
  active decision scope and owner tenure, relevant Nexus/evidence/claim/outcome
  events, latest relevant Hypothesis Card revisions, both integrity-chain
  heads, and the last accepted persistence receipt;
- `language`: desired response language.

Do not pass credentials, raw private memory, raw transcripts, private traces, or
unnecessary personal data.

## Return contract

Return a structured object or equivalently headed response:

```text
route
goal
facts
hypotheses
interpretations
evidence_gaps
active blocked claims derived from claim_log
latest post-release outcome derived from outcome_log
recommended_artifact_or_decision
evidence_status
enforcement_boundary
persistence_handoff
persistence_status
next_step
```

Each `next_step` includes the action, owner, expected evidence, and pass/fail
decision rule. The result is advisory until Robin or another authorized owner
accepts the decision.

`persistence_handoff` is either:

- a complete atomic candidate transaction with expected revisions,
  decision-scope and owner-tenure bindings, a new Hypothesis Card revision,
  typed Nexus/evidence/claim deltas, structured `metric_results`,
  `new_nexus_entry_ids`, optional outcome events, exact Nexus-decision
  authority, and subject-bound required approvals; or
- a schema-valid `proposal_intent` when one of those bindings is unavailable.
  The intent lists the missing host inputs, is `commit_eligible: false`, and
  cannot be passed to Robin's persistence adapter.

`awaiting_owner_rule` is a persistable checkpoint, not permission to run. Any
`running` transition also needs a host-supplied `execution_ref` and a
`state_transition` approval bound to the candidate revision and that exact ref.
The candidate may remain `proposed` while Robin resolves the approval. A co-test
keeps separate peer contracts and verdicts while sharing its bound plan and
execution evidence; one peer may close while the other remains reviewable.
Pending requests may disappear only with a matching approval or append-only
resolution (`withdrawn` or `invalidated_by_tenure_transition` appended in the
same candidate revision as the owner transition).
A complete transaction is `proposed` until Robin's adapter returns `accepted`,
`rejected`, `conflict`, `failed`, or `outcome_unknown`; an incomplete intent is
always `not_persisted`. A later invocation must receive the matching accepted
receipt before it treats an update as persistent. Robin's storage, power-loss,
backup, and external-integrity guarantees remain host concerns.

The card's external-outcome fields are the immutable closure snapshot. Later
impact assertions must be appended to `outcome_log` against current usable
evidence. Missing, stale, or contradictory evidence cannot support a positive
outcome; withdrawal requires contradictory evidence.

## Prohibited behavior

- Do not write Robin memory or project state directly. Return the bounded
  persistence handoff to Robin instead.
- Do not call connectors or tools unless Robin explicitly delegates them inside
  the host's existing permission boundary.
- Do not broaden source scope or permissions.
- Do not send, publish, schedule, commit, deploy, or change external systems.
- Do not claim host checks, receipts, or outcomes that were not supplied.
- Do not answer as Robin or modify Robin's voice and identity contract.

If required host evidence is absent, return `host-required` and the exact
coverage gap.
