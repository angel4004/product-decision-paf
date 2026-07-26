# PAF hypothesis card

This Markdown card is a human-readable view. For longitudinal work, render it
from the canonical JSON record in
`assets/hypothesis-workspace-state.schema.json`; do not maintain two sources of
truth.

## Identity and lifecycle

- Workspace ID and expected workspace revision:
- Decision scope ID:
- Hypothesis ID and card revision:
- Lifecycle state:
- Verdict: pending / confirmed / disconfirmed / unresolved / not_run
- Host execution ref (required from `running` onward):
- Last accepted persistence receipt ref:

## Origin and decision

- Product/business goal:
- Nexus revision at origin:
- Originating Nexus entry IDs:
- Reason for opening the hypothesis:
- Decision this hypothesis must unlock:
- Base: null_base / data_base

## Hypothesis

- PAF class: customer_need / value_proposition / solution / business_model
- Lifecycle context: discovery / acquisition_activation / onboarding /
  go_to_market / adoption / post_release_impact
- Statement:
- Target segment:
- Situation:
- Rationale:

## Upstream dependencies

| Dependency ID | Mode | Required class and hypothesis ID | Evidence status and IDs | Co-test plan ref |
|---|---|---|---|---|
|  | prerequisite / co_test |  |  | null for prerequisite |

For a co-test, keep separate peer hypothesis IDs, approved test contracts,
metric results, interpretations, and verdicts. Running peers use the same host
execution ref; one may close while the other remains reviewable.

For `evidence_status = supported`, record the current unsuperseded supported
evidence and current supported Nexus lineage. A historical confirmed card alone
is insufficient.

## Validation design

- Experiment or observation:
- Metrics:

| Metric ID | Role | Definition | Numerator/denominator | Segment and baseline | Criterion | Provenance and approval status |
|---|---|---|---|---|---|---|
|  | primary / guardrail / diagnostic |  |  |  |  | owner_supplied / evidence_derived / proposed_assumption / unset |

- Sample population, target size, inclusion, exclusion, rationale, provenance,
  approval:
- Time window, rationale, provenance, approval:
- Known confounders:
- If confirmed:
- If disconfirmed:
- If unresolved:
- Decision-rule approval ID, owner tenure, subject revision/hash, and safe ref:
- Pending approval scope, owner tenure, subject revision/hash, reason, and source
  change-set ID:
- Pending-request resolution ID, original tenure/subject, resolution
  (`withdrawn` / `invalidated_by_tenure_transition`), active authority, reason,
  and safe receipt:

## Evidence and claims

- Hypothesis evidence IDs:
- Safe source refs, periods, filters, denominators, and freshness:
- New claim-log events:
- Active blocked claims derived from latest claim events:

## Result at closure

- Observations:
- Interpretation:
- Overall validity: adequate / limited / invalid / not_reviewed
- Metric results:

| Metric ID | Evidence IDs and period | Observed summary | Actual numerator/denominator | Actual sample | Criterion evaluation | Validity |
|---|---|---|---|---|---|---|
|  |  |  | canonical decimal strings or null |  | met / not_met / indeterminate | adequate / limited / invalid |

- New Nexus entry IDs added in this workspace revision:
- External outcome status: not_verified / observed / attribution_limited /
  verified
- External outcome evidence IDs:
- External outcome host receipt ref (only for `verified`):
- Decision taken:
- Decision-owner acceptance ref:

These external-outcome fields are the immutable closure snapshot. Do not update
them after the card becomes terminal.

## Post-release outcome timeline

Render later assertions from authoritative append-only `outcome_log`:

| Event ID | Status | Evidence IDs | Summary / attribution note | Host receipt | Supersedes |
|---|---|---|---|---|---|
|  | observed / attribution_limited / verified / withdrawn | current usable evidence |  | only for verified | latest prior event |

Observed and verified require supported evidence; attribution-limited allows
supported/partial evidence and requires a note; withdrawn requires
contradictory evidence. Never rewrite the terminal result.

## Relations

- Based-on hypothesis IDs:
- Replaces hypothesis ID (only a closed or superseded historical target):

## Next step

- Action and owner ref:
- Expected evidence:
- Pass rule:
- Fail rule:

## Persistence handoff

- Change-set ID and expected/candidate workspace revisions:
- Appended decision-scope, owner-tenure, Nexus, evidence, and claim-event IDs:
- Appended outcome-event IDs:
- Created/updated hypothesis revisions:
- New Nexus decision authority: subject hash, owner tenure, scope, safe receipt,
  reversibility:
- Required owner approvals:
- Persistence status: proposed / accepted / rejected / conflict / failed /
  outcome_unknown / not_persisted
- Matching receipt ref and state hash:
