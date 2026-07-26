# Longitudinal fresh-context eval report

Date: 2026-07-26

## Current release verdict

**PARTIAL — no `27/27` behavior claim.**

The original isolated run established a semantic baseline of 21 passing turns
out of 27. A later remediation review judged six replacement answers
semantically adequate, but release audit found that several artifacts called
“change sets” were incomplete sketches and could not satisfy
`assets/hypothesis-change-set.schema.json`. The previously reported effective
`27/27` result is therefore withdrawn.

This correction matters: an answer can describe the right persistence boundary
while still failing to emit the complete portable transaction required by the
skill contract.

| Evidence | Result | What it proves |
|---|---:|---|
| Original fresh-context semantic baseline | 21/27 turns; 5/11 scenarios fully passing | Bounded instruction-following sample |
| Six remediation answers, semantic-only review | 6/6 described the intended rule | Rule recognition only; not transaction conformance |
| Former combined effective result | **WITHDRAWN** | Must not be cited as `27/27` |
| Proposal-intent deterministic positive | 1 valid fixture accepted by `validate-intent` | The incomplete-input artifact has an executable contract |
| Proposal-intent deterministic negative controls | 7/7 invalid variants rejected | Intent semantics fail closed |
| Focused model-emitted no-store intent | Current rerun PASS; predecessor rejected | One bounded intent-emission route conforms after exact nested extraction |
| Full model-emitted change-set conformance run | **NOT ESTABLISHED** | No release claim that a model emitted every complete transaction |
| Complete 50-case host behavior harness | **NOT RUN** | Eval definitions exist; full runtime behavior remains host-required |

## Scope and method

The baseline inspected:

- current `SKILL.md`;
- all 11 multi-turn scenarios under `evals/lifecycle/`;
- 27 isolated raw result objects under the Git-ignored `evals/results/`;
- each turn's `expected`, `forbidden`, and scenario invariants.

Each baseline turn used a separate fresh-context generator. The independent
grader inspected rubric and output together; generators were not intentionally
given the rubric. Raw result objects contain response actions, persistence
status, and next step, not a complete invocation trace or signed runtime
manifest. The exact model build was not exposed.

Six failed turns were later regenerated. Five used new rubric-withheld child
contexts; one resume turn reused its same rubric-withheld generator after a
stable-ID correction. Those replacements were originally graded semantically.
The later release audit applied the stronger artifact contract and invalidated
the aggregate pass claim.

## Preserved baseline result

| Scenario | Passed / total | Baseline result | Main finding |
|---|---:|---|---|
| `append-only-evidence-correction` | 2/2 | PASS | Correction was append-only and preserved prior evidence |
| `current-nexus-authority` | 2/2 | PASS | Current evidence and Nexus lineage were required together |
| `execution-proof-and-frozen-design` | 2/3 | FAIL | Start transition lacked separate subject-bound state approval |
| `no-store-mode-pair` | 1/2 | FAIL | Standalone answer deferred the portable artifact |
| `owner-approval-binding` | 2/3 | FAIL | Pending checkpoint lacked a concrete bound proposal |
| `owner-transition-pending-resolution` | 1/2 | FAIL | Old-owner request lacked originating change-set binding |
| `post-release-outcome-continuation` | 2/3 | FAIL | Closure omitted same-revision evidence-bound Nexus learning |
| `proposal-replay-and-atomicity` | 3/3 | PASS | Replay and post-write ambiguity were handled honestly |
| `receipt-honesty-matrix` | 3/3 | PASS | Failed and mismatched receipts did not become persistence |
| `resume-after-accepted-receipt` | 1/2 | FAIL | Initialization was deferred instead of represented now |
| `version-conflict-reload` | 2/2 | PASS | Stale revision caused reload rather than overwrite |

Baseline total:

```text
turns: 21/27
fully_passing_scenarios: 5/11
baseline_failures: 6
```

## Why the former remediation pass was invalid

The release audit compared raw replacement objects with the actual portable
schemas and found a category error:

- the no-store object omitted required transaction fields such as
  `schema_version`, request/workspace bindings, full `candidate_state`, and
  exact `change_manifest`;
