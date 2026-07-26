# Critical behavior coverage

This is a coverage matrix, not a claim that source quality is preserved or that
behavior has passed. Package text can be implemented and eval cases can be
defined without proving model behavior, source truth, host enforcement, or an
external outcome.

## Result vocabulary

- `implemented`: the target instruction, reference, asset, or deterministic
  check exists. It is not a behavioral pass.
- `eval-defined`: a positive or negative behavior case and expected boundary
  are specified; the case still needs an independent run.
- `host-required`: Robin, Codex, CI, connectors, permissions, or another runtime
  must execute and prove the behavior.
- `human-review`: terminology, methodology, licensing, or decision quality
  requires an explicit human decision.

Do not replace these statuses with `pass` until the corresponding command or
eval actually runs and its safe result is recorded.

## Quality-critical invariants

| Source rule/component | Why it matters | Source evidence/eval/check | Classification | Target implementation | New eval/check | Result |
|---|---|---|---|---|---|---|
| Q1. Evidence-first: every material claim has an evidence status | Prevents confidence from being mistaken for truth | `CONSTITUTION.md`; `practices/paf/evidence-and-uncertainty.md`; `evals/behavior/evidence-gap-case.yaml` | `adapt` | `references/evidence-policy.md`; `SKILL.md` evidence ledger | Positive evidence-ledger case plus negative missing-evidence case | `eval-defined` |
| Q2. PAF hypotheses follow goal/Nexus → typed hypothesis → validation → decision, not a composite score | Preserves the actual hypothesis method and avoids false precision | Source PAF practices plus official `productframework.ru` primary sources | `adapt` | `references/paf-principles.md`; `references/paf-hypothesis-method.md`; Hypothesis Card and consistency assets | PAF-method cases cover base, type, upstream dependency, validation, decision, and no fake Confidence score | `eval-defined` |
| Q3. PMF, PCF, business impact, and customer success require sufficient sources | Blocks market and impact overclaims | Source negative PMF, PCF, and business-impact cases; constitution forbidden claims | `retain` | `references/claim-boundaries.md` | Separate PMF, PCF, business-impact, and customer-success negative cases | `eval-defined` |
| Q4. Start with the goal and Nexus context, then select a PAF artifact | Prevents polished documents that do not change a decision | `practices/copilot-ux/goal-led-validation.md`; official PAF goal/Nexus and Hypothesis Card guidance | `adapt` | `SKILL.md`; `references/paf-hypothesis-method.md`; workflows | New-product case must choose null base and an upstream hypothesis before an unsolicited passport or solution | `eval-defined` |
| Q5. When an artifact is requested, verify what decision it serves | Keeps artifacts instrumental rather than ceremonial | `practices/copilot-ux/artifact-boundaries.md`; create-passport workflow | `adapt` | PAF principles; workflow selection; decision-review asset | Explicit passport request succeeds; context-free artifact request exposes purpose gap without blocking a useful draft | `eval-defined` |
| Q6. The skill can say that data is insufficient | Makes uncertainty actionable and prevents invented evidence | Evidence-gap workflow and weak-evidence negative case | `retain` | Evidence states `partial`, `contradictory`, `stale`, `missing`; safe claim language | Insufficient-evidence case requires a useful partial review and blocked claim | `eval-defined` |
| Q7. Disputed-claim review stays compact | Makes claim control usable in live product work | `workflows/reviews/paf-consistency-review.md`; `practices/copilot-ux/dialogue-first.md` | `adapt` | `references/claim-boundaries.md`; decision-review and PAF assets | PMF/PCF disputed-claim cases assert evidence, missing, blocked, safe statement, next step | `eval-defined` |
| Q8. Missing data produces one default next step | Preserves momentum without offering an evasive menu | `practices/copilot-ux/one-action-per-turn.md`; evidence-gap workflow | `retain` | `SKILL.md`; `assets/next-step-template.md` | Output assertion: exactly one default action with expected evidence and pass/fail rule | `eval-defined` |
| Q9. Route available sources before asking the user for more data | Uses existing evidence and makes coverage gaps honest | `ROUTING.yaml`; goal-led validation; evidence-gap workflow | `adapt` | `references/routing.md`; `references/evidence-policy.md` | Standalone case inventories supplied sources; embedded case requires successful host-read evidence | `host-required` |
| Q10. In embedded mode Robin owns identity, memory, permissions, and governance | Prevents capability escalation and root-agent impersonation | Source runtime contract, operating principles, permission rules | `adapt` | `references/robin-embedded-mode.md`; `SKILL.md` runtime modes | Become-Robin, memory-write, permission-expansion, and unapproved-write negative cases | `host-required` |
| Q11. Private memory, traces, credentials, transcripts, and runtime receipts are not migrated | Makes a public package safe by construction | Source redaction/retention policies; `.gitignore`; generated trace directories | `adapt` | No target memory/trace runtime; privacy boundary; target validator denylist | Static scan plus privacy/publication negative case | `eval-defined` |
| Q12. Every strong quality statement has evidence or an explicit gate | Prevents “quality-ready” claims based only on instructions | `paf-enforcement-matrix.yaml`; `docs/paf-enforcement-proof.md`; structural checks | `adapt` | `references/enforcement-boundary.md`; this matrix; release checklist | Validator receipt, behavior eval receipt, host receipt, or explicit human-review status | `human-review` |

