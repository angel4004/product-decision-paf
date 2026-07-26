# Онбординг в `product-decision-paf`

## Короткий ответ про память

У skill нет собственной приватной долгосрочной памяти — и это намеренное
архитектурное решение.

При этом долгосрочная работа с гипотезами возможна. Skill поставляет:

- PAF-метод и правила переходов;
- переносимую модель Nexus и Hypothesis Card;
- versioned state schemas;
- двухфазный proposal-intent → атомарный change-set protocol;
- требования к approvals и receipts;
- проверяемый локальный file adapter.

Фактическое состояние хранит **host**: Robin, локальный файловый host или другая
система, реализующая тот же контракт. Поэтому правильная формула такая:

```text
skill = метод + формат состояния + правила изменения
host = хранение + retrieval + права + фактическая запись
```

Без host, сохранённого state и `accepted` receipt skill может подготовить
checkpoint, но следующая сессия не обязана его помнить.

## Что такое Nexus

Nexus — это не «папка памяти» и не конкретная база данных. Это предметная модель
накопленного знания о продукте, пользователях, рынке и бизнесе, нужного для
решений.

В переносимом state Nexus представлен `nexus_entries`. Каждая запись — это:

- `fact`, `interpretation`, `decision` или `unknown`;
- формулировка;
- evidence IDs и статус доказательности;
- момент актуальности;
- ссылки на записи, которые она заменяет.

Физически один и тот же Nexus может жить в локальном JSON bundle, памяти Robin
или транзакционной базе. Содержание и правила остаются одинаковыми; меняется
только host adapter.

## Как выглядит долгосрочный цикл

```text
цель в активном decision scope
  → актуальный Nexus и evidence
  → самая ранняя критическая PAF-гипотеза
  → owner-approved test contract
  → выполнение и metric_results
  → verdict и новое Nexus-знание
  → proposal intent, если обязательные bindings ещё неизвестны
  → materialization после заполнения bindings
  → атомарный change set
  → host commit + exact readback
  → accepted receipt
  → следующая сессия загружает новую revision
```

Именно повторяемый цикл `load → reason → propose → commit → receipt → reload`,
а не chat history, создаёт долгосрочную непрерывность.

## Кто за что отвечает

| Участник | Ответственность |
|---|---|
| Илья | Цель, приоритет, критерии, допустимый риск, смена decision scope, owner approvals и terminal verdict |
| Skill | PAF-классификация, upstream gates, Hypothesis Card, Nexus/evidence/claim semantics, proposal intent или полный change set и один следующий шаг |
| Host | Retrieval, источники, права, owner identity, запись, receipts, retention, backups и внешние эффекты |
| Adapter | Schema/semantic checks, revisions, concurrency, atomic commit и readback |

Skill не становится Robin и не получает скрытого права писать в его память.
Robin не должен менять PAF-семантику при сохранении.

## Что хранится в workspace

Один workspace относится к продукту и сохраняет непрерывный Nexus через
несколько последовательных решений. В нём есть:

- `decision_scope_log` — история ограниченных целей и решений;
- `owner_tenure_log` — история владельцев решения;
- `nexus_entries` — предметное знание;
- `evidence_log` — наблюдения и источники;
- `claim_log` — история блокировки и разрешения сильных claims;
- `outcome_log` — authoritative post-release timeline после закрытия карточек;
- versioned hypotheses;
- focus hypothesis;
- revision-chain head и последний receipt ref.

Текущие `goal` и `decision_owner_ref` не переписываются произвольно. Они всегда
совпадают с последними элементами соответствующих append-only журналов.

### Смена цели

Когда заканчивается один ограниченный decision и начинается другой, добавляется
новая запись в `decision_scope_log`. Она указывает предыдущий scope, причину,
workspace revision и safe receipt перехода.

Каждая гипотеза навсегда связана со своим `decision_scope_id`. Перед открытием
нового scope активные гипотезы предыдущего должны стать terminal по
соответствующим approval rules. Nexus и evidence при этом не теряются и не
переносятся в новый разрозненный workspace.

### Смена владельца

