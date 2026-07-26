# Evaluation suite

These cases test the portable behavior contract of `product-decision-paf`.
They are not proof that a model followed the skill, that a host enforced an
approval, or that an external outcome occurred.

## Case format

Every `evals/cases/**/*.json` file is a single JSON object that can be parsed
with the Python standard library. Required fields:

- `id`: stable case identifier;
- `case_id`: compatibility alias equal to `id`;
- `mode`: `standalone` or `embedded-robin`;
- `prompt`: user or host input to evaluate;
- `expected`: semantic behaviors that must be present;
- `forbidden`: semantic claims, effects, or response patterns that must be absent;
- `tags`: coverage labels;
- `source_refs`: source rules, evals, or target contract sections adapted by the
  case.

`expected` and `forbidden` are rubric statements, not literal substring
assertions unless a statement explicitly says that exact wording is required.
A behavior runner or human/model grader is still required.

Every `source_refs` value must be either an existing package-relative file or an
HTTPS source. Source-repository lineage is pinned to audited commit
`bb67e75a2c561c6aa90c779a9c5429b7b8383e2f`; opaque local-workspace refs are not
accepted by the validator.

Parse all cases without third-party packages:

```powershell
python -c "import json,pathlib; files=list(pathlib.Path('evals/cases').rglob('*.json')); [json.loads(p.read_text(encoding='utf-8')) for p in files]; print(f'parsed {len(files)} cases')"
```

Run the package validator from the repository root:

```powershell
python scripts/quick_validate.py
```

## Official PAF hypothesis-method layer

The skill architecture, host boundaries, and publication discipline follow the
Bayram/Robin system-design rules in the goal prompt. Hypothesis behavior is
evaluated against the official Product Architecture Framework (PAF), not
against a generic goal-artifact lens.

Official primary sources reviewed on 2026-07-25:

- https://productframework.ru/ops/main
- https://productframework.ru/product_discovery
- https://productframework.ru/feature_life_cycle
- https://productframework.ru/hypotheses/customer
- https://productframework.ru/hypotheses/value_proposition
- https://productframework.ru/hypotheses/solution
- https://productframework.ru/hypotheses/business_model

The PAF-specific cases enforce these distinctions:

- `null base`: with no product-behavior foundation, validate customer/need
  hypotheses before value propositions and validate value before treating a
  solution as supported;
- `data base`: for an existing product, start from the current Nexus/context,
  observed behavior, anomaly and root cause/bottleneck before proposing a
  feature;
- customer, value proposition, solution and business-model hypotheses have
  different objects, evidence and claims;
- an upstream signal does not validate a downstream claim;
- value and solution may be co-tested in one experiment, while their statements,
  metrics, evidence and decisions remain separate;
- Und-Id-Ex means Understand, Identify and Execute, followed by Harvesting the
  result and new knowledge back into the Nexus;
- Confidence Point must not be fabricated as a score when the current stage,
  context/risk evidence, scale, gates and cost-of-risk inputs are absent.
- PAF requires decision criteria and experiment conditions to be explicit, but
  does not make an unsourced threshold, sample size or time window an official
  default. A concrete number introduced without source evidence must be labelled
  `proposed assumption`, include its rationale, and remain subject to owner
  approval before it becomes a decision rule.

## Coverage

`allow_implicit_invocation` is `false`. Therefore positive activation fixtures
grade routing suitability and behavior after an explicit user invocation or an
intentional host `route -> invoke -> grade` step. They are not evidence of
implicit host activation. Negative activation fixtures grade routing out of
scope or refusal after an explicit but unsuitable invocation.

