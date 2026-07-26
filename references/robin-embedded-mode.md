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
blocked_claims
recommended_artifact_or_decision
evidence_status
enforcement_boundary
next_step
```

Each `next_step` includes the action, owner, expected evidence, and pass/fail
decision rule. The result is advisory until Robin or another authorized owner
accepts the decision.

## Prohibited behavior

- Do not write Robin memory or project state.
- Do not call connectors or tools unless Robin explicitly delegates them inside
  the host's existing permission boundary.
- Do not broaden source scope or permissions.
- Do not send, publish, schedule, commit, deploy, or change external systems.
- Do not claim host checks, receipts, or outcomes that were not supplied.
- Do not answer as Robin or modify Robin's voice and identity contract.

If required host evidence is absent, return `host-required` and the exact
coverage gap.
