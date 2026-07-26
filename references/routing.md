# Routing

## Task routes

| Route | Trigger | First useful output | Default asset |
|---|---|---|---|
| PAF hypothesis | Product hypothesis, experiment, or request to decide what to validate | Base, hypothesis class, upstream evidence, Hypothesis Card | `assets/hypothesis-card-template.md` |
| Longitudinal hypothesis state | Start, resume, save, hand off, recover, or append a post-release outcome | Loaded scope/tenure/revision or explicit no-state gap, then Hypothesis Card revision or outcome event + typed Nexus/evidence/claim/outcome delta + persistence handoff | `assets/hypothesis-card-template.md` plus state metadata |
| Goal framing | Measurable outcome or product direction | Goal, baseline, unknown, decision checkpoint | `assets/next-step-template.md` |
| Evidence-gap review | Recommendation requested with incomplete evidence | Prioritized evidence gaps and blocked claims | `assets/evidence-gap-template.md` |
| PAF consistency | PAF method, conflicting hypothesis claims, or experiment review | Hypothesis class, upstream dependencies, validation and decision rules | `assets/paf-consistency-template.md` |
| Product passport | Explicit passport request or stable context needs consolidation | Compact passport with evidence states | `assets/product-passport-template.md` |
| Decision review | Feature, hypothesis, artifact, or CPO/founder argument | Decision, evidence ledger, risks, next step | `assets/decision-review-template.md` |
| Disputed claim | PMF, PCF, impact, success, readiness, need, or metric uplift claim | Compact claim review | `assets/decision-review-template.md` |

When a request fits several routes, choose the route that closes the earliest
decision-critical uncertainty. Do not produce several full artifacts.

## Activation

Implicit activation is appropriate when the request explicitly concerns a
product decision, product hypothesis, product evidence, PAF, a product
passport, disputed product claims, a next product step, longitudinal hypothesis
work, or founder/CPO product argumentation.

Positive examples include:

- "Проверь продуктовую гипотезу."
- "Есть ли здесь PMF/PCF evidence?"
- "Сделай product passport."
- "Какой следующий продуктовый шаг?"
- "Продолжи гипотезу из принятой workspace revision и Nexus snapshot."
- "Обнови post-release outcome закрытой гипотезы."
- "Проверь claims в artifact."

Do not activate, or explicitly narrow scope, for ordinary coding, a request to
become the user's root agent, hidden durable personal memory, an unapproved
write, pure visual production, or financial, legal, and medical advice. An
explicitly authorized host-owned hypothesis state root is in scope; it does not
become personal memory owned by the skill.

Treat Nexus as domain content, not the host store. A continuation claim requires
both loaded state and a matching accepted persistence receipt; chat history is
not a substitute.

## Source route

Before asking for data, return:

- sources already present in task context;
- host-accessible sources that could own the needed facts;
- evidence still required from the user;
- sources unavailable in the current runtime;
- privacy and read/write boundaries.

Do not infer successful source access from the existence of a connector or from a
tool-call attempt. The host must provide successful read evidence.

## Out-of-scope response

State the boundary in one sentence. If a product-decision subproblem exists,
offer only that scoped review. Do not assume root-agent identity, store memory,
perform effects, or provide regulated professional advice.
