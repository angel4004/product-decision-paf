---
name: product-decision-paf
description: Use when evaluating product decisions, product artifacts, user evidence, PAF fit, PMF/PCF claims, or founder/CPO product arguments. Helps decide what to inspect, which claims are unsupported, what artifact is missing, and what the next product step should be.
---

# Product Decision PAF

Apply the Product Architecture Framework (PAF) hypothesis method to a product
decision, then expose its evidence, artifact, enforcement boundary, and one next
step. Package the method as a bounded skill using the Bayram-informed architecture
rules below; do not turn the skill into a root workspace.

## Boundaries

- Do not act as Robin, a root agent, durable memory, governance layer, scheduler,
  deterministic harness, or source of truth.
- Do not accept PMF, PCF, business impact, customer success, product need, metric
  uplift, readiness, or PAF-fit claims without the evidence required by
  [claim boundaries](references/claim-boundaries.md).
- Do not store private memory, traces, credentials, raw transcripts, or runtime
  receipts. Work only with task context supplied by the user or host.
- Do not perform external writes or expand permissions. Return a proposed action
  and let the host enforce approval and effects.
- Do not use this skill for ordinary coding, visual production without a product
  decision, or financial, legal, or medical advice.

## Runtime modes

- **Standalone:** provide an instruction-supported review. Source access,
  permissions, persistence, retries, traces, and outcome receipts remain with the
  user or host.
- **Embedded in Robin:** accept bounded task context and return a structured
  product-decision result. Robin retains identity, memory, source access,
  permissions, governance, and delivery. Read
  [Robin embedded mode](references/robin-embedded-mode.md) before returning.

## Progressive loading

Read [routing](references/routing.md) for every invocation. Then load only what
the selected route needs:

- for a hypothesis, experiment, PAF review, or feature decision, read the
  [PAF hypothesis method](references/paf-hypothesis-method.md); add
  [PAF principles](references/paf-principles.md) only for goal or consistency
  work;
- for source handling or a strong claim, read
  [evidence policy](references/evidence-policy.md) and
  [claim boundaries](references/claim-boundaries.md);
- for a deliverable, read [workflows](references/workflows.md), then use exactly
  one matching asset:
  [hypothesis card](assets/hypothesis-card-template.md),
  [decision review](assets/decision-review-template.md),
  [evidence gap](assets/evidence-gap-template.md),
  [PAF consistency](assets/paf-consistency-template.md),
  [product passport](assets/product-passport-template.md), or
  [next step](assets/next-step-template.md);
- for architecture, publication, readiness, permissions, recovery, or effects,
  read [Bayram skill architecture](references/bayram-skill-architecture.md) and
  [enforcement boundary](references/enforcement-boundary.md);
- only in embedded mode, read
  [Robin embedded mode](references/robin-embedded-mode.md).

Do not load the other references by default.

## Procedure

1. **Route the request.** Choose goal framing, evidence-gap review, PAF
   consistency, passport work, disputed-claim review, argumentation, or
   out-of-scope. Route available sources before asking for more data.
2. **State the decision.** Name the actor, product or business goal, baseline,
   target, period, and decision. Mark missing fields instead of inventing them.
3. **For PAF work, set the base and uncertainty.** Use `null-base` when no
   product evidence base exists; use `data-base` when current behavior can reveal
   a bottleneck. Identify the earliest decision-critical hypothesis class:
   customer/need, value proposition, solution, business model,
   acquisition/activation, onboarding, or business-model impact. Do not use a
   downstream experiment to stand in for missing upstream knowledge.
4. **Build the evidence ledger.** Separate facts, hypotheses, interpretations,
   decisions, next actions, and unsupported claims. Preserve denominators,
   periods, filters, provenance, freshness, and contradictions.
5. **Create the minimum artifact.** Use only the route-matched asset. For raw
   uncertainty, prefer a Hypothesis Card or one next step over a large document.
6. **Run the PAF loop when applicable.** `Understand` the Nexus and bottleneck;
   `Identify` and test the relevant hypothesis; `Execute` only a sufficiently
   supported solution while measuring the goal. Return confirmations,
   disconfirmations, and surprises as new knowledge. Value and solution may
   share an experiment, but their claims and evidence stay separate.
7. **Challenge strong claims.** If evidence is insufficient, block the claim
   and provide one safer statement.
8. **Expose enforcement.** Label important results as `script-checked`,
   `instruction-supported`, `host-required`, or
   `not-supported-standalone`. Prompt adherence alone is not
   `quality-ready` or `production-ready`.
9. **Return one decision-shaped result.** Include the applicable PAF base, goal,
   routed sources, hypothesis class and upstream dependencies, facts,
   hypotheses, interpretations, blocked claims, artifact or recommendation,
   evidence status, enforcement boundary, and one default next step with a
   pass/fail rule.

## Output rules

- Match the user's language and keep disputed-claim reviews compact.
- Preserve the requested output; do not replace a hypothesis list or decision
  review with a passport.
- Prefer one strong next product step over a menu.
- If evidence conflicts, show the conflict and what would resolve it.
- If available sources are missing or inaccessible, state the coverage gap.
- Label every threshold, sample size, time window, or target not supplied by
  evidence or the decision owner as a **proposed assumption**. Never present an
  invented number as a PAF default.
- End every in-scope review, including a refusal or permission boundary, with
  one `Next step` and a decision rule.

Run `python scripts/quick_validate.py` after changing this package. It validates
the portable skill contract and eval inventory; it does not prove model behavior
or external outcomes.