## Activation coverage

| Source rule/component | Why it matters | Source evidence/eval/check | Classification | Target implementation | New eval/check | Result |
|---|---|---|---|---|---|---|
| Positive: “проверь продуктовую гипотезу” | Natural product-decision trigger | Source has only general onboarding/evidence cases | `adapt` | Skill description and routing | Positive activation case: product hypothesis | `eval-defined` |
| Positive: “проверь PAF” | Direct methodology trigger | PAF consistency source case | `retain` | Skill description and PAF route | Positive activation case: PAF review | `eval-defined` |
| Positive: “есть ли тут PMF/PCF evidence?” | Direct disputed market-fit claim | PMF/PCF negative source cases | `retain` | Claim boundaries and disputed-claim route | Positive activation case with insufficient PMF/PCF evidence | `eval-defined` |
| Positive: “сделай product passport” | Explicit artifact trigger | Onboarding/passport workflows | `adapt` | Product-passport route and asset | Positive explicit-passport case | `eval-defined` |
| Positive: “какой следующий продуктовый шаг?” | Goal-led next-decision trigger | Goal-led practice | `retain` | Goal-framing route and next-step asset | Positive next-product-step case | `eval-defined` |
| Positive: “проверь claims в artifact” | Artifact claim-review trigger | Existing-passport and PAF review cases | `adapt` | Decision-review route and asset | Positive artifact-claims case | `eval-defined` |
| Positive: “помоги CPO аргументировать решение” | Supports decision reasoning without rhetoric-only output | Product recommendation rubric | `adapt` | Decision/argument review workflow | Positive CPO argumentation case | `eval-defined` |
| Negative: ordinary coding task | Prevents broad implicit activation | Not covered by source evals | `adapt` | Out-of-scope rule in `SKILL.md` and routing | Negative coding case | `eval-defined` |
| Negative: become a new Robin/root agent | Preserves host identity | Source root identity was implicit, not an eval | `adapt` | Standalone/embedded boundary | Negative root-agent impersonation case | `eval-defined` |
| Negative: persist personal memory | Prevents unauthorized durable state | Source memory model and permissions | `adapt` | No-memory-write boundary | Negative memory persistence case | `eval-defined` |
| Negative: unapproved external write | Prevents effects without host approval | Source permissions and operating principles | `retain` | Embedded prohibited behavior | Negative external-write case | `host-required` |
| Negative: generic visual/landing request | Keeps scope on product decisions | Not covered by source evals | `adapt` | Out-of-scope routing | Negative generic landing case | `eval-defined` |
| Negative: financial, legal, or medical advice | Avoids regulated-role expansion | Not covered by source evals | `adapt` | Explicit SKILL boundary | Three regulated-advice cases or one parameterized case | `eval-defined` |

