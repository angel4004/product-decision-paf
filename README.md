# product-decision-paf

`product-decision-paf` is a portable Agent Skill for reviewing product
decisions through an evidence-first PAF lens.

Use it to:

- clarify the product goal before creating or approving an artifact;
- separate facts, hypotheses, interpretations, decisions, and unsupported
  claims;
- review evidence gaps and PAF consistency;
- create or improve a product passport;
- challenge PMF, PCF, business-impact, customer-success, readiness, user-need,
  and metric-uplift claims;
- choose one strong next product step with a pass/fail decision rule.

The skill connects four things:

1. the human or business outcome;
2. the product artifact under review;
3. the user and market evidence;
4. the next decision.

It does not turn PAF into a score. Weak or missing evidence stays weak or
missing; it is not averaged into a confident verdict.

## PAF hypothesis method

In this repository, hypotheses follow the official **Product Architecture
Framework (PAF)** methodology.

Start from the product-development goal, then choose the evidence situation:

- **null base:** there is no sufficient existing product evidence, so discovery
  starts from the beginning and validates customer/need, value-proposition, and
  solution hypotheses in sequence;
- **data base:** an existing product already provides behavioral evidence, so
  the team starts from observed constraints or bottlenecks and identifies which
  product change may reduce the relevant risk.

The simplified PAF **Und-Id-Ex** loop is:

1. define the product-development goal;
2. **Understand:** inspect the current product, business, and market context,
   find what constrains the goal, and identify missing knowledge;
3. **Identify:** form and test candidate hypotheses, update the evidence and
   confidence, and select a supported solution;
4. **Execute:** scale the supported solution, observe whether it changed the
   goal, preserve the new knowledge, and begin the next loop.

The core hypothesis chain is:

```text
customer and need -> value proposition -> solution
```

A solution decision is still incomplete without relevant business-model,
go-to-market and distribution, onboarding and adoption, and measured-impact
context. The skill must not treat a validated prototype as proof of demand,
adoption, monetization, or business impact.

Each tested hypothesis should have one dynamic **Hypothesis Card** recording its
origin, primary and supporting metrics with thresholds, expected effect and
experiment conditions, audience and sample, actions for confirmation and
refutation, and the new knowledge produced by validation.

Read [`references/paf-hypothesis-method.md`](references/paf-hypothesis-method.md)
when defining, reviewing, or sequencing hypotheses.

## A skill, not a Copilot or root agent

This repository packages one product-decision capability. It is not a second
root workspace and does not replace Robin, Codex, a CPO, or another host agent.

The package owns:

- task routing inside its product-decision scope;
- evidence and claim-review instructions;
- PAF-oriented references and workflows;
- reusable decision templates;
- static package checks and eval cases.

The host still owns:

- identity, voice, and user profile;
- source and connector access;
- private or durable memory;
- permissions, approvals, budgets, and external effects;
- scheduling, retries, recovery, traces, and runtime receipts;
- delivery and verification of external outcomes.

The skill may recommend an action. It cannot authorize or execute that action
unless a host separately provides and enforces the required capability.

This separation is **Bayram-informed skill architecture**, not a redefinition
of PAF. It maps a human request to a system function, a concrete artifact, the
runtime or host mechanism that can enforce it, the evidence and evals that test
it, and an observable external outcome. Read
[`references/bayram-skill-architecture.md`](references/bayram-skill-architecture.md)
when deciding whether a responsibility belongs in the portable skill or in its
host.

## When to use it

Invoke the skill for product-decision work such as:

```text
$product-decision-paf Review this product hypothesis and identify the evidence gap.
```

```text
$product-decision-paf Check whether this artifact supports the PMF claim and choose the next product step.
```

```text
$product-decision-paf Turn this context into a product passport without inventing missing evidence.
```

Do not use it as the primary tool for:

- ordinary coding without a product-decision question;
- visual production without a product-decision review;
- becoming or replacing Robin;
- storing personal memory;
- performing an external write;
- financial, legal, or medical advice.

## Standalone use

