# PAF hypothesis method

## Contents

- [Provenance and adaptation](#provenance-and-adaptation)
- [1. Begin with the goal and Nexus](#1-begin-with-the-goal-and-nexus)
- [2. Select the evidence base](#2-select-the-evidence-base)
- [3. Run Und-Id-Ex](#3-run-und-id-ex)
- [4. Classify the hypothesis](#4-classify-the-hypothesis)
- [5. Enforce upstream dependency](#5-enforce-upstream-dependency)
- [6. Use one Hypothesis Card](#6-use-one-hypothesis-card-per-tested-hypothesis)
- [7. Make a decision without a fake score](#7-make-a-decision-without-a-fake-score)

## Provenance and adaptation

Here **PAF** means **Product Architecture Framework**, authored by
[Sergey Tikhomirov](https://productframework.ru/). This reference is a condensed
English adaptation for product-decision reviews, not a new expansion of the PAF
acronym and not a verbatim copy.

Primary PAF sources:

- [AI Product Operations / PAF guide](https://productframework.ru/ops/main)
- [Feature Life Cycle](https://productframework.ru/feature_life_cycle)
- [Hypothesis](https://productframework.ru/hypothesis)
- [Customer hypotheses](https://productframework.ru/hypotheses/customer)
- [Value proposition hypotheses](https://productframework.ru/hypotheses/value_proposition)
- [Solution hypotheses](https://productframework.ru/hypotheses/solution)
- [Business model hypotheses](https://productframework.ru/hypotheses/business_model)

See [`NOTICE.md`](../NOTICE.md) for attribution and the CC BY-SA 4.0 boundary.

## 1. Begin with the goal and Nexus

PAF starts product development from a goal and the current context, not from a
requested artifact or an ungrounded feature list. A **Nexus** is the maintained
information model of the product, business, and market that supplies sufficient
decision context. Compare the current state with the target, identify the gap,
and state which uncertainty blocks the goal.

A hypothesis is useful only when its resolution can update the Nexus or change
a decision about that gap. Record the goal, object of change, target condition,
known context, missing context, and decision that the evidence will enable.

## 2. Select the evidence base

- **null base**: the team lacks a usable product-data foundation. Start discovery
  with customer/need hypotheses, then validate value propositions and their
  implementation. Do not use solution polish as a substitute for upstream
  evidence.
- **data base**: an existing product supplies behavioral evidence that can reveal
  bottlenecks. Start from the observed bottleneck, but reopen upstream
  customer/need or value assumptions when the data does not establish them.

The distinction determines where investigation begins; it does not lower the
evidence standard or make downstream evidence prove an upstream claim.

## 3. Run Und-Id-Ex

The PAF guide describes **Understand, Identify, Execute (Und-Id-Ex)**:

1. **Goal** — define the product-development goal.
2. **Understand** — inspect the Nexus and determine what currently constrains
   the goal; formulate research questions or hypotheses where context is weak.
3. **Identify** — generate and test candidate ways to remove the bottleneck;
   update the Nexus as evidence arrives.
4. **Execute** — scale a supported solution and check whether the goal is
   actually reached.
5. Repeat with the updated Nexus.

Execute is not permission to skip validation, and shipping is not proof of
impact.

## 4. Classify the hypothesis

| Class | Decision question | Typical evidence |
|---|---|---|
| Customer / need | Does this segment actually behave, think, feel, struggle, or pursue the goal as proposed? | Past behavior, observation, interviews, qualified surveys, product behavior |
| Value proposition | Does the proposed benefit address that validated need and produce measurable demand or benefit? | Demand test, offer response, observed benefit, declared success criterion |
| Solution | Does this implementation let the user obtain the intended result at the required level? | Prototype or product behavior, task success, controlled comparison, usability evidence |
| Business model | Can the linked product and business metrics reach a scalable or company-goal configuration? | Financial model, funnel/unit-economics evidence, direct or inverse model constraints |

Go-to-market, acquisition, onboarding, and post-release impact are context
around these hypotheses, not evidence-free shortcuts. A launch plan explains
delivery; onboarding evidence shows whether users reach value; impact evidence
checks whether the released change advanced the product or business goal.

## 5. Enforce upstream dependency

Default dependency:

`customer/need → value proposition → solution → business model and impact`

A downstream result cannot silently repair a missing upstream link. For
example, prototype usage may support a solution claim but does not by itself
prove that the underlying need is important or that the business model scales.

PAF explicitly allows an important practical exception: value proposition and
solution validation may be the **same experiment** when users need a concrete
solution to experience the value. Co-test them, but keep two hypotheses, two
success criteria, and two conclusions. Evidence may resolve one and leave the
other open.

## 6. Use one Hypothesis Card per tested hypothesis

The official Feature Life Cycle describes a dynamic **Hypothesis Card** that
contains the hypothesis, validation method, and result, including:

- reason the hypothesis arose;
- primary and secondary result metrics with control/threshold values;
- expected effect and experiment conditions;
- audience segment and sample size;
- action plan for confirmation and for refutation;
- new knowledge obtained during validation.

For an auditable review, also record safe source refs, collection period,
material exclusions, validity threats, owner, and next decision. These are
package-level evidence fields, not claimed as verbatim PAF template fields.

PAF does not supply universal thresholds or sample sizes for every hypothesis.
When the user or evidence has not set them, label proposed numbers as explicit
decision-owner assumptions and explain the trade-off they encode. Do not make an
arbitrary threshold look like a methodology requirement.

## 7. Make a decision without a fake score

Normalize the card outcome as:

- **confirmed** — predeclared success criteria were met with evidence adequate
  for the stated claim;
- **disconfirmed** — criteria were not met and the experiment was valid enough
  to reject or revise the hypothesis;
- **new knowledge / unresolved** — the work changed the Nexus but cannot decide
  the hypothesis because evidence is partial, contradictory, or invalid.

The labels above operationalize PAF's confirmation/refutation plans and its
requirement to preserve new knowledge; they are not presented as an official
three-value PAF enum.

Do not calculate an overall PAF score or invent numeric **Confidence**. The PAF
guide discusses team Confidence Point as context grows, but this skill reports
evidence and uncertainty per hypothesis and dependency. Without a declared,
validated measurement method, use `supported`, `partial`, `contradictory`, or
`missing`, then name one decision-relevant next step.
