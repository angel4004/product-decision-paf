# Evidence policy

## Evidence ledger

Classify every decision-critical statement:

| Class | Meaning | Treatment |
|---|---|---|
| Fact | Directly observed in an identified source | Preserve source, date, scope, and freshness |
| Hypothesis | Testable statement about user, mechanism, or outcome | Name disconfirming evidence and test |
| Interpretation | Meaning inferred from one or more facts | Keep separate from the underlying facts |
| Decision | Human or authorized host commitment | Name owner, time, and reversibility |
| Next action | Concrete work intended to reduce uncertainty or create value | Add owner and pass/fail checkpoint |
| Unsupported claim | Strong wording without sufficient evidence | Block or weaken it |

## Evidence quality

For quantitative evidence, record the metric definition, numerator, denominator,
period, segment, exclusions, baseline, and uncertainty. For qualitative evidence,
record the source type, selection method, sample, observed behavior versus stated
preference, and contradictory cases.

Do not invent a methodology default for a target, threshold, sample, or time
window. If a useful working number is needed, label it a proposed assumption,
state its rationale, and leave final acceptance with the decision owner.

Use these evidence states:

- `supported`: relevant sources cover the claim at the required grain.
- `partial`: useful signal exists, but a decision-critical dimension is missing.
- `contradictory`: credible sources point in different directions.
- `stale`: the source no longer represents the decision period or product state.
- `missing`: no qualifying source is available.
- `not-applicable`: the claim does not require this evidence class.

Never translate `partial`, `stale`, or `contradictory` into `supported`.

## Source routing before asking

1. List sources already supplied in task context.
2. Identify approved local or connected sources the host can access.
3. Map each claim to its owning source instead of substituting a convenient proxy.
4. Read only the minimum source scope needed for the decision.
5. Ask the user only for decision-critical evidence that remains unavailable.
6. State read-only, privacy, freshness, truncation, and coverage boundaries.

The skill itself has no connectors. In standalone mode, source discovery is an
instruction; in embedded mode, the host owns connector selection and proof of
successful reads.

## Contradictions and missing evidence

When evidence conflicts:

- show both observations and their scope;
- identify whether the conflict is temporal, segment-specific, methodological,
  or genuinely unresolved;
- block the strongest affected claim;
- propose one check that can change the decision.

When evidence is insufficient, return a useful partial review. Do not turn a
request for more data into the entire output.

## External outcome

An artifact or recommendation is not an external outcome. Outcome evidence needs
an observable change, a relevant baseline or comparison, a time window,
attribution limits, and a source or receipt. If the host cannot observe those,
label the outcome `not verified`.
