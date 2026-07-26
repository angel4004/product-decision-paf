# Release checklist

## Release scope

- Repository: `angel4004/product-decision-paf`.
- Branch: `main`.
- Portability mode: cross-platform Agent Skill.
- Publication method: reviewed non-force push.
- Package boundary: portable method, schemas, reference file adapter, tests,
  eval definitions, and public-safe documentation only.
- Host boundary: identity, authentication, connectors, private state,
  permissions, backups, delivery, and external outcome receipts remain outside
  the package.

The repository is public but has no package-level software license. Do not call
it open source or infer reuse rights for unlicensed portions. PAF-derived
material and the Bayram-informed synthesis are attributed and bounded in
`NOTICE.md` and the architecture reference.

## Architecture decisions

- [x] The skill owns PAF hypothesis semantics and the Nexus content model.
- [x] The skill does not own hidden product memory or a private default store.
- [x] Longitudinal work uses versioned workspace state, immutable hypothesis
  revisions, append-only evidence/Nexus/claim/outcome logs, change sets, and
  persistence receipts.
- [x] Standalone mode may use the explicit file adapter only at a user-selected
  absolute state root outside the package.
- [x] Robin is an optional host adapter, not a package dependency.
- [x] If all product/state bindings are known but no usable adapter exists, the
  skill returns the complete change set with `not_persisted`.
- [x] If a schema-required binding is unknown, the skill returns a separate
  schema-valid proposal intent with `commit_eligible = false`; it never calls
  the partial artifact a change set.
- [x] PAF uses exactly four hypothesis classes: customer need, value
  proposition, solution, and business model. Lifecycle contexts and external
  impact are modeled separately.
- [x] Owner approval, execution evidence, persistence, and external outcomes
  remain distinct proof types.

## Local validation evidence

Run from the repository root:

```text
python scripts/quick_validate.py --root .
python -m unittest discover -s tests -v
python "$CODEX_HOME/skills/.system/skill-creator/scripts/quick_validate.py" .
python -m py_compile scripts/hypothesis_state.py scripts/quick_validate.py tests/test_hypothesis_state.py tests/test_quick_validate.py
git diff --check
```

Candidate results on 2026-07-26:

```text
package_validator: PASS
checks_run: 12
eval_cases: 50
lifecycle_scenarios: 11
unit_tests: 115/115 PASS
dependency_free_ci_simulation: 115 tests PASS; 3 optional jsonschema checks skipped
optional_jsonschema_local_differential: PASS
official_skill_validator: PASS
python_compile: PASS
diff_check: PASS
strict_json_duplicate_and_nonfinite_scan: PASS
```

These checks establish package structure, schemas, deterministic adapter
semantics, and documented eval coverage. They do not prove production host
behavior, authenticated owner identity, storage durability beyond the
documented scope, or business impact.

## Behavioral evidence

The targeted longitudinal evaluation used isolated rubric-withheld turn
generators and an independent semantic grader. Release audit later applied the
actual artifact schemas and withdrew the former aggregate remediation pass:

```text
baseline: 21/27 turns; 5/11 scenarios fully passing
baseline_failures: 6
remediation_semantic_review: 6/6 described intended rules
former_effective_27_of_27: WITHDRAWN
model_emitted_full_transaction_conformance: NOT_ESTABLISHED
proposal_intent_conformance: 1 positive plus 7 negative controls PASS
focused_model_no_store_intent: current nested artifact PASS; predecessor rejected
runtime: Codex fresh-context subagents; exact build not exposed
report: docs/longitudinal-forward-eval-report.md
```

The complete 50-case host harness was not executed. The baseline is
`instruction-supported`, not a production runtime receipt. Raw baseline and
rerun outputs remain Git-ignored and unpublished.

## Secret, privacy, and package-boundary scan

- [x] The package validator scanned the complete candidate for selected secret,
  credential, private-path, trace, receipt, and copied-memory hazards.
- [x] Strict JSON parsing covered package and ignored eval JSON without printing
  private payloads.
- [x] `evals/results/` and `evals/results-rerun/` are ignored.
- [x] CI remote actions use full commit SHAs, checkout does not persist
  credentials, and validation CI performs no network dependency installation.
- [x] No `.env*`, credential, session, raw transcript, private memory, runtime
  receipt, or generated host state is tracked.
- [x] Targeted review found no source-client-specific product state.
- [ ] Secondary secret scanner: unavailable locally (`gitleaks` was not
  installed). The built-in scan is not a complete secret-history audit.

## Repository and publication preflight

Read-only preflight on 2026-07-26:

```text
remote: https://github.com/angel4004/product-decision-paf.git
visibility: PUBLIC
default_branch: main
local_head_before_release: 0d7487cc3673b5f007cc0122522d06305c65ac9e
origin_main_before_release: 0d7487cc3673b5f007cc0122522d06305c65ac9e
divergence_before_release: 0 ahead / 0 behind
force_push: prohibited
```

Candidate publication status:

```text
implementation_commit: not_created_yet
implementation_push: pending
implementation_ci: pending
release_evidence_commit: pending
final_remote_readback: pending
```

These are live release gates, not placeholders for a success claim. Replace
them only with exact commit SHAs, GitHub Actions results, and remote readback
after each operation succeeds.

## Release gates

| Gate | Current result |
|---|---|
| Skill frontmatter and package structure | PASS |
| Runtime references and Markdown links | PASS |
| Four PAF classes and dependency/co-test semantics | PASS |
| Workspace/proposal-intent/change-set/receipt/bundle schemas | PASS |
| Unit suite: validator plus file adapter | PASS, 115/115 |
| Static eval inventory | PASS, 50 cases |
| Lifecycle inventory | PASS, 11 scenarios |
| Targeted longitudinal behavior | PARTIAL, baseline 21/27; former effective 27/27 withdrawn |
| Standalone no-store artifact contract | PASS deterministic fixture, 7 negative controls, and one focused nested model intent; full model transaction run not established |
| Robin failed-store boundary | PASS in targeted baseline |
| Secret/privacy built-in scan | PASS |
| Secondary secret scanner | NOT AVAILABLE |
| External product outcome | NOT VERIFIED |
| Production Robin persistence adapter | HOST-REQUIRED; not runtime-tested here |
| Implementation commit and non-force push | PENDING |
| Cross-platform GitHub Actions matrix | PENDING |
| Final remote commit/tree readback | PENDING |

## Publication procedure

1. Review the exact tracked candidate and confirm ignored raw eval outputs are
   absent from the index.
2. Fetch `origin/main` and fail closed on divergence.
3. Create the implementation commit and push `main` without force.
4. Wait for the exact GitHub Actions run and require every matrix job to pass.
5. Record the implementation SHA, workflow URL, job matrix, and remote
   readback in this file.
6. Commit that release evidence, push without force, wait for its exact workflow
   run, and perform final remote readback.
7. Report external outcome as not verified unless a separate host-owned metric
   and attribution receipt exists.

## Final handoff requirements

- repository URL, final commit SHA, and exact CI result;
- standalone and Robin embedded usage boundary;
- local validator, unit-test, and targeted behavior counts;
- secret/privacy scan scope and unavailable secondary scanner;
- explicit statement that the package has no hidden memory;
- explicit statement that durable continuity works through host-owned state and
  accepted receipts;
- remaining host/runtime and external-outcome gaps.