Смена decision owner добавляет запись в `owner_tenure_log`. Старые approvals
остаются частью истории, но не дают полномочий новому владельцу. Активный test
contract должен получить approval, связанный с новым
`active_owner_tenure_id`.

Так система сохраняет знания продукта, но не переносит человеческие полномочия
молча.

Незавершённый запрос approval не должен навсегда блокировать работу. Он может
закрыться matching approval либо append-only записью в
`pending_owner_resolutions`:

- `withdrawn` — active owner явно снял запрос;
- `invalidated_by_tenure_transition` — одна candidate revision одновременно
  добавила новый tenure и resolution, который сделал запрос предыдущего tenure
  неактуальным.

Исходный запрос остаётся в immutable history, а resolution связывает его
tenure, subject revision/hash, активную authority, reason и safe receipt.

## Четыре класса PAF-гипотез

Skill использует ровно четыре класса:

1. `customer_need` — существует ли нужда у выбранного сегмента;
2. `value_proposition` — создаёт ли ценность значимый выбор или результат;
3. `solution` — позволяет ли реализация получить этот результат;
4. `business_model` — жизнеспособна ли продуктово-бизнесовая конфигурация.

Acquisition, activation, onboarding, go-to-market, adoption и post-release
impact — это `lifecycle_context`, а не дополнительные PAF-классы.

Базовая зависимость:

```text
customer_need → value_proposition → solution
```

`business_model` — связанная системная гипотеза, а не обязательная «пятая
ступень».

### Co-test

Один experiment может быть общим только для допустимых пар:

- `value_proposition` + `solution`;
- `solution` + `business_model`.

В dependency это явно фиксируется как `mode = co_test` и
`co_test_plan_ref`. У каждой гипотезы остаются собственные:

- ID и statement;
- owner-approved test contract;
- metrics и `metric_results`;
- interpretation и verdict.

Peers должны быть готовы совместно, а после запуска ссылаться на один
`execution_ref`. После общего запуска одна peer-гипотеза может закрыться, пока
другая остаётся `ready_for_review`. Общий experiment не превращает две
гипотезы в один вывод.

Supported upstream — не вечный сертификат. Он должен ссылаться на актуальное,
не superseded supported evidence и текущую supported Nexus lineage. Старый
`closed/confirmed` verdict сам по себе недостаточен, если его evidence или
Nexus learning позже потеряли актуальность.

## Жизненный цикл Hypothesis Card

```text
framing
  → blocked_upstream | awaiting_owner_rule | ready_to_run
  → running
  → ready_for_review
  → closed
```

Также возможны terminal-состояния `cancelled` и `superseded`.

Главные gates:

- `blocked_upstream` допустим только при реальном unresolved dependency;
- `awaiting_owner_rule` хранит точный запрос approval, но не разрешает запуск;
- при `ready_to_run` замораживается утверждённый test contract;
- `running` требует host-supplied `execution_ref` и отдельный
  `state_transition` approval, связанный с candidate revision и этим exact
  execution ref; skill может вернуть такой candidate как `proposed`, но не
  заявить, что переход уже принят;
- `ready_for_review` требует evidence и структурированных результатов;
- `closed` требует reviewed validity, terminal approval и owner acceptance;
- terminal-карточка не редактируется; новая формулировка получает новый ID и
  может указывать в `replaces_hypothesis_id` закрытую или superseded
  историческую карточку.

## Evidence, claims и Nexus learning

`evidence_log`, `nexus_entries`, `claim_log` и `outcome_log` append-only.
Исправление не переписывает старую запись, а добавляет новую с
`supersedes_*`.

Сильный claim начинается с события `blocked` в `claim_log` и списка нужного
evidence. Позже новое событие для того же `claim_id` может разрешить его как:

- `supported` — только на supported evidence;
- `withdrawn` — на contradictory evidence.

Список активных заблокированных claims вычисляется по последнему событию каждого
claim. Отдельного изменяемого поля для этого списка нет.

Новое знание после проверки становится обычными typed Nexus entries. Поле
`result.new_nexus_entry_ids` должно ссылаться на записи, добавленные в той же
workspace revision. Так skill не создаёт второй, неструктурированный журнал
«выводов».

