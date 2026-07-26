# Bayram-informed skill architecture

## Status and scope

This is an implementation synthesis of the Bayram-informed architecture brief
supplied for this migration. It is not a quotation, an attribution of this exact
matrix to Bayram Annakov, or a claim of endorsement.

Use the matrix to prevent a portable skill from masquerading as a root agent or
runtime. The package owns decision procedures and review artifacts; the host
owns identity, private state, execution authority, persistence, and effects.

## Trace from request to outcome

For material work, keep this chain inspectable:

`human formulation → system function → artifact → runtime/enforcement → evidence → external outcome`

An artifact is not an outcome. A recommendation is not an effect. A successful
tool request is not a receipt unless the host verifies the resulting state.

## Ownership and evidence matrix

| Brick | Human capability | Skill-owned contract | Host-owned capability | Evidence or honest gap |
|---|---|---|---|---|
| Identity | Knows who it is | Declares a narrow product-decision capability and output contract | Root-agent identity, role, voice, governance | Activation evals; the output must not claim to be Robin or the root agent |
| User context | Knows the user | Accepts task-scoped goals, preferences, and constraints | User profile, consent, private personalization, retention policy | Input refs in the review; `host-required` when context was not supplied |
| Sources | Sees and hears | Routes required evidence before asking for more or making claims | Connectors, credentials, freshness checks, source authorization | Safe source refs, period, denominator, freshness, and explicit coverage gaps |
| Memory | Remembers | Defines Nexus as a domain/content model plus versioned Hypothesis state, non-committable proposal intents, complete candidate transactions, and receipt semantics | Retrieval, durable storage, private traces, write authority, and bounded rehydration | No package-owned private memory; a matching accepted adapter receipt and readback are required before claiming persistence |
| Model | Thinks | Provides a bounded procedure and evidence vocabulary | Model selection, inference runtime, reliability controls | Evals sample behavior; deterministic truth remains unsupported |
| Tools | Has hands | Names required read/check/write operations and approval boundaries | Tool availability, sandbox, budgets, approvals, external effects | Tool-result evidence plus effect receipt; otherwise recommendation only |
| Skills | Knows how to work | Owns `SKILL.md`, references, templates, eval cases, and local checks | Capability registry and invocation orchestration | Package validation and activation/task evals |
| Events | Shows initiative | Describes eligible triggers and stop conditions | Hooks, scheduler, goal loop, wakeups | No autonomous standalone start; event execution is `host-required` |
| Delegation | Coordinates others | May propose separable work and an expected return contract | Sub-agent creation, permissions, merge/conflict handling | Delegation log or host receipt; otherwise `not-supported-standalone` |
| Boundaries | Knows limits | States forbidden claims, modes, approvals, and stop/escalation rules | Permission enforcement, policy engine, cost and privacy controls | Negative evals plus host enforcement evidence where effects are possible |
| Recovery | Does not get lost | Defines stable IDs, revisions, checkpoints, conflict handling, and resumable artifacts | Durable checkpoint store, retries, locks, idempotency, and rehydration | Reference file adapter can checkpoint explicitly; automatic recovery remains `host-required` |
| Evals | Checks itself | Owns positive, negative, boundary, and realistic scenario cases | Model runner, reviewer independence, trace store, CI | Corpus/schema check is static; executed eval results need runner receipts |
| External outcome | Proves usefulness | Defines the expected change and verification criterion | Real-world action, attribution window, measurement and receipt | Verified external state or metric; without it, report `not verified` |

## Architectural consequences

- Standalone mode can produce an evidence-aware review, templates, and a next
  step. With explicit host write authority it may use the package's reference
  file adapter against a user-selected root. The adapter is a host mechanism,
  not package-owned memory. Its atomic bundle combines the authoritative
  `current_state`, compact hash-linked `revision_history`, immutable
  `hypothesis_history`, append-only Nexus/evidence/claim/outcome events,
  receipts, and a proposal-attempt commitment chain. It supplies optimistic
  concurrency, idempotent proposal handling, exact readback, and token-bound
  local recovery, but does not supply identity, connectors, authenticated
  decision-owner approvals, or autonomous runtime guarantees.
- Nexus is the portable product-domain model, not the store. Typed Nexus
  learning is bound through `new_nexus_entry_ids`; `decision_scope_log` and
  `owner_tenure_log` preserve changing goals and authority without fragmenting
  the product knowledge.
- Missing product, scope, owner, or state bindings are represented as a typed
  non-committable proposal intent. A partial sketch is never promoted by name
  into a transaction; only a complete schema-valid candidate change set can
  cross the host write boundary.
- A Nexus decision is not merely an interpretation labelled as decided. Its
  portable record binds the exact subject, active scope and owner tenure, safe
  receipt, and reversibility; the host remains responsible for authenticating
  that authority.
- Terminal-card results are immutable closure snapshots. The host appends later
  post-release assertions to `outcome_log` with current evidence.
- The reference file adapter is bounded to 32 MiB and 10,000 accepted
  workspace revisions. It fails closed at either boundary and requires
  migration to a transactional host; silent compaction would destroy the audit
  contract and is not supported.
- The file adapter is a single-host local-filesystem mechanism. Its accepted
  receipt proves atomic replace plus exact readback, while power-loss durability
  remains host-dependent. Exit code `6` means `OUTCOME UNKNOWN` and requires
  reconciliation before retry.
- Embedded mode returns a structured product-decision result to Robin; Robin
  remains owner of identity, memory, permissions, tools, and governance.
- `skill-instruction` is not deterministic enforcement. Use
  `script-checked`, `host-required`, or `not-supported-standalone` when that is
  the real boundary.
- Never infer success from a polished artifact, model confidence, tool-call
  intent, or process exit alone. Verify the external state named in advance.
- Owning a state contract is different from owning state. The skill defines
  what a valid longitudinal update means; a host decides where it lives, who may
  write it, and whether the write actually happened.
- Hash-linked revisions and receipts make internal inconsistency inspectable.
  A second proposal-attempt chain preserves accepted, rejected, and conflict
  receipts. Neither chain is tamper-proof without a trusted external anchor
  controlled by the host.
- Canonical hashing uses the supported RFC 8785/JCS subset: strict JSON, NFC
  strings, no lone surrogates or floats, safe-range integers, canonical decimal
  strings, UTF-16 key order, compact UTF-8 output, and no trailing line feed.
