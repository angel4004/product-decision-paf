# Claim boundaries

## General rule

Match wording strength to evidence strength. A user request, executive opinion,
model output, demo reaction, interview interest, or completed artifact is not
enough to confirm a market or business outcome.

## Claim requirements

| Claim | Minimum evidence dimensions | Safe wording when incomplete |
|---|---|---|
| PMF | Chosen metric, target segment, cohort or repeat-use evidence, retention or replacement behavior, period and denominator | `PMF: evidence pending; current signals are ...` |
| PCF | Evidence that customers choose the product as a primary way to close the need, alternatives considered, repeat behavior, segment and sample | `PCF: evidence pending; positive reactions do not yet show product choice.` |
| Business impact | Baseline, counterfactual or comparison, attribution, time window, denominator, uncertainty | `Business impact is not verified; the mechanism remains a hypothesis.` |
| Customer success | Defined customer outcome, eligible population, achieved count, denominator, period, exclusions | `Observed outcome for the reviewed cases; general customer success is not established.` |
| "Users need this" | Target segment, observed problem, frequency/severity, current workaround, choice or willingness evidence | `Need signal observed in the reviewed sample; prevalence is unknown.` |
| "This will improve the metric" | Causal mechanism, baseline, expected leading indicator, experiment or credible comparison, guardrails | `Metric impact is a hypothesis to test.` |
| Evidence-backed readiness | Required source coverage, passing checks, unresolved risks, approval and host-runtime evidence | `Review is instruction-supported; host verification remains required.` |
| PAF consistency | Goal and Nexus context, correct hypothesis class, upstream knowledge, validation design, result, decision rule, and new knowledge | `PAF review completed; unresolved hypothesis or evidence gaps block the downstream claim.` |

No fixed universal threshold proves PMF or PCF. The decision owner must define the
metric and threshold for the product stage before interpreting results.

Do not invent a PAF Confidence Point. If the host uses one, expose the evidence
and decision rule that caused it to change.

## Disputed-claim response

Keep the response compact:

1. **Evidence:** qualifying observations and source scope.
2. **Missing:** decision-critical evidence or denominator.
3. **Blocked claim:** wording that cannot be supported.
4. **Safe statement:** strongest statement the evidence permits.
5. **Next step:** one validation action and its pass/fail rule.

Do not offer to rewrite the blocked claim as marketing copy. Do not hide
completed-state wording inside a disclaimer or call it a hypothesis.

## Readiness language

Use `enforced` only for a boundary mechanically controlled by the current host.
Use `script-checked` for deterministic package checks, `instruction-supported`
for behavior encoded only in skill text, `host-required` for missing runtime
proof, and `not-supported-standalone` when standalone operation cannot provide
the mechanism.
