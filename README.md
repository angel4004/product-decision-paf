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
- adapter-neutral versioned Nexus/Hypothesis schemas and persistence handoff;
- a cross-platform reference file adapter for explicitly authorized local state;
- static package checks and eval cases.

Here **Nexus** means the product-domain model of maintained facts,
interpretations, decisions, and unknowns. It is content with evidence and
supersession semantics, not a storage engine. The package defines that model;
the host stores and retrieves product-specific instances.

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
block unsupported claims, and recommend a next step. Invocation alone does not
create durable memory, source access, write authority, or outcome receipts.

## Long-term hypothesis work

Longitudinal work uses a portable state protocol:

```text
host loads versioned Nexus and Hypothesis Card
  -> skill returns proposal intent if required bindings are missing
  -> host/user resolves those bindings
  -> skill returns a complete atomic candidate change set
  -> authorized adapter validates and commits it
  -> adapter returns an accepted receipt
  -> next invocation receives the new snapshot and receipt
```

The skill owns the schemas and transition rules, not the stored product data.
The state must live outside this public package. This separation lets the same
skill work with a local file host, Robin, or another approved store.

There are two deliberately different portable artifacts:

- `proposal_intent` preserves known values and enumerates unresolved bindings.
  It is always `commit_eligible: false` and `not_persisted`;
- `hypothesis-change-set` contains the complete candidate state and exact
  manifest. Only this artifact can be offered to an adapter.

Lack of storage does not make a complete change set invalid: it can still be
returned as `not_persisted`. Lack of schema-required product, scope, owner, or
state bindings does: in that case the skill must return an intent rather than
invent values or mislabel a sketch as a transaction.

The product workspace preserves one Nexus across sequential
`decision_scope_log` entries. Each hypothesis is immutably bound to the scope in
which it was created. `owner_tenure_log` preserves changes in decision
ownership; old approvals remain auditable but do not authorize work under a new
tenure.

Evidence, Nexus entries, claim events, and post-release outcome events are
append-only. The active blocked claim set is derived from the latest event for
each logical claim in `claim_log`. Result learning enters the typed Nexus through
`result.new_nexus_entry_ids`; there is no second generic learning journal.
Every primary validation metric receives a structured `metric_results` record
before review or closure.

Nexus decision entries carry an exact `decision_authority` binding: canonical
subject hash, owner tenure, decision scope, safe receipt, and reversibility.
Pending owner requests may be resolved by an approval, explicitly withdrawn, or
invalidated in the same candidate revision that records an owner-tenure
transition; their prior request and resolution history remain auditable.

The default dependency chain is customer need → value proposition → solution.
The contract also supports explicitly bound co-tests for value proposition plus
solution and solution plus business model. Each peer keeps its own ID, approved
test contract, metric result, interpretation, and verdict. After a shared run,
one peer may close while the other remains reviewable under the same execution
evidence.

A supported upstream link must still cite current unsuperseded supported
evidence and current supported Nexus lineage. A historical closed/confirmed
card alone is not continuing authority. A new formulation may point to either a
closed or superseded historical replacement target without editing it.

For an explicitly selected absolute state root, a host can use the
standard-library reference adapter:

```text
python scripts/hypothesis_state.py validate-intent --intent <proposal-intent.json>
python scripts/hypothesis_state.py load --root <absolute-state-root>
python scripts/hypothesis_state.py commit --root <absolute-state-root> --change-set <change-set.json>
python scripts/hypothesis_state.py verify --root <absolute-state-root>
python scripts/hypothesis_state.py inspect-lock --root <absolute-state-root>
python scripts/hypothesis_state.py recover-lock --root <absolute-state-root> --expected-pid <dead-pid> --expected-token <lock-token>
```

There is deliberately no default state path, background process, network call,
delete command, or silent write. The root must be outside the skill repository.
It must also be an absolute, single-host local-filesystem root; the reference
adapter rejects Windows UNC roots and symlink/reparse-point state targets.
`commit` uses schema validation, subject-bound owner-tenure gates, host
execution refs, append-only state checks, optimistic workspace revisions, and a
lock. One atomic `hypothesis-state-bundle.json` contains:

- the authoritative `current_state`;
- compact hash-linked `revision_history` records whose delta hashes cover
  changed cards and appended decision scopes, owner tenures, Nexus entries,
  evidence, claim events, and outcome events;
- immutable changed-card revisions in `hypothesis_history`;
- current append-only Nexus, evidence, claim, and outcome logs;
- immutable receipts, handled-proposal commitments, and
  `proposal_history_head_sha256`.

The bundle uses compact incremental history instead of duplicating a complete
workspace snapshot for every revision.
Pending owner requests remain in each hypothesis record as
`pending_owner_approvals`, so an `awaiting_owner_rule` checkpoint can be resumed
without the originating change-set file. Matching
`pending_owner_resolutions` preserve a withdrawal or tenure-transition
invalidation without losing the original request from history. Exact proposal
replay returns the same receipt; reuse of an ID for different content fails
closed. Only an accepted persistence receipt supports the word `persisted`.

The reference file host is intentionally bounded to 32 MiB and 10,000 accepted
workspace revisions. Crossing either guard fails closed and requires migration
of the same portable contract to a transactional host. The adapter does not
silently compact, truncate, or discard history.

After a crash, `inspect-lock` is read-only. Recovery requires both the exact
dead PID and the opaque token returned for that unchanged lock. It removes only
lock-owned files. Lock publication and recovery share a short-lived
operating-system advisory gate, preventing a new commit from publishing a
replacement lock during the recovery recheck/unlink window.