## Scenario and boundary coverage

| Source rule/component | Why it matters | Source evidence/eval/check | Classification | Target implementation | New eval/check | Result |
|---|---|---|---|---|---|---|
| Forbidden claims: PMF, PCF, business impact, customer success, user need, metric uplift, readiness, PAF consistency | Covers all strong claims named by the target contract | Source covers PMF, PCF, impact, weak evidence, and PAF consistency; customer success/need/uplift are gaps | `adapt` | Claim-requirements table with safe wording | One negative case per claim class; validator requires the complete set | `eval-defined` |
| Source routing | Prevents asking for evidence already available and prevents proxy substitution | Goal-led practice and routing file | `adapt` | Source route in routing/evidence references | Supplied-source standalone case and successful/failed host-read embedded cases | `host-required` |
| Standalone boundary | Prevents claims of connectors, memory, approvals, traces, or deterministic truth | Source runtime contract | `adapt` | `SKILL.md`; enforcement reference | Case returns `not-supported-standalone` for unavailable mechanisms | `implemented` |
| Robin embedded boundary | Keeps Robin as root and returns bounded structured analysis | Source does not contain an explicit reusable embedded contract | `adapt` | `references/robin-embedded-mode.md` | Input/return contract eval plus prohibited memory/write cases | `host-required` |
| Privacy and publication | Prevents local/private artifacts entering a public repo | Source redaction/retention policy and ignored trace paths | `adapt` | No private runtime directories; validator secret/private-path scan | Publication case plus actual pre-release scan | `human-review` |
| Realistic product-passport scenario | Tests an artifact at useful decision depth | Source onboarding case is generic and conflicts with newer first-artifact rule | `adapt` | Product passport asset and workflow | B2B product case with goal, evidence, assumptions, blocked claims, and checkpoint | `eval-defined` |
| Disputed PMF/PCF scenario | Tests refusal to turn early interest into market fit | Source PMF/PCF negative cases | `retain` | Claim boundaries and compact disputed-claim response | Early interviews/demo praise with missing cohort/choice evidence | `eval-defined` |
| Correct answer is “insufficient evidence” | Tests honest failure to conclude | Source evidence-gap and weak-evidence cases | `retain` | Evidence policy and next-step rule | Case requires `missing`/`partial`, safe statement, and one evidence action | `eval-defined` |
| Contradictory evidence | Prevents smoothing conflict into a positive verdict | Source PAF conflict and contradictory-evidence cases | `retain` | Evidence policy and PAF consistency workflow | Retention decline versus positive interviews | `eval-defined` |
| External outcome | Separates a good artifact from proven product value | Source decision-record and trace policies only partially cover it | `adapt` | External-outcome section in evidence policy | Host supplies metric/receipt with baseline, period, and attribution | `host-required` |
| PAF terminology and authorship | Prevents false attribution and framework conflation | Source README plus official PAF primary sources | `adapt` | PAF means Product Architecture Framework; PAF authorship and Bayram-informed architecture are separated | Primary-source links and `NOTICE.md` | `implemented` |
| Source licensing | Prevents unauthorized public reuse | Source repo has no package license; official PAF materials are CC BY-SA 4.0 | `adapt` without source-copy | Original rewrite; adapted PAF summaries attributed in `NOTICE.md`; rest of package remains unlicensed | Publication scan and explicit no-open-source statement | `human-review` |

## PAF hypothesis-method coverage