| Requirement | Cases | Main source adaptation |
|---|---|---|
| Positive activation | `activation-product-hypothesis`, `activation-paf-review`, `activation-pmf-pcf-evidence`, `activation-product-passport`, `activation-next-product-step`, `activation-artifact-claims`, `activation-cpo-argument` | `AGENTS.md`; `workflows/activation/activate-cpo-copilot.md`; `practices/copilot-ux/dialogue-first.md`; `references/routing.md` |
| Negative activation | `coding-task-no-activation`, `root-agent-refusal`, `private-memory-refusal`, `external-write-without-approval`, `visual-landing-no-activation`, `regulated-advice-out-of-scope` | Source `AGENTS.md` runtime/permission boundary, adapted to the narrower skill scope |
| PAF review | `activation-paf-review`, `activation-artifact-claims`, `disputed-pmf-contradictory`, `scoped-pmf-evidence` | `evals/behavior/paf-conflict-case.yaml`; `workflows/reviews/paf-consistency-review.md` |
| Forbidden claims | `forbidden-pmf-marketing-bypass`, `forbidden-business-impact`, `customer-success-metric-uplift` | Source PAF negative evals and `practices/paf/evidence-and-uncertainty.md` |
| Insufficient evidence | `insufficient-evidence-next-step`, `disputed-pcf-demo-reaction` | `evals/behavior/evidence-gap-case.yaml`; `evals/behavior/paf-weak-evidence-recommendation-negative.yaml` |
| Realistic passport | `realistic-project-passport` | `workflows/onboarding/create-project-passport.md`; `assets/product-passport-template.md` |
| Existing passport review | `existing-passport-review` | `evals/behavior/existing-passport-review-case.yaml`; `workflows/onboarding/review-existing-passport.md` |
| Disputed PMF/PCF | `disputed-pmf-contradictory`, `disputed-pcf-demo-reaction`, `scoped-pmf-evidence` | `evals/behavior/paf-pmf-without-evidence-negative.yaml`; `paf-pcf-without-evidence-negative.yaml`; `paf-contradictory-evidence-negative.yaml` |
| Client feedback intake | `client-feedback-intake` | `evals/behavior/client-feedback-intake-case.yaml`; `practices/copilot-ux/dialogue-first.md` |
| UI evidence boundary | `ui-evidence-gate` | `evals/behavior/ui-evidence-gate-case.yaml`; `practices/copilot-ux/artifact-boundaries.md` |
| Robin embedded mode | `robin-embedded-review`, `robin-permission-expansion` | Goal prompt embedded-mode requirements; `references/robin-embedded-mode.md` |
| Standalone enforcement boundary | `standalone-enforcement-boundary` | `docs/runtime-contract.md`; `docs/paf-enforcement-proof.md`; `references/enforcement-boundary.md` |
| Privacy/publication | `privacy-publication-boundary`, `private-memory-refusal` | Source privacy/redaction boundary and goal prompt publication rules |
| External write | `external-write-without-approval`, `robin-permission-expansion` | Source `AGENTS.md` permissions; host-owned boundary |
| Root-agent refusal | `root-agent-refusal` | Goal prompt identity boundary; `references/robin-embedded-mode.md` |
| Out of scope | `coding-task-no-activation`, `visual-landing-no-activation`, `regulated-advice-out-of-scope` | Goal prompt activation-negative list; `references/routing.md` |
| PAF null-base sequence | `paf-null-base-customer-value-solution` | Official PAF main, Product Discovery and customer-hypothesis pages |
| PAF data-base start | `paf-data-base-nexus-bottleneck` | Official PAF main and Feature Life Cycle pages |
| Hypothesis type classification | `paf-hypothesis-type-classification` | Official customer, value-proposition, solution and business-model hypothesis pages |
| Upstream stage gate | `paf-upstream-gate-no-downstream-claim` | Official Product Discovery and Feature Life Cycle stage order |
| Value and solution co-test | `paf-value-solution-cotest` | Official Feature Life Cycle value/solution validation rule |
| Complete Hypothesis Card | `paf-hypothesis-card-complete` | Official hypothesis pages and Feature Life Cycle artifact model |
| Und-Id-Ex and Harvest | `paf-und-id-ex-harvest` | Official PAF main process and Harvesting event |
| Confidence Point boundary | `paf-confidence-point-no-fake-score` | Official PAF main Confidence Point definition |
| No invented PAF defaults | `paf-no-invented-threshold` | Official PAF hypothesis templates require criteria, while the concrete values remain context-dependent |

## Important source adaptations

The source behavior YAML files describe expected behavior but do not execute a
model. They are retained as case lineage, not represented as deterministic
enforcement.

The source `evals/behavior/onboarding-minimal-case.yaml` expects a project
passport for a new-product prompt. Newer source rules in
`workflows/activation/activate-cpo-copilot.md` and
`practices/copilot-ux/goal-led-validation.md` explicitly forbid a passport as
the first artifact for a raw new idea unless the user asks for one. This suite
uses the newer rule: first validation step for a raw idea; compact passport for
an explicit passport request.

The source missing-trace and missing-methodology cases depend on the source
workspace runner, hooks, memory manifest, and host reports. A standalone skill
cannot recreate those mechanisms. `standalone-enforcement-boundary` therefore
checks honest status language: static validation is `script-checked`; behavior
is `instruction-supported`; live source, approval, trace, receipt, and outcome
proof are `host-required` or `not-supported-standalone`.

The source repository has structural activation checks, but no complete
standalone activation behavior suite for all positive and negative examples in
the goal prompt. The cases here add those missing controls without importing
private memory, traces, receipts, or source runtime state.

The original portable cases use a compact goal/evidence/artifact vocabulary.
That vocabulary remains useful for response structure, but it is not treated as
the PAF hypothesis method. The `paf-hypothesis-method` cases are the regression
authority for null-base/data-base routing, hypothesis types, stage gates,
Hypothesis Cards, Und-Id-Ex, Harvesting and Confidence Point behavior.
