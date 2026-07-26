---
name: product-decision-paf
description: Use when evaluating product decisions, product artifacts, user evidence, PAF architecture/consistency, PMF/PCF claims, or founder/CPO product arguments. Helps decide what to inspect, which claims are unsupported, what artifact is missing, and what the next product step should be.
---

# Product Decision PAF

Apply the Product Architecture Framework (PAF) hypothesis method to a product
decision, then expose its evidence, artifact, enforcement boundary, and one next
step. Package the method as a bounded skill using the Bayram-informed architecture
rules below; do not turn the skill into a root workspace.

## Boundaries

- Do not act as Robin, a root agent, package-owned durable memory, governance
  layer, scheduler, deterministic harness, or source of truth.
- Do not accept PMF, PCF, business impact, customer success, product need, metric
  uplift, readiness, or PAF-fit claims without the evidence required by
  [claim boundaries](references/claim-boundaries.md).
- Do not store product state, private memory, traces, credentials, raw
  transcripts, or runtime receipts inside this package. Work only with task
  context supplied by the user or host.
- Treat Nexus as the product-domain model of typed, evidence-bound knowledge,
  not as a storage engine. Own its portable semantics; leave product-specific
  persistence and retrieval to the host.
- Do not perform writes or expand permissions on your own authority. For
  longitudinal work, return a versioned persistence proposal. Only an authorized
  host adapter may commit it and return a receipt.
- Do not use this skill for ordinary coding, visual production without a product
  decision, or financial, legal, or medical advice.

## Runtime modes

- **Standalone:** provide an instruction-supported review. A compatible host may
  use the included file adapter against a user-selected state root; otherwise
  return either a complete portable change set or, when required bindings are
  missing, a non-committable proposal intent with `not_persisted`. Source
  access, write authority, retries, traces, and outcome receipts remain with
  the user or host.
- **Embedded in Robin:** accept bounded task context and return a structured
  product-decision result plus an optional state-change proposal. Robin retains
  identity, memory, source access, persistence, permissions, governance, and
  delivery. Read
  [Robin embedded mode](references/robin-embedded-mode.md) before returning.

## Progressive loading

Read [routing](references/routing.md) for every invocation. Then load only what
the selected route needs:

- for a hypothesis, experiment, PAF review, or feature decision, read the
  [PAF hypothesis method](references/paf-hypothesis-method.md); add
  [PAF principles](references/paf-principles.md) only for goal or consistency
  work;
- for starting, resuming, saving, handing off, or recovering longitudinal
  hypothesis work, read the
  [hypothesis state and persistence contract](references/hypothesis-state-and-persistence.md)
  and use the canonical
  [workspace-state schema](assets/hypothesis-workspace-state.schema.json),
  [proposal-intent schema](assets/hypothesis-proposal-intent.schema.json),
  [change-set schema](assets/hypothesis-change-set.schema.json), and
  [persistence-receipt schema](assets/persistence-receipt.schema.json). The
  optional standalone adapter stores them in the
  [atomic state-bundle schema](assets/hypothesis-state-bundle.schema.json);
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
2. **Rehydrate longitudinal state when applicable.** Ask the host to load the
   bounded workspace with active decision scope and owner tenure, relevant
   Nexus/evidence/claim/outcome events, latest Hypothesis Card revision, and
   last persistence receipt. Treat a missing or rejected receipt as
   `not_persisted`; never infer continuity from chat history alone. An
   explicitly absent workspace is initialization, not a failed resume: when the
   user asks to start a named hypothesis and all required bindings are
   available, return the complete revision-zero create change set in this
   response (`workspace_operation = create`, expected workspace revision
   `null`, candidate workspace revision `0`, and that stable hypothesis ID at
   revision `0`). If any binding needed for a complete candidate state is
   unavailable, do not invent it and do not call a sketch a change set. Return
   a schema-valid `proposal_intent` in this response, list every unresolved
   binding, set `commit_eligible: false` and `persistence_status:
   not_persisted`, and name the materialization contract. Label a complete
   change set `persistence_status: proposed` when a host adapter handoff is
   available; the absence of a receipt means the candidate is not yet accepted.
3. **State the decision.** Name the actor, product or business goal, baseline,
   target, period, and decision. Mark missing fields instead of inventing them.
4. **For PAF work, set the base and uncertainty.** Use `null-base` when no
   product evidence base exists; use `data-base` when current behavior can reveal
   a bottleneck. Identify the earliest decision-critical hypothesis class:
   customer/need, value proposition, solution, or business model. Record
   acquisition, activation, onboarding, go-to-market, adoption, and post-release
   impact separately as lifecycle context. Do not use a downstream experiment to
   stand in for missing upstream knowledge.
5. **Build the evidence ledger.** Separate facts, hypotheses, interpretations,
   decisions, next actions, and unsupported claims. Preserve denominators,
   periods, filters, provenance, freshness, and contradictions.