If you are the repository owner or otherwise have separate permission to use
the unlicensed package, point a compatible Agent Skills host at this checkout.
Then invoke `$product-decision-paf` explicitly and provide the decision context
and any available evidence. Public visibility is not permission to copy,
redistribute, or modify the unlicensed portions; see
[`NOTICE.md`](NOTICE.md) and [License status](#license-status).

A useful request includes:

- the outcome and actor;
- the current product state or baseline;
- the decision to make;
- the artifact being created or reviewed;
- source references, periods, denominators, and filters;
- known constraints and the decision deadline.

Standalone mode is instruction-supported. The skill can structure the review,
block unsupported claims, and recommend a next step. It does not gain source
access, durable memory, deterministic enforcement, or outcome receipts merely
because it was invoked.

## Embedded use in Robin

Robin should remain the root agent.

1. Robin identifies the product-decision task and gathers only the required
   source observations.
2. Robin invokes `$product-decision-paf` with bounded task context.
3. The skill returns a structured review: goal, sources, facts, hypotheses,
   interpretations, blocked claims, evidence status, enforcement boundary, and
   one next step.
4. Robin applies its own identity, memory, permissions, approvals, governance,
   and delivery rules.

The skill must not write Robin memory, expand permissions, call connectors on
its own authority, or present itself as Robin.

## Evidence-backed use

An evidence-backed result identifies enough of the following to let another
person inspect the claim:

- source and provenance;
- freshness and observation period;
- denominator, segment, and filters;
- measurement or research method;
- contradictions and missing coverage;
- the decision that the evidence can and cannot support.

The output must distinguish:

- facts;
- hypotheses;
- interpretations;
- decisions;
- next actions;
- claims that remain unsupported.

PMF, PCF, business impact, customer success, readiness, user need, and metric
uplift are not accepted from confidence, a polished artifact, or a single
unqualified observation. When evidence is insufficient, the correct result is
to block the strong claim, offer a safer statement, and choose one
uncertainty-reducing next step.

## Enforcement boundaries

The package uses explicit enforcement labels:

- `script-checked`: a deterministic local check verified the package property;
- `instruction-supported`: the behavior is specified for the model but is not
  mechanically guaranteed;
- `host-required`: the host must enforce the behavior or supply the evidence;
- `not-supported-standalone`: standalone skill execution cannot provide it.

Passing a structural validator does not prove model behavior, factual truth, or
external product impact.

## Checks and evals

Run the local package validator from the repository root:

```text
python scripts/quick_validate.py
python -m unittest discover -s tests -p "test_*.py" -v
```

The validator checks the portable skill contract, required references and
assets, publication hazards, all 37 required eval IDs, their mapping to the 12
quality-critical invariants, and required documentation. The unit tests prove
that removing a required regression case or invariant mapping, or using an
unresolved provenance ref, fails closed. Review the exact output before making
a release claim.

The eval suite covers:

- positive and negative activation;
- PAF and product-passport reviews;
- forbidden strong claims;
- insufficient-evidence responses;
- Robin embedded-mode boundaries;
- privacy and publication boundaries.

Eval cases are behavioral test inputs and expected outcomes. Their presence is
not evidence that a particular model passed them. This migration ran six
targeted fresh-context reviews, but not the complete 37-case host harness.
Therefore model behavior remains `instruction-supported`; a
behavior-verified release would additionally require the full host run, failure
review, and an immutable receipt. Claims about business value require a real
external outcome.

See:

- [`docs/migration-map.md`](docs/migration-map.md) for source classification;
- [`docs/equivalence-coverage.md`](docs/equivalence-coverage.md) for
  quality-critical behavior coverage;
- [`docs/release-checklist.md`](docs/release-checklist.md) for release gates;
- [`references/paf-hypothesis-method.md`](references/paf-hypothesis-method.md)
  for the official PAF hypothesis sequence used by the skill;
- [`references/bayram-skill-architecture.md`](references/bayram-skill-architecture.md)
  for portable-skill and host ownership boundaries;
- [`NOTICE.md`](NOTICE.md) for attribution and licensing boundaries.

## Portability

The selected mode is **Cross-platform**.

Package paths are repository-relative, and the release check uses Python rather
than the source workspace's PowerShell-only runtime. A release should run the
same validation and eval commands on Windows and at least one Unix-like host.
The repository's `validate` workflow runs the static package gate on Windows
and Ubuntu with supported Python versions. A local Windows-only pass is not
cross-platform evidence.

The package still requires a compatible Agent Skills host. Host-specific
connectors, hooks, schedulers, memory systems, and approval mechanisms are
integrations, not part of the portable contract.

## Activation policy

`allow_implicit_invocation` is deliberately set to `false`.

The skill covers a broad product domain, while several negative cases must stay
outside its authority, including ordinary coding, root-agent identity, memory,
and external writes. Explicit `$product-decision-paf` invocation makes the
capability boundary visible and reduces accidental activation. A host may still
route a task to the skill intentionally after applying its own policy.

## PAF terminology and provenance

Within this repository, **PAF means Product Architecture Framework**. No
alternate expansion is used by this package.

The official materials identify Sergey Tikhomirov as the author of Product
Architecture Framework and publish the framework and site materials under
CC BY-SA 4.0. Consult the
[official PAF site](https://productframework.ru/) and
[official guide](https://productframework.ru/ops/main).

This repository is an independent software skill and is not presented as an
official PAF distribution or as endorsed by the framework author. Official PAF
methodology and terminology must not be attributed to Bayram Annakov. The
Bayram-informed contribution here is the separate skill-architecture layer:
portable capability versus host ownership, evidence, evals, enforcement, and
external outcomes.

Any extension or interpretation that differs from the official methodology
must be labeled as an implementation choice rather than represented as official
PAF. See [`NOTICE.md`](NOTICE.md) for the compact provenance and licensing
boundary.

## License status

No software license has been selected for this repository yet. This README does
not grant a license or apply CC BY-SA 4.0 to the entire software package.

The audited source repository, `angel4004/cpo-codex-copilot`, also had no
top-level `LICENSE` file or package-level license metadata. Before calling this
repository open source, accepting outside reuse, or copying source text, the
owner should choose an explicit license and reconcile it with the provenance
and licensing of any adapted PAF material described in
[`NOTICE.md`](NOTICE.md). Until then, do not infer reuse rights from public
GitHub visibility alone.

## Known gaps

- Five targeted fresh-context forward scenarios were reviewed during the
  migration; the complete 37-case host harness and immutable behavior receipt
  remain unexecuted.
- Source access, permissions, writes, and receipts are host-required.
- Durable memory, autonomous scheduling, and deterministic recovery are not
  supported in standalone mode.
- The validator can detect selected structural and publication hazards, but it
  is not a complete legal, privacy, or secret-history audit.
- Cross-platform readiness requires successful validation outside the current
  Windows development host.
- External product impact requires follow-up evidence after a recommendation is
  acted on.
