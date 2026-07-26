# Hypothesis state and persistence contract

## Contents

- [Purpose](#purpose)
- [Nexus, state, and storage](#nexus-state-and-storage)
- [Logical state model](#logical-state-model)
- [Decision scopes and owner tenures](#decision-scopes-and-owner-tenures)
- [Hypothesis lifecycle](#hypothesis-lifecycle)
- [PAF dependencies and co-tests](#paf-dependencies-and-co-tests)
- [Evidence, Nexus, and claims](#evidence-nexus-and-claims)
- [Results and external outcomes](#results-and-external-outcomes)
- [Post-release outcome log](#post-release-outcome-log)
- [Owner approvals](#owner-approvals)
- [Change-set protocol](#change-set-protocol)
- [Persistence receipts](#persistence-receipts)
- [Revision integrity](#revision-integrity)
- [Portable skill and host boundaries](#portable-skill-and-host-boundaries)
- [Standalone file adapter](#standalone-file-adapter)
- [Robin adapter](#robin-adapter)
- [Canonical JSON](#canonical-json)
- [Privacy and operational limits](#privacy-and-operational-limits)

## Purpose

This contract makes PAF hypothesis work resumable without turning the portable
skill into a memory system or root agent. It separates:

1. PAF reasoning and state semantics defined by the skill;
2. product state stored and retrieved by a host;
3. writes, permissions, and external effects enforced by an adapter or runtime;
4. receipts that say what the host actually accepted.

The portable JSON contract is defined by:

- [`hypothesis-workspace-state.schema.json`](../assets/hypothesis-workspace-state.schema.json);
- [`hypothesis-proposal-intent.schema.json`](../assets/hypothesis-proposal-intent.schema.json);
- [`hypothesis-change-set.schema.json`](../assets/hypothesis-change-set.schema.json);
- [`persistence-receipt.schema.json`](../assets/persistence-receipt.schema.json);
- [`hypothesis-state-bundle.schema.json`](../assets/hypothesis-state-bundle.schema.json)
  for the reference standalone host.

Markdown cards are review views rendered from those records. They are not a
second source of truth.

## Nexus, state, and storage

**Nexus is the product-domain model of maintained knowledge**, not a database,
folder, memory service, or Robin-specific feature. In this contract its atomic
content units are `nexus_entries`: facts, interpretations, decisions, and
unknowns with evidence status, safe evidence references, freshness, and
supersession links.

The portable state protocol defines how Nexus content, hypothesis records,
evidence, claims, goals, owners, revisions, and receipts fit together. It still
does not store anything by itself.

The host owns the physical persistence mechanism:

```text
portable Nexus/Hypothesis state
  -> proposal intent while required bindings are unresolved
  -> complete candidate change set
  -> authorized host adapter
  -> accepted receipt and exact readback
  -> bounded state rehydrated into the next invocation
```

Robin is one possible host. The explicit local file adapter is another. A
transactional database can be a third if it preserves the same semantics.
Without a host-loaded snapshot and a matching accepted receipt, a new
invocation has no truthful long-term continuity.

## Logical state model

A **workspace** is the versioned product-level state across sequential product
decision scopes. It contains:

- stable workspace and product refs;
- the active goal, decision scope, and owner tenure;
- the current evidence base (`null_base` or `data_base`);
- append-only `nexus_entries`, `evidence_log`, `claim_log`, and `outcome_log`;
- current versioned hypothesis records and one optional focus hypothesis;
- the last persistence receipt ref and revision-chain head.

A **hypothesis record** is one testable PAF hypothesis. It has a stable
`hypothesis_id`, immutable decision-scope binding and origin, its own revision,
lifecycle state, PAF class, lifecycle context, dependencies, test contract,
owner approvals, evidence references, result, relations, and one next step.

A **change set** is an atomic proposal. It binds the expected workspace
revision, complete candidate state, exact change manifest, pending owner
requirements, and enforcement boundary. It is not proof of a write.

A **proposal intent** is a portable but deliberately non-committable artifact
for the earlier phase where one or more bindings required by the change-set
schema are unknown. It records known bindings, every unresolved binding, the
requested change, and the materialization contract. It always has
`commit_eligible = false` and `persistence_status = not_persisted`; the state
adapter never accepts it as a change set.

A **persistence receipt** records whether the host accepted, rejected, failed,
or found a conflict in that exact proposal.

Stable IDs are never reused. Workspace revision starts at zero and increases by
exactly one per accepted replacement. Hypothesis revision starts at zero and
increases by one whenever that record changes. A replacement with no
substantive state change is rejected.

`as_of` is snapshot time, not proof of source freshness. `base` is derived from
currently usable evidence: a workspace can move from `data_base` back to
`null_base` after the prior evidence becomes stale, missing, or superseded.

## Decision scopes and owner tenures

One product workspace can carry multiple goals over time without fragmenting
its Nexus.

`decision_scope_log` is append-only. Its latest item supplies both
`active_decision_scope_id` and the current `goal`. Each new scope:

- has a new stable ID and increasing sequence;
- points to its immediate predecessor;
- binds its opening workspace revision and a safe transition receipt;
- explains why the bounded decision changed.

Every hypothesis is immutably bound to one `decision_scope_id`. A non-terminal
hypothesis must belong to the active scope, and the focus hypothesis must be
both active and non-terminal. Before changing scopes, close, cancel, or
supersede prior-scope active work through the applicable approval gate. Earlier
Nexus and evidence remain in the same product workspace.

`owner_tenure_log` is the corresponding append-only history of decision
ownership. Its latest item supplies `active_owner_tenure_id` and
`decision_owner_ref`. A new tenure links to its predecessor, effective
workspace revision, safe transition receipt, and reason.

Owner approvals are tenure-bound. Historical approvals remain auditable but do
not silently authorize work under the new owner. Active work that requires an
owner rule must receive a current approval bound to the active tenure.

## Hypothesis lifecycle

Lifecycle state and PAF verdict are separate:

| State | Meaning |
|---|---|
| `framing` | Goal, claim, segment, dependencies, or validation design is incomplete |
| `blocked_upstream` | A required upstream hypothesis or evidence link is unresolved |
| `awaiting_owner_rule` | A criterion, sample, time window, or rule awaits owner approval |
| `ready_to_run` | Upstream and owner gates are satisfied |
| `running` | The host supplied evidence that execution actually started |
| `ready_for_review` | Structured results exist and await validity and verdict review |
| `closed` | The owner accepted a `confirmed`, `disconfirmed`, or `unresolved` verdict |
| `cancelled` | Work stopped without a PAF verdict |
| `superseded` | Another linked record replaced this formulation |

Allowed transitions:

```text
framing
  -> blocked_upstream | awaiting_owner_rule | ready_to_run
  -> cancelled | superseded

blocked_upstream
  -> framing | awaiting_owner_rule
  -> cancelled | superseded

awaiting_owner_rule
  -> framing | ready_to_run
  -> cancelled | superseded

ready_to_run
  -> running | cancelled | superseded

running
  -> ready_for_review | cancelled

ready_for_review
  -> running | closed
```

`closed`, `cancelled`, and `superseded` are terminal and immutable. A correction
or new formulation creates a linked record. Relation and dependency graphs must
not contain self-links or cycles. A new record may replace a historical target
that is either `closed` or `superseded`; it never rewrites that target.

All non-terminal records use `verdict = pending`. Closed records use
`confirmed`, `disconfirmed`, or `unresolved`. Cancelled and superseded records
use `not_run`.

The complete approved test contract freezes at `ready_to_run`. A transition to
`running` requires both a host-supplied `execution_ref` and an approved
`state_transition` subject bound to the candidate hypothesis revision and that
exact execution ref. If the execution ref exists before the approval, the skill
returns the complete `running` candidate and its concrete required-approval
request as `proposed`; the host may accept it only after resolving that request.
The skill must not claim that the candidate already entered `running`. A
persistence receipt proves neither execution nor owner approval.

## PAF dependencies and co-tests

The four PAF classes are:

- `customer_need`;
- `value_proposition`;
- `solution`;
- `business_model`.

Acquisition, activation, onboarding, go-to-market, adoption, and post-release
impact are lifecycle contexts, not new PAF classes.

The default upstream chain is:

```text
customer_need -> value_proposition -> solution
```

Each dependency declares `mode = prerequisite` or `mode = co_test`.
`prerequisite` requires supported upstream knowledge and has no co-test plan.
A co-test is the narrow PAF exception for:

- `value_proposition` with `solution`;
- `solution` with `business_model`.

A co-test requires a `co_test_plan_ref`, separate hypothesis IDs, separately
approved test contracts, and separate metric results, interpretations, and
verdicts. The peers must be jointly runnable. When running or ready for review,
they must cite the same host execution evidence. One experiment may therefore
produce evidence for two claims without collapsing them into one claim. After
the shared run, one peer may close while the other remains
`ready_for_review`, provided both retain the same `execution_ref`.

## Evidence, Nexus, and claims

`evidence_log`, `nexus_entries`, `claim_log`, and `outcome_log` are append-only:

- an existing event is never edited, removed, or reordered;
- a correction is a new event with a new stable ID and an earlier supersession
  target;
- every appended event has a sequence strictly greater than the preserved log
  prefix;
- the change manifest names every appended ID;
- raw source payloads remain outside the portable state.

Evidence records preserve source ref, observation period, method, segment,
filters, exclusions, numerator, denominator, summary, and status. Currently
usable evidence determines `base`.

A Nexus entry has `kind`, `statement`, evidence IDs, status, validity time, and
`supersedes_entry_ids`. A `supported` Nexus entry must be backed by supported
evidence. An `unknown` entry cannot be marked supported.

A Nexus entry with `kind = decision` additionally requires
`decision_authority`. It binds:

- the exact canonical decision subject hash;
- owner ref and owner tenure;
- decision scope and decision time;
- safe external receipt ref;
- `reversible` or `irreversible`.

New decision entries must use the active scope, owner, and tenure. Their status
must be supported. Other Nexus kinds must not carry decision authority. The
adapter validates the exact subject hash; the host authenticates the owner and
receipt.

New learning from a hypothesis is not stored in a separate generic journal.
The result lists `new_nexus_entry_ids`, and those IDs must identify Nexus
entries appended in the same accepted workspace revision. This binds the
interpretation to the product model without copying it into the card.

Claims use append-only events in `claim_log`. The first event for a logical
`claim_id` is `blocked` and declares the evidence needed. A later event must
supersede the latest event for that claim and may resolve it as:

- `supported`, with supported resolution evidence; or
- `withdrawn`, with contradictory resolution evidence.

The active blocked-claim set is derived from the latest event for each
`claim_id`; it is not a separately editable state field.

## Results and external outcomes

Before review, the result envelope stays empty with
`validity_status = not_reviewed`.

At `ready_for_review` and `closed`, every primary validation metric has one
`metric_results` record containing:

- the metric ID and in-run evidence IDs;
- observation period and safe observed summary;
- actual numerator and denominator as canonical decimal strings when present;
- actual sample size;
- `criterion_evaluation = met | not_met | indeterminate`;
- result validity.

`confirmed` requires every primary criterion to be met, supported evidence, and
adequate overall and primary-metric validity. `disconfirmed` requires at least
one primary criterion not met, no indeterminate primary result, supported
evidence, and adequate validity. Invalid evidence can close only as
`unresolved`.

`new_nexus_entry_ids` records what the review added to the Nexus. A terminal
verdict proposal must append at least one evidence-bound Nexus entry in the
same candidate revision and list that entry in `new_nexus_entry_ids`. If the
review cannot support retained learning, the card must not close. A verdict
without retained, evidence-bound learning does not provide longitudinal value.

External product impact is a later, separate assertion:

- `observed`, `attribution_limited`, and `verified` require outcome evidence;
- `verified` additionally requires supported outcome evidence and a host
  receipt;
- no other status may carry an external-outcome receipt.

A closed or confirmed hypothesis is not itself proof of business impact.

The result's external-outcome fields are a closure-time snapshot only. They
cannot be edited after the card becomes terminal. In that snapshot,
`observed`/`attribution_limited` may cite only supported or partial evidence,
and `verified` requires supported evidence plus a host receipt. Missing, stale,
or contradictory evidence cannot support an embedded positive outcome claim.

## Post-release outcome log

`outcome_log` is the authoritative append-only timeline for assertions made
after a card closes. Every outcome event:

- targets a `closed` hypothesis and its original decision scope;
- has a new event ID, sequence, evidence IDs, safe summary, and supersession
  links;
- supersedes only the latest earlier outcome for that hypothesis;
- preserves earlier outcome assertions instead of editing the terminal card.

Status gates are:

- `observed` requires supported evidence;
- `attribution_limited` allows supported or partial evidence and requires an
  attribution note;
- `verified` requires supported evidence and a host receipt;
- `withdrawn` requires contradictory evidence.

The latest event must rely on current, unsuperseded usable evidence. Missing,
stale, or superseded evidence cannot remain authoritative. The change manifest
lists appended IDs in `appended_outcome_event_ids`, and the revision delta
commits the complete appended events.

## Owner approvals

Approval scopes are:

- `decision_rule`;
- `proposed_assumption`;
- `state_transition`;
- `terminal_verdict`.

Every approval binds the workspace, hypothesis, active owner tenure, scope,
subject revision, canonical SHA-256, and safe external receipt ref.
Decision-rule approval binds the complete frozen test contract. Proposed
assumptions bind the proposed metric, sample, and time-window values.
State-transition and terminal-verdict approvals bind the current revision. For
`ready_to_run -> running`, the canonical state-transition subject also includes
the supplied execution ref; the execution ref itself is not approval.

Changing a bound subject invalidates reuse. A later rejection for the same
subject revokes an earlier approval. The adapter checks structural binding and
owner-ref equality; only the host can authenticate the owner and external
receipt.

`pending_owner_approvals` is a resumable request, not authority. It binds the
current owner tenure, exact subject revision and hash, and the exact
`source_change_set_id` that created it. It must correspond byte-for-byte to
`required_owner_approvals` in that originating change set. The skill returns
the concrete checkpoint proposal in the same response; it does not merely
describe fields for the host to construct later. The request can be persisted
only at `awaiting_owner_rule`. Runnable and terminal states cannot carry
unresolved requests.

A pending request does not deadlock the workspace forever. When it is removed,
the same change must append either a matching owner approval or a
`pending_owner_resolutions` event:

- `withdrawn` — the active owner explicitly withdraws the request;
- `invalidated_by_tenure_transition` — the candidate revision that appends the
  authenticated owner transition also appends the resolution that makes the
  old-tenure request inapplicable.

The resolution binds the original request tenure, subject revision and hash,
the active resolving authority, reason, and safe receipt. The original request
remains in immutable hypothesis history; resolution history is append-only.

## Change-set protocol

1. The host loads and validates the latest workspace and accepted receipt.
2. The skill reasons over that exact bounded snapshot.
3. If every required binding is known, the skill returns a complete candidate
   state and atomic change set with expected revision and exact manifest.
   Otherwise it returns a schema-valid proposal intent, never a partial object
   labelled as a change set.
4. The host resolves any required owner approval.
5. The adapter validates schema, semantics, transitions, append-only prefixes,
   approval bindings, canonical hashes, and optimistic concurrency.
6. The adapter commits state, revision record, immutable card revisions,
   receipt, handled-proposal binding, and both integrity-chain heads as one
   bundle replacement.
7. The adapter rereads and verifies the exact written bundle.
8. The next invocation receives the new snapshot and accepted receipt.

For `workspace_operation = create`, expected revision is `null` and the
candidate starts at revision zero. For `replace`, candidate revision is
`expected_workspace_revision + 1`.

When the host explicitly reports that no workspace exists and the user asks to
start a named hypothesis, the workspace and hypothesis revision semantics are
known: create uses expected workspace revision `null`, candidate workspace
revision zero, and candidate hypothesis revision zero. That is not enough by
itself to fabricate product, scope, owner, statement, class, segment, or
validation bindings.

If every change-set field is available, return the complete create transaction.
With an adapter handoff its status is `proposed`; without a usable adapter,
state root, or write authority the same complete transaction is
`not_persisted`. A complete change set remains useful without storage because
another authorized host can validate the exact bytes later.

If any required binding is unavailable, return a
`hypothesis-proposal-intent/v1` artifact instead. It preserves the known
operation and revision semantics, enumerates unresolved bindings, and names the
full candidate-state, exact-manifest, adapter, write-authority, receipt, and
readback requirements. It is never `proposed`, commit-eligible, accepted by the
adapter, or evidence of a checkpoint. After bindings are resolved, materialize
a new complete change set with its own stable ID and hash. Do not instruct the
host to reconstruct an omitted transaction from prose, and do not mislabel an
intent as one.

If observed and expected revisions differ, the adapter returns `conflict`.
Reload and reason again; never merge or overwrite blindly.

Exact replay of the same proposal returns its prior receipt. Reusing a
`change_set_id` for different content fails closed.

Supported upstream dependencies are revalidated against current authority, not
only historical card status. A supported dependency must cite current,
unsuperseded supported evidence. When it names an upstream hypothesis, that
hypothesis must be closed/confirmed with adequate validity and its
`new_nexus_entry_ids` must lead to a current supported Nexus descendant backed
by the dependency evidence. A historical confirmed verdict whose evidence or
Nexus lineage was superseded is no longer sufficient.

## Persistence receipts

Only `status = accepted` proves that this adapter accepted the exact change set,
performed its atomic-replace protocol, and successfully read back the exact
bundle in that run. The receipt binds:

- change-set ID and SHA-256;
- expected, observed, and new revisions;
- state SHA-256, adapter ref, and storage ref;
- approval refs and validation results;
- persistence timestamp;
- `durability_scope =
  atomic_replace_with_readback_power_loss_host_dependent`.

That durability scope is intentional. An accepted standalone receipt is strong
local readback evidence, but it does not promise storage-controller,
filesystem, backup, or power-loss durability beyond what the host provides.

`rejected`, `conflict`, and `failed` prove only that an attempt was handled.
Without an accepted receipt, say `proposed` or `not_persisted`, never `saved`,
`remembered`, or `updated`.

Exit code `6` with `OUTCOME UNKNOWN` is different from `failed`: replacement
may have happened, but post-replace readback or durability verification could
not establish the outcome. Do not submit changed content under the same or a
new ID. Run `verify` and `load`, recover only an unchanged stale lock if
necessary, then replay the exact unchanged change-set file. The adapter's
idempotency binding returns the stored receipt if that proposal was already
handled, or commits it once if it was not.

## Revision integrity

The standalone bundle contains:

- `proposal_history_head_sha256`;
- authoritative `current_state`;
- contiguous `revision_history`;
- immutable changed-card revisions in `hypothesis_history`;
- immutable receipts;
- handled proposal ID/hash/receipt bindings.

Each revision record commits:

- `previous_revision_sha256` and `previous_state_sha256`;
- `revision_delta_sha256`;
- `revision_sha256`;
- current state hash, manifest, summary, receipt, and acceptance time.

The delta hash covers changed hypothesis records and the appended decision
scopes, owner tenures, Nexus entries, evidence entries, and claim events.
It also covers appended outcome events.
`current_state.revision_chain_head_sha256` must equal the latest revision
commitment. This detects archived-card and ledger inconsistency, not only
current-state edits.

Every accepted revision directly commits the exact `change_set_sha256`. Its
accepted receipt, handled-proposal record, and revision record must agree on
that hash.

A separate proposal-attempt commitment chain covers every handled
`accepted`, `rejected`, or `conflict` receipt. Each handled proposal commits its
sequence, previous proposal hash, change-set ID/hash, receipt ID, and receipt
hash. The bundle-level `proposal_history_head_sha256` must equal the final
proposal commitment. Rejected and conflicting attempts therefore remain
auditable even though they create no workspace revision.

The chain is not tamper-proof against an actor who can rewrite the whole bundle
and recompute every hash. Strong tamper evidence requires a trusted external
anchor such as an immutable host receipt log, signature, or independently
retained chain head.

## Portable skill and host boundaries

The skill owns:

- PAF classification, routing, and reasoning rules;
- portable state schemas and semantic invariants;
- candidate hypothesis revisions and change sets;
- evidence, Nexus, claim, result, and approval vocabulary;
- one decision-shaped next step.

The skill does not own:

- product-specific durable state or retrieval;
- owner authentication or write permission;
- locks, backup, retention, or recovery authority;
- connectors, experiment execution, or external effects;
- host receipts or external-outcome proof.

The host owns those mechanisms and may reject a structurally valid proposal
when source freshness, privacy, permission, or product policy fails. Owning a
portable state protocol is not the same as owning memory.

## Standalone file adapter

The included file adapter is an optional explicit host. It is not hidden skill
memory.

Its operating boundary is:

- the user supplies an absolute state root for every command;
- the root must be outside the skill package;
- it must be a single-host local filesystem root; Windows UNC roots are
  rejected;
- state targets that are symlinks or reparse points are rejected;
- there is no default path, network access, scheduler, background loop, delete
  operation, connector, or silent write;
- the bundle is limited to 32 MiB, 10,000 revisions, and JSON nesting depth
  128; change-set input is separately bounded;
- one process commits at a time.

Physical layout:

```text
<absolute-user-selected-root>/
  .hypothesis-state.lock.gate  # reusable one-byte OS advisory-lock target
  hypothesis-state-bundle.json
  hypothesis-state.lock  # only while commit is active
```

Commands:

```text
python scripts/hypothesis_state.py validate-intent --intent <proposal-intent.json>
python scripts/hypothesis_state.py load --root <absolute-state-root>
python scripts/hypothesis_state.py commit --root <absolute-state-root> --change-set <change-set.json>
python scripts/hypothesis_state.py verify --root <absolute-state-root>
python scripts/hypothesis_state.py inspect-lock --root <absolute-state-root>
python scripts/hypothesis_state.py recover-lock --root <absolute-state-root> --expected-pid <dead-pid> --expected-token <lock-token>
```

Commit stages a lock-owned file, flushes it, atomically replaces the bundle, and
performs exact readback. On supported Unix-like hosts it also requests a
directory flush. Power-loss guarantees remain host-dependent.

Lock recovery is deliberately manual. `inspect-lock` returns both PID status
and an opaque lock token. `recover-lock` succeeds only when the exact PID and
exact token still match, the owner is proven dead, and the lock has not changed.
It removes only files named by that lock record. Lock publication and recovery
share a short-lived operating-system advisory gate, so a new commit cannot
publish a replacement lock between the recovery recheck and unlink. The
one-byte gate file is reusable, contains no state, and an operating-system
process exit releases the advisory lock.

Cleanup happens after the command result is known. If removing the owner record
or the command's own main lock fails at that point, stderr receives a safe JSON
warning with `warning = lock_cleanup_required`, the opaque `lock_id`, cleanup
stage, and recovery next step. The already-emitted receipt and the command exit
code remain authoritative; cleanup failure must not turn a known accepted,
rejected, or conflict result into `failed`. Inspect the lock and recover it only
after the exact owner PID is proven dead. This is not `OUTCOME UNKNOWN`: in
that case the write/readback outcome, rather than only lock cleanup, is
unresolved.

The adapter is designed for one machine and one local filesystem. Use a
transactional host with its own concurrency, durability, backup, and integrity
controls for shared or production state.

## Robin adapter

Robin remains the root agent and host. It supplies:

- the authorized product ref and bounded state revision;
- relevant Nexus, hypothesis, evidence, claim, scope, and tenure records;
- successful safe source reads;
- privacy, permission, budget, and deadline boundaries;
- current execution and persistence receipts.

The skill returns reasoning plus either a proposal intent or a complete change
set. Robin resolves missing bindings and owner approval, commits only the
complete transaction through its own adapter, and supplies the resulting
receipt to the next invocation.

For later impact tracking, Robin appends an `outcome_log` event instead of
editing the closed card. The external-outcome fields embedded in that card
remain only the immutable closure snapshot.

Robin must not let the skill broaden permissions, infer source success, mark a
planned experiment `running`, close a hypothesis without review and owner
acceptance, or treat model output as a persistence receipt.

The Robin adapter is specified by this package but not implemented by the
standalone file host.

## Canonical JSON

Hashes and approval subjects use the supported RFC 8785/JCS subset with:

- strict JSON only: no duplicate keys, `NaN`, or infinities;
- Unicode NFC for every key and string;
- no unpaired/lone Unicode surrogates;
- no JSON floating-point values;
- decimal measurements represented by schema-constrained canonical decimal
  strings;
- integers within the interoperable safe range
  `-9007199254740991..9007199254740991`;
- object keys ordered by UTF-16 code units, compact separators, UTF-8 output,
  and no trailing line feed.

The bundle file may be pretty-printed for review; hashes are always computed
from the canonical representation. The pretty file's final newline is not part
of any canonical hash.

## Privacy and operational limits

Portable state contains safe product-decision summaries and safe refs only. It
must not contain credentials, tokens, cookies, session strings, raw
transcripts, private messages, raw connector payloads, unrestricted personal
memory, hidden reasoning, or unnecessary direct identifiers.

The reference adapter performs a bounded sensitive-pattern scan. A passing scan
is not a complete privacy review. A production host still owns structured
privacy controls, access policy, retention, recovery, backups, external
integrity anchors, and real-world outcome verification.