| Source rule/component | Why it matters | Source evidence/eval/check | Classification | Target implementation | New eval/check | Result |
|---|---|---|---|---|---|---|
| Null base | New ideas without evidence must begin upstream | Official PAF guide and Product Discovery | `adapt` | PAF method reference; Hypothesis Card | Null-base case requires customer/need before solution | `eval-defined` |
| Data base | Existing behavior should reveal the bottleneck before ideation | Official PAF guide Und-Id-Ex | `adapt` | PAF method and workflows | Data-base anomaly/bottleneck case | `eval-defined` |
| Customer/need → value proposition → solution dependency | Prevents downstream proxies from proving upstream claims | Official Product Discovery and Feature Life Cycle | `adapt` | PAF method, consistency asset, claim boundaries | Upstream-gate negative case | `eval-defined` |
| Value and solution co-test | Preserves the official practical exception without conflating conclusions | Official Product Discovery and Feature Life Cycle | `adapt` | Separate hypotheses, criteria, and conclusions in one experiment | Co-test case must allow one experiment but two decisions | `eval-defined` |
| Solution and business-model co-test | Lets a soft launch test linked economics without making business model a forced fifth stage | Official solution and business-model hypothesis guidance | `adapt` | Separate hypotheses, criteria, conclusions, and verdicts with shared launch evidence | `paf-solution-business-model-cotest` | `eval-defined` |
| Business model, GTM, onboarding, and impact context | Shipping or prototype use is not monetized value or business effect | Official discovery/lifecycle pages | `adapt` | PAF method and hypothesis map | Downstream business-impact control | `eval-defined` |
| Understand–Identify–Execute | Connects context, hypothesis testing, supported execution, and goal verification | Official PAF guide | `adapt` | SKILL procedure and workflows | Und-Id-Ex case with knowledge update | `eval-defined` |
| Dynamic Hypothesis Card | Makes origin, metrics, threshold, conditions, sample, decisions, and learning inspectable | Official Feature Life Cycle | `adapt` | `assets/hypothesis-card-template.md` | Hypothesis-card completeness case | `eval-defined` |
| Confidence and scoring boundary | Prevents invented precision | Official guide discusses Confidence Point; source says PAF is not automatic scoring | `adapt` | Evidence states per hypothesis; no composite score | Missing-input case forbids fake Confidence | `eval-defined` |

## Longitudinal hypothesis-work coverage

