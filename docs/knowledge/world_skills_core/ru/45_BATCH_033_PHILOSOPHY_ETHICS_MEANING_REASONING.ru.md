# 📜 Batch 033 — Philosophy, Ethics, Meaning & Reasoning

**Язык:** русский  
**Статус:** 50K batch 033 / seed units / не L3 truth  
**Цель:** добавить слой смысла и осторожного reasoning: эпистемология, этика, философия науки, аргументация, ценности и границы знания.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `philosophy.epistemology.knowledge` | TERM | Знание обычно связывают с истинностью, обоснованием и убеждением. | Классическое определение спорно из-за Gettier cases. | epistemology |
| `philosophy.epistemology.belief` | TERM | Убеждение — принятие утверждения как верного. | Может быть истинным или ложным. | cognition |
| `philosophy.epistemology.justification` | TERM | Обоснование объясняет, почему убеждению стоит доверять. | Разные школы понимают иначе. | evidence |
| `philosophy.epistemology.gettier` | PROBLEM | Gettier cases показывают, что justified true belief может не быть знанием. | Философский problem, не простой тест. | epistemology |
| `philosophy.epistemology.fallibilism` | POSITION | Fallibilism признаёт, что даже обоснованное знание может быть ошибочным. | Не равно релятивизму. | science |
| `philosophy.epistemology.skepticism` | POSITION | Скептицизм сомневается в возможности или границах знания. | Бывает методологическим или радикальным. | philosophy |
| `philosophy.epistemology.empiricism` | POSITION | Empiricism подчёркивает опыт и наблюдение как источник знания. | Не исключает роль теории. | science |
| `philosophy.epistemology.rationalism` | POSITION | Rationalism подчёркивает разум, структуры и априорные принципы. | В чистом виде спорен. | philosophy |
| `philosophy.science.falsifiability` | PRINCIPLE | Фальсифицируемость требует, чтобы claim мог быть опровергнут возможным наблюдением. | Не все научные практики сводятся к одному критерию. | science |
| `philosophy.science.paradigm` | MODEL | Paradigm задаёт общие понятия, методы и стандарты науки в эпоху. | Термин связан с Kuhn and debate. | history |
| `philosophy.science.normal_science` | MODEL | Normal science решает задачи внутри принятой парадигмы. | Не обязательно некреативна. | science |
| `philosophy.science.paradigm_shift` | PROCESS | Paradigm shift меняет базовую рамку объяснения. | Не любое открытие — shift. | history |
| `philosophy.science.reductionism` | POSITION | Reductionism объясняет сложное через более простые уровни. | Может терять emergent properties. | systems |
| `philosophy.science.holism` | POSITION | Holism подчёркивает свойства целого и контекст. | Может быть расплывчатым без механизма. | systems |
| `philosophy.science.instrumentalism` | POSITION | Instrumentalism ценит теории как инструменты предсказания. | Не отвечает прямо, "реальны" ли сущности теории. | science |
| `philosophy.science.realism` | POSITION | Scientific realism считает, что успешные теории примерно описывают реальный мир. | Спорит с anti-realism. | science |
| `philosophy.logic.deduction` | REASONING_MODE | Дедукция выводит следствие, необходимое из посылок. | Истинность вывода зависит от истинности посылок. | logic |
| `philosophy.logic.induction` | REASONING_MODE | Индукция обобщает из случаев к правилу. | Даёт вероятностную поддержку. | logic |
| `philosophy.logic.abduction` | REASONING_MODE | Abduction ищет лучшее объяснение наблюдения. | Может выбрать красивую, но ложную гипотезу. | reasoning |
| `philosophy.logic.analogy` | REASONING_MODE | Аналогия переносит структуру между доменами. | Нужно искать disanalogies. | cross_domain |
| `philosophy.logic.validity_soundness` | DISTINCTION | Validity — форма вывода; soundness — validity плюс истинные посылки. | Частая путаница в споре. | logic |
| `philosophy.logic.modal` | LOGIC_TYPE | Modal logic работает с возможностью и необходимостью. | Семантики различаются. | logic |
| `philosophy.logic.deontic` | LOGIC_TYPE | Deontic logic формализует обязанность, разрешение и запрет. | Нормативные парадоксы сложны. | ethics |
| `philosophy.logic.paraconsistent` | LOGIC_TYPE | Paraconsistent logic допускает противоречия без взрыва всей системы. | Полезна для конфликтных баз знания. | knowledge_graph |
| `philosophy.ethics.consequentialism` | POSITION | Consequentialism оценивает действие по последствиям. | Сложно считать все последствия. | ethics |
| `philosophy.ethics.deontology` | POSITION | Deontology оценивает действие по обязанностям и правилам. | Может конфликтовать с outcomes. | ethics |
| `philosophy.ethics.virtue` | POSITION | Virtue ethics фокусируется на качествах характера и практической мудрости. | Менее процедурна. | ethics |
| `philosophy.ethics.care` | POSITION | Ethics of care подчёркивает отношения, зависимость и заботу. | Важно для медицины и семейных решений. | ethics |
| `philosophy.ethics.principlism` | MODEL | Principlism использует autonomy, beneficence, non-maleficence, justice. | Принципы могут конфликтовать. | bioethics |
| `philosophy.ethics.autonomy` | PRINCIPLE | Автономия уважает способность человека принимать решения о себе. | Требует информации и отсутствия принуждения. | rights |
| `philosophy.ethics.nonmaleficence` | PRINCIPLE | Non-maleficence требует не причинять вред. | Иногда вред и польза конфликтуют. | safety |
| `philosophy.ethics.beneficence` | PRINCIPLE | Beneficence требует стремиться к благу другого. | Нельзя оправдывать paternalism без границ. | care |
| `philosophy.ethics.justice` | PRINCIPLE | Justice требует справедливого распределения благ, рисков и прав. | Теории справедливости спорят. | society |
| `philosophy.political.social_contract` | MODEL | Social contract объясняет власть как соглашение ради порядка и защиты. | Исторически не буквальный контракт. | politics |
| `philosophy.political.liberty` | VALUE | Свобода может пониматься как отсутствие вмешательства или способность действовать. | Negative/positive liberty различаются. | rights |
| `philosophy.political.equality` | VALUE | Equality может значить равные права, возможности или результаты. | Разные смыслы конфликтуют. | politics |
| `philosophy.political.legitimacy` | TERM | Legitimacy — признание власти оправданной. | Не равна одной legal validity. | governance |
| `philosophy.mind.consciousness` | PROBLEM | Consciousness — проблема субъективного опыта и его связи с мозгом. | Нельзя честно обещать "сознательный AI". | mind |
| `philosophy.mind.intentionality` | TERM | Intentionality — направленность мыслей на объекты или содержание. | Не то же, что намерение в быту. | mind |
| `philosophy.mind.embodiment` | POSITION | Embodiment подчёркивает роль тела и действия в мышлении. | Не отменяет абстрактное мышление. | cognition |
| `philosophy.language.meaning_use` | POSITION | Meaning as use связывает значение слова с практикой употребления. | Не единственная теория значения. | language |
| `philosophy.language.reference` | TERM | Reference связывает выражение с объектом или классом объектов. | Имена, описания и контекст сложны. | semantics |
| `philosophy.language.speech_act` | MODEL | Speech act рассматривает высказывания как действия: обещание, приказ, вопрос. | Смысл зависит от ситуации. | communication |
| `philosophy.aesthetics.beauty` | PROBLEM | Beauty может пониматься как свойство, опыт, культурная норма или отношение. | Не сводить к одному вкусу. | art |
| `philosophy.aesthetics.sublime` | CONCEPT | Sublime связано с переживанием величия, опасности или бесконечности. | Исторический термин эстетики. | art |
| `philosophy.technology.instrumental_view` | POSITION | Инструментальный взгляд считает технологию нейтральным средством. | Критика: инструменты меняют поведение и общество. | technology |
| `philosophy.technology.affordance` | CONCEPT | Affordance показывает, какие действия вещь делает возможными или очевидными. | Зависит от пользователя и контекста. | design |
| `philosophy.technology.technological_mediation` | MODEL | Технологии посредничают восприятие, действие и социальные отношения. | Важно для AI and interfaces. | STS |
| `philosophy.ai.alignment` | PROBLEM | AI alignment пытается согласовать поведение AI с человеческими целями и нормами. | Цели людей конфликтуют. | AI_safety |
| `philosophy.ai.explainability` | PRINCIPLE | Explainability требует понятного пути от входа к выводу. | Объяснение может быть post-hoc и неверным. | AI |
| `philosophy.ai.accountability` | PRINCIPLE | Accountability спрашивает, кто отвечает за AI decision and harm. | Нужны роли, logs, governance. | law |
| `philosophy.ai.personification_risk` | RISK | Персонификация AI может создавать ложное доверие и зависимость. | Интерфейс должен быть честным. | ethics |
| `philosophy.meaning.purpose` | CONCEPT | Purpose связывает действие с желаемым направлением и ценностью. | Может быть личным, социальным, институциональным. | meaning |
| `philosophy.meaning.narrative_identity` | MODEL | Narrative identity связывает жизнь человека через истории о себе. | История может исцелять или ограничивать. | psychology |
| `philosophy.meaning.absurd` | CONCEPT | Absurd describes conflict between search for meaning and indifferent world. | Разные философы отвечают по-разному. | existential |
| `philosophy.practical_wisdom` | CONCEPT | Practical wisdom — умение применять правила к конкретной ситуации. | Не заменяется списком норм. | ethics |
| `philosophy.argument.steelman` | METHOD | Steelman усиливает позицию оппонента перед критикой. | Помогает честному спору. | communication |
| `philosophy.argument.charity` | PRINCIPLE | Principle of charity интерпретирует аргумент в разумной сильной форме. | Не означает игнорировать ошибки. | reasoning |
| `philosophy.argument.burden_of_proof` | PRINCIPLE | Тот, кто делает claim, обычно несёт burden of proof. | Зависит от контекста. | logic |
| `philosophy.argument.defeater` | TERM | Defeater — информация, ослабляющая или отменяющая обоснование. | Важно для non-monotonic reasoning. | epistemology |
| `philosophy.knowledge.negative` | CONCEPT | Negative knowledge хранит, что не работает и почему. | Особенно ценно для инженерии и науки. | world_knowledge |
| `philosophy.knowledge.uncertainty_honesty` | PRINCIPLE | Честная система сообщает неопределённость, а не имитирует уверенность. | Центрально для Velantrim. | truth_gate |

---

## 📊 Batch 033 summary

```text
new units: 62
main layers:
  epistemology and philosophy of science
  logic and argumentation
  ethics, politics and meaning
  AI ethics and practical wisdom
```
