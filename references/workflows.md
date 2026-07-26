# Workflows

## Contents

- [PAF hypothesis review](#paf-hypothesis-review)
- [Goal framing and next step](#goal-framing-and-next-step)
- [Evidence-gap review](#evidence-gap-review)
- [PAF consistency review](#paf-consistency-review)
- [Product passport](#product-passport)
- [Decision or argument review](#decision-or-argument-review)
- [Client feedback](#client-feedback)
- [Post-release outcome update](#post-release-outcome-update)
- [Recovery](#recovery)

## PAF hypothesis review

1. Load the accepted workspace revision. Confirm the active decision scope,
   owner tenure, product/business goal, and current Nexus context.
2. Choose `null-base` when no evidence foundation exists; choose `data-base`
   when current behavior or product data can reveal an anomaly or bottleneck.
3. Classify the earliest uncertainty as customer/need, value proposition,
   solution, or business model. Record acquisition/activation, onboarding,
   go-to-market, adoption, and post-release impact as lifecycle context rather
   than additional PAF hypothesis classes.
4. Preserve upstream dependencies. Do not use solution interest as proof of a
   need, value demand as proof of solution effectiveness, or feature use as
   proof of business impact. Recheck support against current unsuperseded
   supported evidence and current supported Nexus lineage; a historical closed
   verdict alone is insufficient.
5. Create one `assets/hypothesis-card-template.md` with the experiment,
   primary and guardrail metrics, threshold/control, sample, conditions, and
   confirm/disconfirm/inconclusive decisions.
6. Use Understand → Identify → Execute. Execute at scale only after the
   relevant solution is supported; then record evidence-bound
   `metric_results`, add typed Nexus entries, and bind their same-revision IDs
   through `result.new_nexus_entry_ids`.

Value proposition and solution hypotheses may share one experiment when a
concrete interaction is required to test value. Keep the two claims, metrics,
and conclusions distinct. A solution and business-model hypothesis may also
share a soft-launch experiment. Both co-test forms require `mode = co_test`, a
shared plan ref, separate approved contracts and verdicts, and shared execution
evidence after launch. One peer may close while the other remains reviewable.

## Goal framing and next step

1. State actor, desired outcome, baseline, period, and decision.
2. Inventory existing artifacts and sources before creating a new one.
3. Identify the highest-impact unknown.
4. Choose the smallest artifact or observation that can resolve it.
5. Define a pass/fail decision rule and the action after each result.

## Evidence-gap review

1. List the decision and strong claims it depends on.
2. Build the evidence ledger from available sources.
3. Rank gaps by their ability to change the decision, not by ease of collection.
4. Block or weaken claims using `references/claim-boundaries.md`.
5. Return one evidence-gathering step with owner, time box, and decision rule.

## PAF consistency review

1. Identify the goal, Nexus context, base, and current PAF stage.
2. Check that the hypothesis class matches the uncertainty being reduced.
3. Check upstream knowledge, the hypothesis statement, segment, experiment,
   metric, threshold/control, sample, conditions, and decision rules.
4. Mark evidence `supported`, `partial`, `contradictory`, `stale`, or
   `missing`; record confirmation, disconfirmation, and unexpected knowledge
   as typed Nexus entries. Record strong-claim blocking or resolution as
   append-only `claim_log` events.
5. State which downstream claim remains blocked and choose one next PAF
   artifact or experiment. Do not invent a Confidence Point or composite score.

## Product passport

Create a passport only when explicitly requested or when a stable shared product
context is needed for repeated decisions. Treat it as a compact host-level Nexus
snapshot, not as an official PAF substitute for PRD or Hypothesis Cards. First
inventory existing passports and historical artifacts. Do not overwrite an
unknown current source of truth.

The passport must separate goal, actor, problem evidence, product mechanism,
adoption evidence, business evidence, constraints, decisions, assumptions,
blocked claims, and next checkpoint. Use
`assets/product-passport-template.md`.

## Decision or argument review

1. Restate the decision rather than polishing the argument.
2. Steelman the proposal and the strongest credible counter-position.
3. Separate facts, interpretations, assumptions, and preferences.
4. Identify the evidence that would change each side's position.
5. Recommend one reversible or information-rich next step.

Do not turn founder/CPO support into generic product advice or rhetorical cover
for an unsupported claim.

## Client feedback

Treat one item of feedback as a signal, not a roadmap or proof. Name the affected
goal, adoption blocker or opportunity, and evidence limits. Choose one immediate
use—retention, reply, MVP clarification, market test, or development input—then
define the next observation before expanding the artifact.

## Post-release outcome update

1. Load the closed card and its latest `outcome_log` event.
2. Treat the card's external-outcome fields as the immutable closure snapshot.
3. Validate that new evidence is current and unsuperseded.
4. Append one event: `observed`/`verified` require supported evidence,
   `attribution_limited` allows supported/partial evidence plus a limitation
   note, and `withdrawn` requires contradictory evidence.
5. Supersede exactly the prior latest event and include the new ID in
   `appended_outcome_event_ids`.

## Recovery

If a source read, model turn, or tool fails, preserve the decision state:
available facts, missing source, blocked claim, chosen artifact, and next retry.
For longitudinal work, prepare the versioned artifact defined in
`references/hypothesis-state-and-persistence.md`: a complete change set when
all required bindings are available, otherwise a schema-valid,
non-committable proposal intent. A standalone host may commit only the complete
change set through `scripts/hypothesis_state.py` against an explicitly selected
absolute external local-filesystem state root; Robin may use its own adapter.
Without an accepted persistence receipt, return a complete candidate as
`proposed` when an adapter handoff exists, or `not_persisted` when no usable
adapter/write authority exists. A proposal intent is always `not_persisted` and
`commit_eligible: false`. If the standalone adapter exits `6`, report
`outcome_unknown`, run `verify` and `load`, recover an unchanged stale lock if
necessary, then replay only the exact unchanged change set so idempotency
returns the stored receipt or commits it once.

An unresolved owner rule may be checkpointed only as
`awaiting_owner_rule` with an exact subject-bound
`required_owner_approvals` entry. That accepted receipt proves the checkpoint
was stored; it does not authorize execution. Do not enter `running` without a
host-supplied `execution_ref` and a `state_transition` approval bound to the
candidate revision and that ref. The skill may return the complete candidate
and required approval as `proposed`; it must not claim the transition entered
`running`.

When a pending request is withdrawn or made obsolete, the same candidate
revision that records the owner transition must append a matching
`pending_owner_resolutions` record and preserve the original request in
immutable history.