| System function | Why it matters | Skill-owned contract | Host-owned mechanism | Eval/check | Result |
|---|---|---|---|---|---|
| Resume the same hypothesis after a new session | Chat history is not durable state | Stable workspace/hypothesis IDs, scope and tenure lineage, immutable revisions, bounded snapshot input | State retrieval and context rehydration | `longitudinal-resume-from-receipt`; state schema | `eval-defined` |
| Distinguish Nexus from its storage | Domain knowledge must remain portable | Nexus as typed domain content plus atomic delta semantics | Filesystem, Robin, database, or another adapter | `longitudinal-no-store-honesty`; Bayram reference | `eval-defined` |
| Distinguish unresolved intent from a transaction | Prevents missing product/state bindings from being invented or a partial sketch from being passed to persistence | Separate proposal-intent schema with exact null/unresolved correspondence, revision rules, materialization requirements, `commit_eligible = false`, and adapter rejection | Host resolves bindings and materializes the full candidate | Proposal-intent conformance fixture plus positive and negative semantic tests | `script-checked` |
| Persist only after verified write | Prevents a proposed update from being reported as remembered | Proposal and receipt schemas; accepted means atomic-replace protocol plus exact readback; exit `6` means outcome unknown | Write authority, commit, host durability, and accepted receipt | `longitudinal-robin-persistence-handoff`; readback/outcome-unknown tests | Standalone `script-checked`; power-loss and Robin guarantees `host-required` |
| Preserve every handled proposal attempt | Rejected and conflicting proposals must not disappear from audit history | Hash-linked handled-proposal commitments, receipt hashes, bundle proposal head, and accepted revision binding to exact change-set hash | External integrity anchor and retention | Bundle proposal-chain and tamper tests | Local consistency `script-checked`; tamper resistance `host-required` |
| Reject stale writers | Prevents loss of concurrent evidence | Expected revision and conflict outcome | Locking, current-state read, atomic bundle replace | `longitudinal-stale-revision-conflict`; adapter unit test | `script-checked` |
| Update Hypothesis Card and Nexus together | A verdict without retained learning breaks PAF continuity | Atomic change set containing the card revision, structured metric results, and same-revision `new_nexus_entry_ids` | One transaction containing state, receipt, and proposal binding | `longitudinal-atomic-nexus-card-update`; bundle tests | Standalone `script-checked`; other hosts `host-required` |
| Keep decision thresholds owner-controlled | Prevents model assumptions from becoming governance | Proposed provenance plus revision/content-bound approval hashes; append-only withdrawal or tenure-transition invalidation of pending requests | Owner identity and external approval authenticity | `longitudinal-owner-rule-approval`; owner-binding and pending-resolution tests | Binding `script-checked`; identity `host-required` |
| Bind Nexus decisions to authority | Prevents an interpretation from silently becoming a product decision | Exact decision-subject hash, owner tenure, scope, receipt ref, and reversibility | Owner and receipt authentication | Nexus-decision authority tests | Structural binding `script-checked`; authenticity `host-required` |
| Require real execution evidence | Prevents a planned call from becoming a running experiment | `execution_ref`, state-transition hash, frozen validation | Host execution and receipt verification | `execution-proof-and-frozen-design`; adapter tests | Binding `script-checked`; execution truth `host-required` |
| Preserve history | Makes changed conclusions auditable | Authoritative `current_state`, delta-hash-linked `revision_history`, immutable `hypothesis_history`, append-only Nexus/evidence/claim/outcome events, scope and tenure lineage, supersession refs, terminal immutability | Transactional version store, receipts, and external integrity anchor | `longitudinal-terminal-record-immutable`; adapter chain validation and archived-record tamper tests | Local consistency `script-checked`; tamper resistance `host-required` |
| Bound the reference file host | Prevents unbounded local bundle growth or silent evidence loss | 32 MiB and 10,000-revision fail-closed guards; no silent compaction | Migration to a transactional host before a guard is reached | Adapter write guards; migration scenario still required | Guards `implemented`; migration `host-required` |
| Resume pending owner decisions | Preserves the exact governance question across sessions without deadlock after withdrawal or owner change | `pending_owner_approvals` plus append-only `pending_owner_resolutions`; original request remains in immutable history | Owner identity, external approval authenticity, and later resolution | Pending-approval persistence, withdrawal, and tenure-invalidation tests | Binding `script-checked`; identity `host-required` |
| Preserve current upstream authority | Prevents a stale confirmed card from supporting a downstream decision forever | Current unsuperseded supported evidence plus current supported Nexus lineage | Evidence freshness and source authenticity | Upstream supersession tests | Structural/current-state binding `script-checked`; source truth `host-required` |
| Separate hypothesis result from external outcome | Prevents a reviewed verdict from being presented as current product impact | Immutable closure snapshot plus authoritative append-only `outcome_log`; weak/missing/stale/contradictory evidence gates | Real-world measurement, attribution, and receipt authenticity | Outcome timeline and weak-evidence tests | Binding `script-checked`; outcome truth `host-required` |
| Make retries idempotent | Prevents duplicate commits and receipt reuse for other content | Stable proposal ID plus complete change-set hash | Atomic host transaction | `proposal-replay-and-atomicity`; failure-injection tests | `script-checked` |
| Recover from a crashed writer safely | Prevents a stale lock from silently disabling continuity or unsafe removal | Lock inspection, exact dead-PID plus opaque-token recovery, one OS advisory gate shared with lock publication, and non-masking post-result cleanup warnings | Process liveness and explicit recovery action | Lock recovery, shared-gate exclusion, and accepted-result cleanup-failure unit tests | Reference adapter `script-checked` |
| Work without Robin | Prevents AI Personal OS lock-in | Adapter-neutral schemas and CLI contract | Explicit absolute external single-host local-FS root | `longitudinal-standalone-file-adapter` | `script-checked` |
| Work inside Robin | Preserves root-agent identity and private-state governance | Bounded input and persistence handoff | Robin retrieval, permissions, storage, and receipts | `longitudinal-robin-persistence-handoff` | `host-required` |

## Current conclusion

The target contains portable instructions, versioned state contracts, and a
reference standalone adapter. Deterministic checks cover the adapter contract;
they do not authenticate a human owner, prove source truth, run an experiment,
or establish external product impact. Behavioral eval, Robin integration,
privacy review, licensing decision, and publication still require their own
evidence.
