# PAF principles

## Terminology and provenance

In this package, **PAF** means **Product Architecture Framework**, the product
management methodology authored by
[Sergey Tikhomirov](https://productframework.ru/). The primary overview is the
[official PAF guide](https://productframework.ru/ops/main).

PAF methodology and the Bayram-informed skill architecture are separate layers:
PAF structures product context, hypotheses, and decisions; the architecture
reference assigns identity, memory, tools, permissions, recovery, and outcome
verification between the skill and its host. Do not attribute the package's
runtime architecture to PAF.

## Purpose in this skill

Use PAF to decide which uncertainty blocks a product goal, which hypothesis is
upstream, what evidence can resolve it, and how the result changes the current
product context. Read
[`paf-hypothesis-method.md`](paf-hypothesis-method.md) for the operational
method and official source links.

PAF is not a composite maturity score, a checklist total, or permission to
confirm PMF, PCF, business impact, customer success, or user need from weak
proxies.

## Core invariants

1. **Goal and Nexus before artifact.** Establish the product goal, current
   product/business/market context, gap, and decision before selecting a
   document or solution.
2. **Choose null base or data base honestly.** Existing behavioral data may
   identify a bottleneck; absent data requires discovery from upstream
   customer/need assumptions.
3. **Follow Und-Id-Ex.** Understand the constraint, identify and test ways to
   remove it, execute supported changes, verify the goal, and update context.
4. **Separate hypothesis classes.** Keep customer/need, value proposition,
   solution, and business-model claims distinct, including in a permitted
   value-plus-solution co-test.
5. **Preserve dependency.** Downstream evidence cannot silently prove an
   upstream claim.
6. **Predeclare the decision rule.** A Hypothesis Card states the hypothesis,
   method, metrics and thresholds, conditions, audience/sample, and actions for
   confirmation or refutation; it also preserves new knowledge.
7. **Do not manufacture certainty.** Report evidence per claim as `supported`,
   `partial`, `contradictory`, or `missing`. Do not average the chain or invent
   an overall PAF/Confidence score.
8. **Distinguish shipping from outcome.** Go-to-market and onboarding describe
   delivery and value access; post-release evidence must still establish impact.
9. **Let disconfirmation improve the Nexus.** A failed hypothesis can be useful
   when the experiment is valid and its knowledge changes the next decision.

## Product-decision review

Inspect these links:

- **Goal → uncertainty:** what must become known or changed to advance the goal?
- **Nexus → hypothesis:** which current facts and gaps justify this hypothesis?
- **Upstream → downstream:** are prerequisite customer/need and value claims
  supported, explicitly co-tested, or still open?
- **Hypothesis → experiment:** could the evidence confirm or refute the claim?
- **Evidence → decision:** do the observed result and validity support the
  wording and chosen action?
- **Decision → outcome:** what external state or metric will verify that the
  executed change advanced the goal?

Return the evidence state for each material link, blocked claims, and one
decision-relevant next step. A polished artifact alone closes none of these
links.