If post-result cleanup cannot remove the command's own lock, the adapter emits
a safe `lock_cleanup_required` warning on stderr. That warning does not change
an already-known `accepted`, `rejected`, or `conflict` result or its exit code.
Use its opaque `lock_id` with `inspect-lock`; after the owner process is proven
dead, use exact-token `recover-lock`. This differs from exit code `6`, where the
persistence outcome itself is unknown.

The adapter's sensitive-data scan catches obvious credentials, private paths,
emails, phone-like strings, and raw-private-content markers. It is a bounded
guard, not a complete privacy proof; a production host still owns access,
retention, structured PII controls, and backups.

Only an `accepted` receipt proves that the adapter accepted the exact proposal,
used its atomic-replace protocol, and read back the exact bundle. Its
`durability_scope` is
`atomic_replace_with_readback_power_loss_host_dependent`: backup, storage-stack,
and power-loss guarantees remain host responsibilities. Exit code `6` reports
`OUTCOME UNKNOWN`; replacement may have occurred but readback or durability
verification did not establish the result. Run `verify` and `load`, recover an
unchanged stale lock if necessary, and replay only the exact unchanged change
set. Idempotent replay returns the stored receipt if the first attempt was
handled, or commits that one proposal if it was not.

Canonical hashing rejects duplicate keys, non-standard numeric constants,
floats, non-NFC strings, lone surrogates, and integers outside the
interoperable safe range. Measurements use canonical decimal strings. The
supported RFC 8785/JCS subset orders object keys by UTF-16 code units and emits
compact UTF-8 JSON with no trailing line feed.

The accepted revision record directly binds `change_set_sha256`. A separate
proposal-attempt chain binds accepted, rejected, and conflict receipts, so
non-committing attempts remain auditable. Both local chains and readback detect
internal inconsistency and many accidental or partial corruptions, including
changed archived cards. They are not tamper-proof against an actor who can
rewrite the whole bundle and recompute its hashes. Strong tamper evidence
requires a trusted external anchor, such as a host-controlled immutable receipt
store, signature, or independently retained head hash.

The immutable card result contains only the external-outcome snapshot known at
closure. Later impact assertions belong in append-only `outcome_log`, which
targets the closed card. Its latest event must use current evidence:
`observed`/`verified` require supported evidence, `attribution_limited` permits
supported or partial evidence with an attribution note, and `withdrawn`
requires contradiction. Missing or stale evidence cannot support the timeline.

Read
[`references/hypothesis-state-and-persistence.md`](references/hypothesis-state-and-persistence.md)
for the state machine, standalone boundary, and Robin adapter contract.
The Russian practical walkthrough is
[`docs/onboarding-ru.md`](docs/onboarding-ru.md).

## Embedded use in Robin

Robin should remain the root agent.

1. Robin identifies the product-decision task and gathers only the required
   source observations.
2. For continuation, Robin loads the bounded workspace revision, relevant
   Hypothesis Card revisions, outcome timeline, and last accepted persistence
   receipt.
3. Robin invokes `$product-decision-paf` with bounded task and state context.
4. The skill returns a structured review: goal, sources, facts, hypotheses,
   interpretations, active blocked claims derived from `claim_log`, evidence
   status, enforcement boundary, and one next step, plus an optional atomic
   persistence proposal.
5. Robin applies its own identity, memory, permissions, approvals, governance,
   and delivery rules; only Robin's adapter may accept the proposal and issue a
   receipt.

Robin treats the card's external-outcome fields as the closure snapshot. It
appends later assertions to `outcome_log`; it does not reopen the terminal card.

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
assets, state schemas, publication hazards, all 50 required eval IDs, their
mapping to the 12 migration invariants and eleven longitudinal invariants, and
required documentation. Unit tests cover validator failure controls plus the
reference adapter's persistence, conflict, owner-gate, terminal-immutability,
and path-boundary behavior. Review the exact output before making a release
claim.

The eval suite covers:

- positive and negative activation;
- PAF and product-passport reviews;
- forbidden strong claims;
- insufficient-evidence responses;
- Robin embedded-mode boundaries;
- privacy and publication boundaries.

Eval cases are behavioral test inputs and expected outcomes. Their presence is
not evidence that a particular model passed them. The isolated longitudinal
run found six failures at baseline (21/27 semantic turns). A first remediation
review addressed those six rules, but release audit found that several returned
objects were incomplete sketches rather than schema-valid transactions. The
former effective `27/27` claim was therefore withdrawn, not re-labelled as a
pass. Deterministic tests now separate and validate a non-committable proposal
intent from a complete change set, including negative controls. The complete
50-case host harness, a full fresh-context transaction-emission rerun, immutable
runtime receipts, and production host enforcement have not been run or proven.
Claims about business value still require a real external outcome.

See:

- [`docs/migration-map.md`](docs/migration-map.md) for source classification;
- [`docs/equivalence-coverage.md`](docs/equivalence-coverage.md) for
  quality-critical behavior coverage;
- [`docs/longitudinal-forward-eval-report.md`](docs/longitudinal-forward-eval-report.md)
  for the isolated multi-invocation behavior run;
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

- The complete 50-case host harness and immutable model-behavior receipt remain
  unexecuted.
- Source access, write authorization, retention, backups, and external outcome
  receipts remain host-required.
- The file adapter provides explicit local persistence and resume artifacts; it
  does not provide autonomous retrieval, scheduling, experiments, or automatic
  crash recovery.
- Robin's persistence adapter is specified but not implemented or runtime-tested
  by this standalone repository.
- The validator can detect selected structural and publication hazards, but it
  is not a complete legal, privacy, or secret-history audit.
- Cross-platform readiness requires successful validation outside the current
  Windows development host.
- External product impact requires follow-up evidence after a recommendation is
  acted on.