- the owner checkpoint contained a compact checkpoint sketch rather than the
  complete candidate workspace;
- the initialization response named revision semantics but did not serialize a
  complete create transaction;
- the closure response named evidence and Nexus IDs without serializing the
  evidence-bound Nexus entry required by the candidate state.

Those answers could demonstrate semantic intent, but not the artifact the
rubric and `SKILL.md` claimed they returned. Counting them as portable
transaction passes lowered the grading threshold after the fact.

## Architectural remediation

The package now defines two distinct artifacts:

1. `hypothesis-proposal-intent/v1`
   - used only while a schema-required product or state binding is unavailable;
   - records known bindings and every unresolved binding;
   - carries the materialization requirements;
   - always has `commit_eligible = false` and `not_persisted`;
   - is rejected by the `commit` command.
2. `hypothesis-change-set/v1`
   - contains the complete candidate workspace and exact manifest;
   - is the only artifact the adapter can validate and commit;
   - remains `proposed` or `not_persisted` until an accepted receipt and exact
     readback exist.

The distinction prevents two opposite failures: inventing missing product
context to fill a schema, and calling an incomplete sketch an atomic
transaction.

## Deterministic conformance evidence

`evals/conformance/standalone-no-store-proposal-intent.json` is the public-safe
positive fixture. The adapter command:

```text
python scripts/hypothesis_state.py validate-intent --intent <proposal-intent.json>
```

checks JSON Schema, bounded sensitive-data patterns, and semantic invariants.
Unit tests also prove that `commit` rejects the same intent.

The negative controls reject:

1. invalid create revision semantics;
2. a known binding also listed as unresolved;
3. a null binding omitted from the unresolved list;
4. an empty lifecycle context omitted from the unresolved list;
5. a missing target lifecycle state;
6. an intent whose only gaps are write authority or adapter availability even
   though a complete candidate could be formed;
7. a materialization contract that omits resolved bindings or a schema-valid
   change set.

The broader adapter unit suite independently validates complete change sets,
state transitions, approvals, append-only logs, receipts, concurrency,
idempotency, integrity chains, and recovery. That proves the deterministic
contract implementation, not that an arbitrary model will always serialize the
right transaction.

### Focused intent-emission check

A rubric-withheld generator was given only the no-store input and current skill
contract. Its first output was rejected because
`response_actions[0].portable_artifact.requested_change.target_state` was
`null`. That failure exposed a schema gap; the contract was tightened so every
intent has a concrete target lifecycle state and an empty lifecycle context is
listed as unresolved.

The same generator then reread the corrected contract and produced a new
ignored output. Exact extraction at
`response_actions[0].portable_artifact` passed proposal-intent schema,
semantic, and sensitive-data validation. This is evidence for one bounded
no-store intent path only. It is not a complete change-set test, a fresh new
child context, an immutable runtime receipt, or evidence for the other 26
turns.

## Leakage and publication controls

- Raw baseline and remediation outputs remain Git-ignored and are not part of
  the public package.
- No direct `expected`, `forbidden`, or scenario-invariant fields were found in
  the raw response objects.
- Raw files do not contain a signed prompt envelope, immutable model build, or
  reconstructable runner receipt; fresh-context and rubric-withholding claims
  therefore remain process evidence, not cryptographic proof.
- The public report preserves the failed baseline and the withdrawn aggregate
  claim instead of rewriting history.

## Release interpretation

The release may claim:

- 50 static eval definitions and 11 lifecycle scenarios are structurally
  validated;
- the original forward semantic sample passed 21/27 turns;
- proposal intent and complete change set are now separate executable
  contracts;
- deterministic intent and adapter tests pass;
- one focused model-emitted no-store intent passed machine conformance after
  its invalid predecessor was rejected.

The release must not claim:

- effective `27/27` model behavior;
- that every lifecycle response was schema-valid or commit-eligible;
- production Robin persistence readiness;
- authenticated owner decisions;
- experiment execution or verified external product impact.

A future behavior promotion requires an immutable skill snapshot, captured
invocation envelopes, rubric-withheld generators, and machine validation of
every emitted intent or change set before semantic grading.