6. **Create the minimum artifact.** Use only the route-matched primary asset.
   Compact typed Nexus, claim, and post-release outcome events plus the
   persistence handoff are state metadata, not extra user deliverables. For raw
   uncertainty, prefer a Hypothesis Card or one next step over a large
   document.
7. **Run the PAF loop when applicable.** `Understand` the Nexus and bottleneck;
   `Identify` and test the relevant hypothesis; `Execute` only a sufficiently
   supported solution while measuring the goal. Return confirmations,
   disconfirmations, and surprises as new knowledge. Value and solution, or a
   solution soft launch and business model, may share an experiment, but each
   keeps a separate hypothesis ID, owner-approved test contract,
   `metric_results`, conclusion, and verdict; bind the pair through
   `mode = co_test`, one `co_test_plan_ref`, and shared host execution evidence.
   One peer may close while the other remains reviewable after that shared run.
   Add learning as typed Nexus entries and list the same-revision IDs in
   `result.new_nexus_entry_ids`. A terminal verdict proposal must append at
   least one evidence-bound learning entry and name it in
   `new_nexus_entry_ids` in that same candidate revision; if no such learning
   can be supported, do not close the card. Treat measured impact as an external
   outcome, not a fifth hypothesis class.
8. **Challenge strong claims and stale authority.** If evidence is
   insufficient, block the claim and provide one safer statement. Do not accept
   a historical upstream verdict after its evidence or supported Nexus lineage
   was superseded. Treat the terminal card's external-outcome fields only as
   its closure snapshot; append later impact updates to `outcome_log`, never to
   the closed card.
9. **Prepare the state handoff when continuity matters.** When all required
   bindings are known, return a complete change set with the expected workspace
   revision, active decision-scope and owner-tenure bindings, a new immutable
   Hypothesis Card revision, typed Nexus/evidence/claim/outcome deltas,
   subject-bound required owner approvals, and exact change manifest. Return
   that actual portable transaction in the current response; do not merely tell
   the host to reconstruct it later. With an adapter handoff, label it
   `proposed`; without an adapter, state root, or write authority, the same
   commit-eligible change set is `not_persisted`. When any schema-required
   binding is unknown, return only a schema-valid proposal intent with the
   known values, unresolved bindings, exact materialization requirements,
   `commit_eligible: false`, and `not_persisted`. Never pass an intent to
   `commit` or describe it as an atomic change set. An unresolved rule may be
   checkpointed only as `awaiting_owner_rule`; a complete checkpoint change set
   must carry actual subject revision/hash and
   `source_change_set_id` in both the pending request and
   `required_owner_approvals`. It does not authorize execution. Enter
   `running` only with both a host execution ref and a current
   `state_transition` owner approval whose subject binds the candidate
   hypothesis revision and that execution ref; neither the execution ref nor a
   persistence receipt substitutes for this approval. When the execution ref
   is present but approval is not, return the complete `running` candidate plus
   its concrete required-approval request; label it only `proposed`, never as an
   entered or persisted state. Do not mutate the approved test contract after
   `ready_to_run`. Every appended evidence event must state a sequence greater
   than the preserved prefix. On a stale revision, return `conflict` and
   require reload; do not overwrite. Treat exit code `6` as
   `outcome_unknown`: verify and load before retrying or claiming persistence.
   Bind every Nexus decision to exact `decision_authority`. Resolve a removed
   pending owner request through a matching approval, `withdrawn`, or
   `invalidated_by_tenure_transition` appended in the same candidate revision
   as the owner transition; preserve its history.
10. **Expose enforcement.** Label important results as `script-checked`,
   `instruction-supported`, `host-required`, or
   `not-supported-standalone`. Prompt adherence alone is not
   `quality-ready` or `production-ready`.
11. **Return one decision-shaped result.** Include the applicable PAF base, goal,
   routed sources, hypothesis class and upstream dependencies, facts,
   hypotheses, interpretations, active blocked claims derived from `claim_log`,
   latest post-release outcome from `outcome_log` when applicable, artifact or
   recommendation, evidence status, enforcement boundary, persistence status
   when applicable, and one default next step with a pass/fail rule.

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
- Never say `saved`, `remembered`, or `persisted` unless the host supplied an
  accepted receipt matching the proposal and new revision. In standalone mode,
  accepted means atomic replace plus exact readback; power-loss durability is
  host-dependent.
- Never call a partial object a change set. A proposal intent is portable but
  non-committable; it becomes a transaction only after all bindings are
  resolved and the complete candidate passes the change-set contract.
- End every in-scope review, including a refusal or permission boundary, with
  one `Next step` and a decision rule.

Run `python scripts/quick_validate.py` after changing this package. Use
`python scripts/hypothesis_state.py --help` for the optional standalone
file-adapter commands. These scripts validate or persist local artifacts; they
do not prove model behavior or external outcomes.
