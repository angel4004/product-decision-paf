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
| Memory | Remembers | Keeps only the current review state in the response/artifact | Retrieval, durable memory, private traces, write policy | No package-owned private memory; persistence is `host-required` |
| Model | Thinks | Provides a bounded procedure and evidence vocabulary | Model selection, inference runtime, reliability controls | Evals sample behavior; deterministic truth remains unsupported |
| Tools | Has hands | Names required read/check/write operations and approval boundaries | Tool availability, sandbox, budgets, approvals, external effects | Tool-result evidence plus effect receipt; otherwise recommendation only |
| Skills | Knows how to work | Owns `SKILL.md`, references, templates, eval cases, and local checks | Capability registry and invocation orchestration | Package validation and activation/task evals |
| Events | Shows initiative | Describes eligible triggers and stop conditions | Hooks, scheduler, goal loop, wakeups | No autonomous standalone start; event execution is `host-required` |
| Delegation | Coordinates others | May propose separable work and an expected return contract | Sub-agent creation, permissions, merge/conflict handling | Delegation log or host receipt; otherwise `not-supported-standalone` |
| Boundaries | Knows limits | States forbidden claims, modes, approvals, and stop/escalation rules | Permission enforcement, policy engine, cost and privacy controls | Negative evals plus host enforcement evidence where effects are possible |
| Recovery | Does not get lost | Defines checkpoints, resumable artifacts, and evidence needed to continue | Durable checkpoint store, retries, leases, idempotency | Local artifact can support recovery; automatic recovery is `host-required` |
| Evals | Checks itself | Owns positive, negative, boundary, and realistic scenario cases | Model runner, reviewer independence, trace store, CI | Corpus/schema check is static; executed eval results need runner receipts |
| External outcome | Proves usefulness | Defines the expected change and verification criterion | Real-world action, attribution window, measurement and receipt | Verified external state or metric; without it, report `not verified` |

## Architectural consequences

- Standalone mode can produce an evidence-aware review, templates, and a next
  step. It cannot supply missing identity, memory, connectors, approvals, or
  durable runtime guarantees.
- Embedded mode returns a structured product-decision result to Robin; Robin
  remains owner of identity, memory, permissions, tools, and governance.
- `skill-instruction` is not deterministic enforcement. Use
  `script-checked`, `host-required`, or `not-supported-standalone` when that is
  the real boundary.
- Never infer success from a polished artifact, model confidence, tool-call
  intent, or process exit alone. Verify the external state named in advance.
