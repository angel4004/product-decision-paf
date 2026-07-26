# Workflows

## PAF hypothesis review

1. Set the product/business goal and inspect current Nexus context.
2. Choose `null-base` when no evidence foundation exists; choose `data-base`
   when current behavior or product data can reveal an anomaly or bottleneck.
3. Classify the earliest uncertainty: customer/need, value proposition,
   solution, business model, acquisition/activation, onboarding, or
   business-model impact.
4. Preserve upstream dependencies. Do not use solution interest as proof of a
   need, value demand as proof of solution effectiveness, or feature use as
   proof of business impact.
5. Create one `assets/hypothesis-card-template.md` with the experiment,
   primary and guardrail metrics, threshold/control, sample, conditions, and
   confirm/disconfirm/inconclusive decisions.
6. Use Understand → Identify → Execute. Execute at scale only after the
   relevant solution is supported; then measure goal attainment and add all
   new knowledge back to context.

Value proposition and solution hypotheses may share one experiment when a
concrete interaction is required to test value. Keep the two claims, metrics,
and conclusions distinct.

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
   `missing`; record confirmation, disconfirmation, and unexpected knowledge.
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

## Recovery

If a source read, model turn, or tool fails, preserve the decision state:
available facts, missing source, blocked claim, chosen artifact, and next retry.
Standalone use can describe this checkpoint but cannot persist or resume it
without host support.