Nexus entry с `kind = decision` требует `decision_authority`: exact canonical
subject hash, owner и owner tenure, decision scope, time, safe receipt и
`reversible/irreversible`. Новое решение обязано использовать active scope и
tenure и иметь supported status. Host подтверждает личность и receipt; adapter
проверяет структуру и точный hash.

## Как фиксируется результат

Для каждой primary metric в `ready_for_review` и `closed` обязателен элемент
`metric_results`:

- metric ID;
- evidence IDs и observation period;
- observed summary;
- actual numerator и denominator;
- actual sample size;
- `criterion_evaluation`;
- validity.

Числовые измерения numerator/denominator передаются canonical decimal strings,
а не JSON floats.

`confirmed` требует supported evidence, adequate validity и `met` для всех
primary criteria. `disconfirmed` требует хотя бы один `not_met`, отсутствие
`indeterminate` у primary metrics и те же evidence/validity gates. Invalid
result может быть закрыт только как `unresolved`.

Реальный внешний эффект — отдельная проверка. `verified` outcome требует
supported outcome evidence и host receipt. Поэтому `closed/confirmed` не равно
«бизнес-эффект доказан».

External-outcome поля карточки — immutable snapshot на момент её закрытия. Для
`observed` или `attribution_limited` допустимы только supported/partial
evidence; для `verified` — только supported evidence и host receipt.
Missing/stale/contradictory evidence не может обосновать положительный snapshot.

Все последующие изменения эффекта записываются в `outcome_log`, а не в
terminal-карточку:

- `observed` — supported evidence;
- `attribution_limited` — supported/partial evidence плюс attribution note;
- `verified` — supported evidence плюс host receipt;
- `withdrawn` — contradictory evidence.

Каждое новое событие supersedes последнее событие той же гипотезы. Последний
outcome должен ссылаться на current unsuperseded usable evidence.

## Первый цикл

Начните с одного решения, а не со всего backlog:

```text
$product-decision-paf

Начни долгосрочный цикл работы с гипотезами.

Продукт:
[safe product ref]

Цель и решение:
[какое изменение нужно получить и что будет решено]

Что известно:
[safe summaries и evidence refs]

Ограничения:
[сегмент, срок, риск, бюджет]

Определи null_base или data_base. Найди самую раннюю критическую
PAF-гипотезу. Не придумывай thresholds. Подготовь одну Hypothesis Card,
typed Nexus/claim delta и один следующий шаг. Если всех bindings хватает,
подготовь полный atomic change set; иначе верни non-committable proposal intent
с полным списком unresolved bindings.
Не заявляй сохранение без accepted receipt.
```

Если host явно сообщает, что workspace ещё не существует и все обязательные
bindings известны, skill в текущем ответе возвращает полный create change set:
`expected_workspace_revision = null`, workspace revision `0` и stable
hypothesis revision `0`. При доступном host adapter этот candidate имеет status
`proposed`; если отсутствует только adapter или write authority, тот же полный
change set возвращается с `not_persisted`.

Если неизвестен product, scope, owner, state или другой обязательный binding,
полный change set построить честно нельзя. Тогда skill возвращает отдельный
schema-valid `proposal_intent`: известные значения, полный список пробелов,
materialization contract, `commit_eligible: false` и `not_persisted`. Это
переносимый checkpoint намерения, но не сохранённое состояние и не вход для
`commit`. После заполнения bindings создаётся новый полный change set с
собственным ID и hash. Skill не выбирает скрытый storage path и не называет
неполный sketch транзакцией.

До запуска Илья должен понимать:

- какое решение изменит результат;
- что является primary evidence;
- кто утверждает критерии, sample и time window;
- что происходит при confirmation, disconfirmation и unresolved.

## Продолжение в новой сессии

Host передаёт:

- workspace ID и revision;
- active decision scope и owner tenure;
- bounded Nexus, evidence, claim и outcome events;
- актуальную revision нужной Hypothesis Card;
- последний matching accepted receipt;
- текущие permissions и approvals.

Пример:

