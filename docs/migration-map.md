# Migration map

## Scope

Source repository: `angel4004/cpo-codex-copilot` (audited from a clean local
checkout at source commit `bb67e75`).

Target repository: `angel4004/product-decision-paf`.

Portability decision: **Cross-platform**. Portable validation belongs in Python.
Windows PowerShell runners, Codex workspace hooks, local memory, traces,
automation, commits, external effects, and receipts remain host-owned.

This map classifies durable system functions rather than promising that source
quality was copied. A component appears more than once when its portable
instruction layer and host-runtime layer require different decisions.

## Terminology and provenance decision

The source `README.md` defines PAF as **Product Architecture Framework**. An
earlier migration brief left the expansion ambiguous; the current owner
direction and a primary-source review resolve the target method as the official
Product Architecture Framework hypothesis process.

The target therefore separates two layers:

- **PAF methodology:** goal and Nexus context, null base/data base,
  Understand–Identify–Execute, typed hypotheses, upstream dependencies,
  Hypothesis Cards, evidence, and decisions;
- **Bayram-informed skill architecture:** the assignment of identity, user
  context, sources, memory, model reasoning, tools, skills, events, delegation,
  boundaries, recovery, evals, and external outcomes between a portable skill
  and its host.

`references/paf-principles.md` and
`references/paf-hypothesis-method.md` adapt the official PAF materials with
attribution. `NOTICE.md` records their CC BY-SA 4.0 boundary. The package does
not claim that Bayram authored PAF or that the architecture matrix is his
verbatim publication.

The source repository has no `LICENSE`, `LICENSE.md`, `COPYING`, or `NOTICE`.
No source file is copied verbatim. The rest of the target software package has
no selected software license and must not be described as open source.

## Component map

