# Release checklist

## Release posture

Portability mode: **Cross-platform**.

Use Python for portable package validation. Do not include PowerShell-only
runtime assumptions, Codex workspace hooks, local memory, traces, scheduler
state, private receipts, or source-project automation in the standalone skill.

This checklist starts with every execution-dependent gate unverified. Replace a
placeholder only after running the exact command and recording a safe result.
`implemented` documentation and `eval-defined` cases are not release passes.

## Human decisions and boundaries

- [x] **PAF terminology:** current user direction and primary sources select
  Product Architecture Framework for hypothesis work.
- [x] **Architecture claim:** label the skill architecture Bayram-informed
  synthesis; do not claim the exact matrix is a verbatim Bayram publication or
  that Bayram authored PAF.
- [x] **Source reuse:** do not copy unlicensed source-repo text; original target
  wording only. Attribute the official PAF-derived summaries in `NOTICE.md`.
- [x] **Implicit activation:** use `allow_implicit_invocation: false`.
- [x] **Public visibility:** the named target already exists as a public empty
  repository and the goal explicitly requires publication there.

No software license is selected for the original package. Publication is
allowed, but the repository must not be described as open source or as granting
reuse rights for the unlicensed portions.

## Package validation

Run from the target repository root:

```text
python scripts/quick_validate.py
```

The validator must check at least:

- `SKILL.md` exists and its frontmatter contains only the approved `name` and
  `description`;
- the skill name is `product-decision-paf`;
- `agents/openai.yaml` exists and references `$product-decision-paf`;
- every runtime reference and asset is linked directly from `SKILL.md`;
- migration and critical-behavior coverage documents exist;
- positive and negative eval cases cover the required case IDs;
- forbidden claim classes are represented;
- no private memory, trace, credential, transcript, receipt, or source-product
  artifact was copied;
- no obvious secret-looking strings or local-user absolute paths exist;
- no required file is a placeholder;
- Markdown links resolve.

Record the actual result:

```text
command: python scripts/quick_validate.py
status: PASS on pre-publication candidate
exit_code: 0
checks_run: 9
eval_cases: 37
checked_commit: PENDING FIRST COMMIT
companion_checks: official skill validator PASS; validator unit tests 4/4 PASS
```

The command establishes package integrity only. It does not prove model
behavior, methodology correctness, live source access, approvals, or product
impact.

## Repository checks

```text
git rev-parse --show-toplevel
git remote -v
git status --short --branch
git diff --check
git ls-files
```

Record:

```text
repository_root: C:/tmp/product-decision-paf
origin: angel4004/product-decision-paf
branch: main
working_tree: reviewed pre-publication candidate
diff_check: PASS
tracked_file_review: PASS; only target package files
```

Confirm manually:

- [x] Source and target are separate Git repositories.
- [x] No unrelated user changes are included.
- [x] No `memory/local`, `traces`, `.env*`, raw transcripts, credentials,
  sessions, private receipts, or generated runtime state is tracked.
- [x] No source-client-specific product or recovery rule leaked into the
  generic skill.
- [x] No source file was recursively copied without classification.

## Secret and privacy scan

First run the package validator. Then run an available trusted secret scanner
against both tracked files and the complete candidate working tree. Record the
exact tool and version; do not paste detected secret values into a report.

```text
primary_command: python scripts/quick_validate.py
secondary_scanner: NOT-AVAILABLE (gitleaks, trufflehog, detect-secrets absent)
scanner_version: NOT-AVAILABLE
tracked_files_result: PASS built-in scan over the staged candidate
working_tree_result: PASS built-in secret/path/privacy scan plus targeted rg review
false_positives_reviewed_by: primary release agent
```

Any real credential, private content, raw trace, or unexplained secret-like
literal blocks release. Synthetic secret fixtures should be generated at test
runtime rather than committed.

## Eval inventory and behavior runs

Required positive activation coverage:

- [x] product hypothesis review;
- [x] PAF review;
- [x] PMF/PCF evidence question;
- [x] explicit product passport;
- [x] next product step;
- [x] claims in an artifact;
- [x] CPO/founder decision argumentation.

Required negative activation coverage:

- [x] ordinary coding;
- [x] become Robin/root agent;
- [x] persist personal memory;
- [x] unapproved external write;
- [x] generic landing/visual production without a product decision;
- [x] financial, legal, and medical advice.

Required behavior coverage:

- [x] all twelve quality-critical invariants;
- [x] PMF, PCF, business impact, customer success, user need, metric uplift,
  readiness, and PAF consistency claim boundaries;
- [x] source routing before asking for more data;
- [x] standalone and embedded boundaries;
- [x] privacy/publication;
- [x] realistic product passport;
- [x] disputed PMF/PCF;
- [x] insufficient and contradictory evidence;
- [x] one default next step with a pass/fail rule.
- [x] null-base and data-base routing;
- [x] customer/need, value proposition, solution, and business-model hypothesis
  classification;
- [x] upstream dependency and the value-plus-solution co-test exception;
- [x] Hypothesis Card completeness;
- [x] Understand–Identify–Execute and knowledge return to the Nexus;
- [x] no fabricated Confidence Point or composite PAF score.

Static eval inventory:

```text
command: python scripts/quick_validate.py
status: PASS
case_count: 37
required_case_ids: 37/37
quality_critical_invariants: 12/12 mapped
missing_case_ids: none
```

Behavior execution requires an independent model or host harness:

```text
command: six independent fresh-context forward reviews
status: TARGETED PASS; COMPLETE 37-CASE HARNESS NOT RUN
model_runtime: Codex subagents; exact build not exposed
skill_commit: pre-publication candidate
cases_run: 6
passed: 6
failed: 0
blocked: 0
safe_report_ref: current goal execution record; no raw private input persisted
```

Do not use `<HOST_EVAL_COMMAND>` literally. If no harness exists, record
`host-required` and keep behavior unverified.

## Standalone forward test

Run the packaged skill in a fresh context without source-repo instructions or
the intended answers. Include at least:

1. a realistic existing-product decision;
2. a new-product request where a passport was not requested;
3. a disputed PMF/PCF claim;
4. an insufficient-evidence case;
5. an ordinary coding negative control.

Record:

```text
command_or_thread_refs: five fresh standalone subagent runs
status: PASS for required targeted scenarios
skill_commit: pre-publication candidate
context_leakage_check: PASS; agents received package path and bounded prompt only
reviewer: independent Codex subagents plus primary release agent
findings: null-base, data-base, value/solution co-test, insufficient evidence,
  and coding/memory negative behavior passed; first runs exposed unlabeled
  thresholds, then the patched skill and regression case passed reruns
```

Success requires transferable behavior from the skill package, not leaked
source context.

## Robin embedded test

Robin must remain the root agent and supply only bounded task context. The test
must show:

- [ ] Robin owns identity, user profile, memory, permissions, tools, approvals,
  delivery, and receipts;
- [ ] the skill receives bounded `task`, `goal_context`, `source_evidence`,
  `constraints`, `runtime_evidence`, and `language`;
- [ ] the skill returns the documented structured product-decision result;
- [ ] the skill does not write memory, broaden source scope, call unapproved
  tools, send, publish, schedule, commit, or deploy;
- [ ] missing host evidence returns `host-required`.

Record:

```text
command: one bounded-context Robin capability forward review
status: TARGETED OUTPUT PASS; HOST ENFORCEMENT STILL REQUIRED
robin_commit_or_version: not applicable to isolated capability test
skill_commit: pre-publication candidate
cases_run: 1
safe_receipt_ref: current goal execution record; no private payload persisted
```

## External outcome boundary

A well-formed review, passport, or recommendation is not proof of product value.
Before claiming an external outcome, require:

- observable product or user change;
- baseline or comparison;
- metric definition, period, denominator, and exclusions;
- attribution limits;
- source or receipt owned by the host.

If unavailable, record `external_outcome: NOT VERIFIED`.

## GitHub pre-publication check

Read-only inspection:

```text
gh repo view angel4004/product-decision-paf --json nameWithOwner,url,visibility,defaultBranchRef
git remote -v
git status --short --branch
```

Record:

```text
github_repo_exists: yes
visibility: public
default_branch: main
remote_history_reviewed: yes; no heads returned and repository size was 0
divergence_reviewed: yes; no remote history to reconcile
```

Before publication:

- [x] Fetch and review remote history using an approved network operation.
- [x] Reconcile existing commits; do not blind `git init`.
- [x] Do not force push.
- [x] Review the exact staged diff and commit scope.
- [x] Treat the explicit goal to publish this exact repository as publication
  authorization within the stated non-force scope.

## Release evidence record

Populate this table with actual results. Initial values deliberately do not
claim success.

| Gate | Required evidence | Current result |
|---|---|---|
| Package structure/frontmatter | `quick_validate.py` command, exit code, commit | `LOCAL PASS; COMMIT/CI BINDING PENDING` |
| Reference/link integrity | Validator output | `PASS` |
| Eval inventory | Case count and missing IDs | `PASS: 37 IDs; 12 invariant mappings` |
| Validator failure controls | Unit tests | `PASS: 4/4` |
| Behavior evals | Harness, runtime, commit, case report | `6 TARGETED PASS; FULL HARNESS NOT RUN` |
| Standalone forward test | Fresh-context refs and reviewer | `PASS: 5 TARGETED SCENARIOS` |
| Robin embedded mode | Host receipt | `OUTPUT PASS; HOST ENFORCEMENT REQUIRED` |
| Secret/privacy scan | Exact scanner commands and safe summary | `BUILT-IN PASS; SECONDARY NOT AVAILABLE` |
| PAF terminology/provenance | Human decision and primary-source refs | `RESOLVED AND ATTRIBUTED` |
| Source reuse/license | Human rights/licensing decision | `ORIGINAL WORDING; PARTIAL CC BY-SA; NO PACKAGE LICENSE` |
| External outcome | Metric/receipt with attribution | `NOT VERIFIED` |
| Git remote/history | Git/GitHub readback | `PASS: PUBLIC EMPTY MAIN` |
| Commit/push | Commit SHA and remote readback | `PENDING` |

## Publication and readback

Only after every release-blocking row is resolved:

```text
git add <reviewed-target-files>
git commit -m "<reviewed-message>"
git push origin <reviewed-branch>
gh repo view angel4004/product-decision-paf --json url,visibility,defaultBranchRef
```

These are release instructions, not standing authorization. Use the active
host's approval boundary.

Final handoff must include:

- repository URL and published commit SHA;
- portability mode;
- exact validator and eval results;
- privacy/secret scan result;
- terminology/provenance and license decisions;
- source functions retained, adapted, host-owned, and dropped;
- known standalone and embedded gaps;
- standalone usage and Robin embedded invocation guidance.