```text
$product-decision-paf

Продолжи hypothesis-007 из переданного state_context.
Сначала проверь workspace revision, card revision, active decision scope,
owner tenure и accepted receipt. Учти новое evidence. Верни новую immutable
card revision, metric_results, new_nexus_entry_ids и atomic change set.
Не заявляй сохранение до ответа adapter.
```

При stale revision правильный результат — `conflict`, reload и повторная
оценка. Blind overwrite запрещён.

## Standalone: локальный файловый host

File adapter позволяет работать долгосрочно без AI Personal OS, но только когда
пользователь явно выбирает storage.

Требования:

- абсолютный state root;
- root вне package/repository skill;
- single-host local filesystem; Windows UNC root не поддерживается;
- только safe summaries и refs;
- явный `commit` для конкретного change set.

Команды:

```text
python scripts/hypothesis_state.py validate-intent --intent <proposal-intent.json>
python scripts/hypothesis_state.py load --root <absolute-state-root>
python scripts/hypothesis_state.py commit --root <absolute-state-root> --change-set <change-set.json>
python scripts/hypothesis_state.py verify --root <absolute-state-root>
python scripts/hypothesis_state.py inspect-lock --root <absolute-state-root>
python scripts/hypothesis_state.py recover-lock --root <absolute-state-root> --expected-pid <dead-pid> --expected-token <lock-token>
```

В root находится один `hypothesis-state-bundle.json`:

- `current_state`;
- hash-linked `revision_history`;
- immutable `hypothesis_history`;
- receipts;
- handled proposal commitments и `proposal_history_head_sha256`.

Adapter ограничен 32 MiB и 10 000 accepted revisions. Он не делает silent
compaction и не удаляет историю. До лимита состояние нужно перенести в
транзакционный host.

### Receipt и readback

`accepted` означает, что adapter:

1. проверил schema и semantic invariants;
2. выполнил atomic-replace protocol;
3. прочитал bundle обратно;
4. сравнил точное canonical содержание;
5. связал receipt с change-set hash и новой revision.

Receipt честно указывает:

`durability_scope = atomic_replace_with_readback_power_loss_host_dependent`.

То есть exact readback доказан, но устойчивость при внезапном обесточивании,
backup и свойства storage stack остаются ответственностью host.

Exit code `6` и `OUTCOME UNKNOWN` означают: replace мог произойти, но финальная
проверка результата не завершилась. Это не обычный `failed`. Нельзя сразу
отправлять изменённый proposal. Сначала выполните `verify` и `load`, при
необходимости восстановите только неизменившийся stale lock, затем повторите
точно тот же change set. Idempotent replay вернёт сохранённый receipt, если
первая попытка была обработана, либо выполнит этот единственный commit.

### Lock recovery

`inspect-lock` возвращает PID, состояние процесса и непрозрачный lock token.
`recover-lock` требует одновременно точный мёртвый PID и точный token. Если
lock изменился, malformed или owner жив/неизвестен, recovery прекращается.
Удаляются только файлы, принадлежащие этому lock. Публикация нового lock и
recovery используют общий короткий OS advisory gate: новый commit не может
вставить другой lock между повторной проверкой stale lock и его удалением.

Если после уже известного результата не удалось удалить собственный lock,
adapter пишет в stderr безопасное предупреждение
`warning = lock_cleanup_required` с непрозрачным `lock_id`. Это не отменяет
уже выданный `accepted`, `rejected` или `conflict` и не меняет его exit code.
Сначала выполните `inspect-lock`; `recover-lock` допустим только после
подтверждения, что точный PID владельца мёртв. В отличие от этого, exit code
`6` означает неизвестность самого результата записи.

## Embedded: Robin

В embedded mode Robin:

1. загружает разрешённый bounded state и source evidence;
2. передаёт skill текущие scope, tenure, revisions и receipts;
3. получает reasoning и либо proposal intent, либо полный change set;
4. для intent сначала заполняет отсутствующие bindings;
5. запрашивает approval Ильи для полного candidate;
6. сохраняет полный change set через свой adapter;
7. возвращает receipt;
8. при следующем вызове снова передаёт accepted state.