| Source component | Current function | Classification | Target artifact | Enforcement level | Evidence / check |
|---|---|---|---|---|---|
| `AGENTS.md` — portable behavior | Evidence-first product role, routing, goal-first procedure, compact claim review | `adapt` | `SKILL.md`; `references/routing.md`; `references/evidence-policy.md`; `references/claim-boundaries.md` | `skill-instruction` → `instruction-supported` | `scripts/quick_validate.py` checks direct references; behavioral evals still required |
| `AGENTS.md` — root identity/runtime | CPO Copilot identity, workspace bootloader, permissions, hooks, memory, trace runner | `host-owned` | `references/robin-embedded-mode.md`; `references/enforcement-boundary.md` | `host-owned` → `host-required` | Embedded boundary eval; current host receipt if a stronger claim is made |
| `CONSTITUTION.md` | Evidence policy, PAF boundary, forbidden claims, goal-led validation, authority order | `adapt` | `references/paf-principles.md`; `references/evidence-policy.md`; `references/claim-boundaries.md` | `skill-instruction` | PMF/PCF/impact/insufficient-evidence evals |
| `docs/runtime-contract.md` — boundary model | Separates prompt guidance, deterministic checks, runner, hooks, and readiness | `adapt` | `references/enforcement-boundary.md` | `skill-instruction` plus `deterministic-script` | Coverage rows distinguish `script-checked` from `host-required` |
| `docs/runtime-contract.md` — runner/hooks | Codex workspace trace lifecycle and live hook readiness | `host-owned` | Host integration contract only | `host-owned`; unavailable standalone | Live host-dispatch receipt; never inferred from package validation |
| `ROUTING.yaml` | Task type → workflow, memory, practices, checks, fallback | `adapt` | `references/routing.md`; compact procedure in `SKILL.md` | `skill-instruction` | Activation and route-selection evals |
| `workflow-registry.yaml` — workflow semantics | Names workflow outputs and decision records | `adapt` | `references/workflows.md`; assets under `assets/` | `skill-instruction` | Eval case → route → expected artifact coverage |
| `workflow-registry.yaml` — state/trace execution | Starts and closes traceable workflows | `host-owned` | `references/enforcement-boundary.md` | `host-required` | Host trace/receipt, if used |
| `paf-enforcement-matrix.yaml` | Static mapping of critical claims to routes, practices, evals, and hook eligibility | `adapt` | `docs/equivalence-coverage.md`; claim and enforcement references | `deterministic-script` for static coverage; behavior remains host/harness | `quick_validate.py`; forward eval results recorded separately |
| `memory/MANIFEST.yaml` — curated knowledge routing | Authority, sensitivity, load rules, claim keys | `adapt` | Direct references from `SKILL.md`; no target memory subsystem | `deterministic-script` for reference presence | Validator checks every required reference is directly linked |
| `memory/MANIFEST.yaml` — local overlays | User/project/session memory and conflict policy | `host-owned` | `references/robin-embedded-mode.md` | `host-required`; unavailable standalone | Eval proves the skill does not persist or mutate memory |
| `memory/shared/product-context.md` | Root Copilot JTBD activation and artifact catalogue | `adapt` | `SKILL.md`; `references/routing.md`; target `README.md` | `skill-instruction` | Positive and negative activation cases |
| `memory/shared/methodology-context.md` | Short PAF/evidence summary and methodology freshness warning | `adapt` | `references/paf-principles.md` with explicit provenance limitation | `human-review` for attribution; otherwise instruction-supported | Primary-source review record |
| `memory/shared/operating-principles.md` | Privacy, approvals, trace limits, external-write boundaries | `adapt` | `references/claim-boundaries.md`; `references/robin-embedded-mode.md` | Instruction plus host enforcement | Privacy, memory-write, and external-write negative cases |
| `memory/templates/*` | Local user, project, and working-state templates | `host-owned` | Host-supplied task context; optionally a non-persistent passport asset | `not-supported-standalone` for durable memory | Embedded eval: no memory write |
| `workflows/activation/activate-cpo-copilot.md` | Root activation ceremony and JTBD routing | `adapt` | Skill description; `agents/openai.yaml`; `references/routing.md` | Host activation plus skill instruction | Positive and negative activation suite |
| `workflows/onboarding/create-project-passport.md` — decision procedure | Artifact inventory, goal-first framing, facts/assumptions/gaps, compact passport | `adapt` | `references/workflows.md`; `assets/product-passport-template.md` | `skill-instruction` | Realistic passport eval and goal-first negative control |
| `workflows/onboarding/create-project-passport.md` — trace calls | Start/close local trace and artifact refs | `host-owned` | Embedded host contract | `host-required` | Current host receipt, not package text |
| `workflows/onboarding/review-existing-passport.md` | Review weak claims, missing evidence, and hardening priority | `retain` | `assets/decision-review-template.md`; `references/workflows.md` | `skill-instruction` | Existing-artifact review eval |
| `workflows/onboarding/harden-project-passport.md` | Improve a passport without inventing facts | `adapt` | Product-passport and decision-review assets | `skill-instruction` | Hardening eval preserves facts and downgrades unsupported claims |
| `workflows/reviews/evidence-gap-review.md` — generic behavior | Source routing, evidence ledger, forbidden claims, one next step | `adapt` | Evidence and claim references; `assets/evidence-gap-template.md` | `skill-instruction` | Insufficient-evidence and forbidden-claim evals |
| `workflows/reviews/evidence-gap-review.md` — source-client-specific clauses | Client-specific product bridge and exact wording | `drop-with-reason` | None | Not part of target scope | Validator/publication review rejects source-product leakage |
| `workflows/reviews/paf-consistency-review.md` | Compact disputed-claim review without composite scoring | `retain` | `assets/paf-consistency-template.md`; `references/workflows.md` | `skill-instruction` | Disputed PMF/PCF and contradictory-evidence evals |
| `workflows/improvement/weekly-copilot-review.md` | Trace-based recurring improvement proposal | `host-owned` | Host documentation only | `not-supported-standalone` | Scheduler/automation remains outside target |
| `practices/copilot-ux/dialogue-first.md` | Direct useful output, brevity, requested-output preservation | `adapt` | `SKILL.md`; `references/workflows.md` | `skill-instruction` | Output-shape evals |
| `practices/copilot-ux/one-action-per-turn.md` | One decision-critical action or next step | `retain` | `SKILL.md`; `assets/next-step-template.md` | `skill-instruction` | One-default-next-step assertion |
| `practices/copilot-ux/goal-led-validation.md` | Goal → sources → evidence → artifact → decision checkpoint | `retain` | PAF/workflow references; next-step asset | `skill-instruction` | Measurable-goal eval |
| `practices/copilot-ux/artifact-boundaries.md` | Draft/review boundaries and optional UI-evidence gate | `adapt` | Decision-review asset; workflow reference | `skill-instruction` | Artifact-boundary and UI-evidence case |
| `practices/paf/*` | Answer modes, evidence strength, forbidden claims, PAF lens | `adapt` | `references/paf-principles.md`; `evidence-policy.md`; `claim-boundaries.md` | `skill-instruction`; provenance human-reviewed | Forbidden-claim suite plus terminology review |
| `practices/product-thinking/*` | Value chain, decision readiness, discovery routing, PMF evidence | `adapt` | `references/workflows.md`; `references/claim-boundaries.md` | `skill-instruction` | Passport, PMF, and recommendation evals |
| `evals/behavior/*` — positive cases | Declarative prompts and expected behavior | `adapt` | `evals/cases/positive/` | Eval definition; no enforcement until run | Case schema plus independent forward run |
| `evals/behavior/*` — negative cases | PMF/PCF/impact/contradiction/weak-evidence controls | `retain` | `evals/cases/negative/` | Eval definition; no enforcement until run | Forbidden-output assertions |
| `evals/protocol/*` | Adapter contract for an external model harness | `host-owned` | Embedded-mode test contract | `host-required` | Actual harness command and receipt |
| `evals/rubrics/*` | Minimal qualitative scoring criteria | `adapt` | Target eval README/rubrics with explicit pass rules | Human or host-eval | Rubric schema and reviewed outputs |
| `evals/structural/*` | Text descriptions of static smoke criteria | `adapt` | `scripts/quick_validate.py`; `docs/release-checklist.md` | `deterministic-script` | Actual validator exit code |
| `evals/fixtures/redaction/*` | Synthetic sensitive strings for the source redactor | `drop-with-reason` | Generate test strings at runtime if needed | Deterministic test only | Public target must contain no secret-looking fixture literal |
| `tools/check-structure.ps1`, `check-links.ps1`, `check-routing.ps1`, `check-eval-schema.ps1`, `check-migration-coverage.ps1` | Portable structural consistency | `adapt` | Cross-platform `scripts/quick_validate.py` | `deterministic-script` → `script-checked` | Actual command result |
| `tools/check-activation-ux.ps1`, `check-goal-led-ux.ps1`, `check-product-ux-regressions.ps1` | Source-text token checks, not model-output tests | `adapt` | Static coverage checks plus separate behavior evals | Script checks structure only | Never report behavior pass from token presence |
| `tools/check-paf-enforcement.ps1` | Matrix/reference consistency; calculates hook eligibility | `adapt` | Coverage validation in `quick_validate.py` | Static `script-checked`; runtime `host-required` | Separate `static_contract` from `behavior_eval` result |
| `tools/check-language.ps1` | Forces Cyrillic across source docs | `drop-with-reason` | `SKILL.md` rule to match user language | `skill-instruction` | Russian activation evals; no repo-wide Cyrillic gate |
| `tools/check-memory-*.ps1`, `setup-local-workspace.ps1` | Local memory validation and installation | `host-owned` | None inside the skill | `not-supported-standalone` | No-memory-write eval |
| `tools/{start,write,close}-trace.ps1`, `run-workflow.ps1`, `check-trace-coverage.ps1` | Local trace lifecycle and runner | `host-owned` | Embedded host contract only | `host-required` | Current host receipt |
| `tools/redact-trace-event.ps1`, `check-redaction-fixtures.ps1` | Regex redactor with limited pattern coverage | `drop-with-reason` | Conservative publication scan in `quick_validate.py` | `deterministic-script` | Scan tracked and untracked target candidates |
| `tools/check-live-validation-readiness.ps1` | Checks status-document tokens; does not execute a live eval | `drop-with-reason` | `docs/release-checklist.md` with actual-result placeholders | `host-required` | Exact host eval receipt |
| `tools/run-smoke.ps1` | Windows smoke orchestration; writes generated self-test traces | `adapt` | `python scripts/quick_validate.py` | `deterministic-script` | Cross-platform exit code |
| `tools/safe-local-commit.ps1`, `tools/prune-traces.ps1` | Commit gate and local trace retention | `host-owned` | Release checklist only | Host-owned | Git/CI evidence; no skill-side commit or deletion |
| `observability/*-schema.md`, `trace-policy.md`, `redaction-policy.md` | Evidence vocabulary, provenance, safe refs, privacy boundaries | `adapt` | `references/enforcement-boundary.md`; embedded return contract | Instruction plus host enforcement | Privacy/evidence-status evals |
| `observability/retention-policy.md`, `weekly-review-schema.md` | Local trace retention and recurring review | `host-owned` | None in standalone core | `not-supported-standalone` | Host policy if embedded |
| `observability/examples/*` | Synthetic trace/report examples | `drop-with-reason` | Small non-sensitive eval fixtures only if needed | Eval only | Publication scan |
| `automation/*` | Dry-run weekly review and approval template | `host-owned` | None | `not-supported-standalone` | Negative scheduler/external-effect case |
| `migration/inventory.yaml` | Historical legacy `cpo` → Copilot migration | `adapt` | This `docs/migration-map.md` | `deterministic-script` | Validator requires coverage of every source family |
| `traces/local/*`, `traces/state/*`, `traces/reports/*` | Generated local events, state, decisions, hook self-test | `drop-with-reason` | No target trace directory | `host-required`; unavailable standalone | Validator rejects private/runtime trace payloads |
| `.codex/hooks.json`, `.codex/hooks/*` | Codex workspace lifecycle hooks | `host-owned` | `references/robin-embedded-mode.md` only | `host-required` | Live host dispatch proof |
| `README.md`, `docs/install.md`, `CHANGELOG.md` | Windows root-workspace packaging and history | `drop-with-reason` then rewrite target docs | Target `README.md`; release checklist | Documentation | Link and usage checks |
| `docs/live-validation.md`, `docs/paf-enforcement-proof.md` | Source host-validation status and proof explanation | `adapt` without copying status | Enforcement reference; release checklist | Host/human | Fresh target evidence only |
| `memory/atomize.md`, `memory/index.md`, `memory/decisions/*` | Project memory tooling and root-workspace ADR history | `drop-with-reason` | Relevant boundary restated in embedded reference | `not-supported-standalone` | Publication scan |

## Source gaps that must not be inherited

1. Source behavior evals are declarative; there is no repo-local model runner.
2. Static UX checks validate strings in files, not observable model behavior.
3. Source hook evidence is `runner_only` with live dispatch unverified.
4. The source onboarding eval expects a passport for a new idea even though the
   newer goal-first rule forbids a passport as the first artifact unless asked.
5. Activation negative cases, Robin embedded cases, and publication/privacy
   behavior cases are absent.
6. `ROUTING.yaml` and `memory/MANIFEST.yaml` disagree on several `load_when`
   combinations, including goal validation and passport hardening.
7. Source PAF enforcement can return structural success while final
   `pass_eligible` remains false; target reporting must keep those states
   separate.
8. Generated traces are ignored by source Git, but a filesystem copy could
   still capture them. Migration must use an allowlist, not recursive copying.

## Target boundary

The target skill owns product-decision instructions, references, templates,
static package checks, and eval definitions. It does not own Robin identity,
durable memory, connector access, permissions, external writes, schedules,
traces, retries, receipts, or publication. Those capabilities remain with the
active host and require current host evidence.