Skill не пишет память Robin напрямую, не расширяет permissions, не вызывает
connectors по собственной инициативе и не становится root agent.

После закрытия гипотезы Robin передаёт её result только как closure snapshot.
Новый факт об эффекте оформляется отдельным `outcome_log` event с актуальным
evidence, а не изменением terminal-карточки.

## Как читать persistence status

| Статус | Значение |
|---|---|
| `proposed` | Skill подготовил change set; записи ещё нет |
| `not_persisted` | Записи нет: отсутствует host/write authority либо обязательные bindings ещё представлены только в non-committable proposal intent |
| `accepted` | Exact change set записан и прочитан обратно; power-loss guarantee зависит от host |
| `rejected` | Proposal нарушил schema, semantic, approval или privacy gate |
| `conflict` | Snapshot устарел; нужен reload |
| `failed` | Запись определённо не подтверждена как принятая |
| `outcome_unknown` | Replace мог состояться; verify/load, при необходимости exact lock recovery, затем replay только неизменённого change set |

Слова «сохранено» и «помнит» допустимы только после matching `accepted`
receipt.

## Что защищают hashes

Каждая accepted revision связывает previous revision hash, previous state hash,
exact `change_set_sha256`, delta hash, manifest, summary и receipt. Delta
включает изменённые карточки и новые scope, tenure, Nexus, evidence, claim и
outcome events. Current state хранит revision-chain head.

Отдельная proposal-attempt chain связывает все handled `accepted`, `rejected` и
`conflict` receipts. Каждый элемент содержит sequence, previous proposal hash,
change-set ID/hash и receipt ID/hash. Bundle хранит
`proposal_history_head_sha256`. Поэтому отклонённые и конфликтные попытки тоже
остаются проверяемой историей.

Это обнаруживает внутренние несоответствия и многие повреждения, включая
подмену архивной карточки. Но атакующий с правом переписать весь bundle может
пересчитать hashes. Для tamper evidence нужен внешний anchor: immutable receipt
log, подпись или независимо сохранённый head hash.

## Canonical JSON

Для переносимых hashes используется поддерживаемое подмножество RFC 8785/JCS:

- JSON не содержит duplicate keys, `NaN` или infinity;
- все strings и keys нормализованы в Unicode NFC;
- lone/unpaired Unicode surrogates запрещены;
- JSON floats запрещены;
- decimals передаются canonical strings;
- integers ограничены безопасным межплатформенным диапазоном
  `-9007199254740991..9007199254740991`;
- object keys сортируются по UTF-16 code units;
- hashing использует compact UTF-8 JSON без trailing LF.

Pretty-printed bundle удобен человеку, но hashes всегда считаются по canonical
representation; финальный newline файла в hash не входит.

## Еженедельная привычка

Для одного активного продукта:

1. проверить active decision scope и goal;
2. проверить owner tenure;
3. обновить freshness evidence, Nexus и post-release outcomes;
4. выбрать одну focus hypothesis;
5. проверить upstream/co-test и owner rule;
6. собрать только decision-relevant evidence;
7. заполнить metric results и verdict;
8. добавить evidence-bound Nexus, claim и outcome events; для Nexus decisions
   проверить `decision_authority`;
9. получить accepted receipt;
10. назначить один следующий шаг.

Хороший недельный результат — не число экспериментов, а уменьшение
decision-critical неопределённости с сохранённой и проверяемой историей.

## Критерий успешного онбординга

Онбординг завершён, когда вы можете:

- объяснить Nexus как domain model, а не storage;
- назвать host, в котором живёт ваше состояние;
- различить decision scope и product-level Nexus;
- объяснить, почему approvals связаны с owner tenure;
- выбрать PAF-класс и допустимый co-test;
- показать evidence-bound `metric_results`, `claim_log` и
  `new_nexus_entry_ids`;
- отличить immutable closure snapshot от post-release `outcome_log`;
- объяснить, зачем отдельно нужны revision chain и proposal-attempt chain;
- получить matching accepted receipt либо честно сказать `not_persisted` или
  `outcome_unknown`;
- открыть новую сессию и продолжить ту же hypothesis по ID и revision.
