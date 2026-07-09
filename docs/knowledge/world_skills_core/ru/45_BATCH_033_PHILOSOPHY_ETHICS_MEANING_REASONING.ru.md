# 📜 Batch 033 — Philosophy, Ethics, Meaning & Reasoning

**Язык:** русский  
**Статус:** 50K batch 033 / seed units / не L3 truth  
**Цель:** добавить слой смысла и осторожного reasoning: эпистемология, этика, философия науки, аргументация, ценности и границы знания.

---

## 📦 Knowledge Units

| ID | Тип | Суть | Условия / границы | Связи |
|---|---|---|---|---|
| `philosophy.epistemology.knowledge` | СРОК | Знание обычно связывают с истинностью, обоснованием и убеждением. | Классическое определение спорно из-за Gettier cases. | эпистемология |
| `philosophy.epistemology.belief` | СРОК | Убеждение — принятие утверждения как верного. | Может быть истинным или ложным. | познание |
| `philosophy.epistemology.justification` | СРОК | Обоснование объясняет, почему убеждению стоит доверять. | Разные школы понимают иначе. | доказательство |
| `philosophy.epistemology.gettier` | ПРОБЛЕМА | Gettier cases показывают, что justified true belief может не быть знанием. | Философский problem, не простой тест. | эпистемология |
| `philosophy.epistemology.fallibilism` | ПОЗИЦИЯ | Fallibilism признаёт, что даже обоснованное знание может быть ошибочным. | Не равно релятивизму. | наука |
| `philosophy.epistemology.skepticism` | ПОЗИЦИЯ | Скептицизм сомневается в возможности или границах знания. | Бывает методологическим или радикальным. | философия |
| `philosophy.epistemology.empiricism` | ПОЗИЦИЯ | Empiricism подчёркивает опыт и наблюдение как источник знания. | Не исключает роль теории. | наука |
| `philosophy.epistemology.rationalism` | ПОЗИЦИЯ | Rationalism подчёркивает разум, структуры и априорные принципы. | В чистом виде спорен. | философия |
| `philosophy.science.falsifiability` | ПРИНЦИП | Фальсифицируемость требует, чтобы claim мог быть опровергнут возможным наблюдением. | Не все научные практики сводятся к одному критерию. | наука |
| `philosophy.science.paradigm` | МОДЕЛЬ | Paradigm задаёт общие понятия, методы и стандарты науки в эпоху. | Термин связан с Kuhn and debate. | история |
| `philosophy.science.normal_science` | МОДЕЛЬ | Normal science решает задачи внутри принятой парадигмы. | Не обязательно некреативна. | наука |
| `philosophy.science.paradigm_shift` | ПРОЦЕСС | Paradigm shift меняет базовую рамку объяснения. | Не любое открытие — shift. | история |
| `philosophy.science.reductionism` | ПОЗИЦИЯ | Reductionism объясняет сложное через более простые уровни. | Может терять emergent properties. | системы |
| `philosophy.science.holism` | ПОЗИЦИЯ | Holism подчёркивает свойства целого и контекст. | Может быть расплывчатым без механизма. | системы |
| `philosophy.science.instrumentalism` | ПОЗИЦИЯ | Instrumentalism ценит теории как инструменты предсказания. | Не отвечает прямо, "реальны" ли сущности теории. | наука |
| `philosophy.science.realism` | ПОЗИЦИЯ | Scientific realism считает, что успешные теории примерно описывают реальный мир. | Спорит с anti-realism. | наука |
| `philosophy.logic.deduction` | REASONING_MODE | Дедукция выводит следствие, необходимое из посылок. | Истинность вывода зависит от истинности посылок. | логика |
| `philosophy.logic.induction` | REASONING_MODE | Индукция обобщает из случаев к правилу. | Даёт вероятностную поддержку. | логика |
| `philosophy.logic.abduction` | REASONING_MODE | Abduction ищет лучшее объяснение наблюдения. | Может выбрать красивую, но ложную гипотезу. | рассуждение |
| `philosophy.logic.analogy` | REASONING_MODE | Аналогия переносит структуру между доменами. | Нужно искать disanalogies. | перекрестный_домен |
| `philosophy.logic.validity_soundness` | РАЗЛИЧИЕ | Validity — форма вывода; soundness — validity плюс истинные посылки. | Частая путаница в споре. | логика |
| `philosophy.logic.modal` | ЛОГИК_ТИП | Modal logic работает с возможностью и необходимостью. | Семантики различаются. | логика |
| `philosophy.logic.deontic` | ЛОГИК_ТИП | Deontic logic формализует обязанность, разрешение и запрет. | Нормативные парадоксы сложны. | этика |
| `philosophy.logic.paraconsistent` | ЛОГИК_ТИП | Paraconsistent logic допускает противоречия без взрыва всей системы. | Полезна для конфликтных баз знания. | знание_график |
| `philosophy.ethics.consequentialism` | ПОЗИЦИЯ | Consequentialism оценивает действие по последствиям. | Сложно считать все последствия. | этика |
| `philosophy.ethics.deontology` | ПОЗИЦИЯ | Deontology оценивает действие по обязанностям и правилам. | Может конфликтовать с outcomes. | этика |
| `philosophy.ethics.virtue` | ПОЗИЦИЯ | Virtue ethics фокусируется на качествах характера и практической мудрости. | Менее процедурна. | этика |
| `philosophy.ethics.care` | ПОЗИЦИЯ | Ethics of care подчёркивает отношения, зависимость и заботу. | Важно для медицины и семейных решений. | этика |
| `philosophy.ethics.principlism` | МОДЕЛЬ | Принципизм использует автономию, благодеяние, непричинение вреда, справедливость. | Принципы могут конфликтовать. | биоэтика |
| `philosophy.ethics.autonomy` | ПРИНЦИП | Автономия уважает способность человека принимать решения о себе. | Требует информации и отсутствия принуждения. | права |
| `philosophy.ethics.nonmaleficence` | ПРИНЦИП | Non-maleficence требует не причинять вред. | Иногда вред и польза конфликтуют. | безопасность |
| `philosophy.ethics.beneficence` | ПРИНЦИП | Beneficence требует стремиться к благу другого. | Нельзя оправдывать paternalism без границ. | забота |
| `philosophy.ethics.justice` | ПРИНЦИП | Justice требует справедливого распределения благ, рисков и прав. | Теории справедливости спорят. | общество |
| `philosophy.political.social_contract` | МОДЕЛЬ | Social contract объясняет власть как соглашение ради порядка и защиты. | Исторически не буквальный контракт. | политика |
| `philosophy.political.liberty` | ЦЕНИТЬ | Свобода может пониматься как отсутствие вмешательства или способность действовать. | Negative/positive liberty различаются. | права |
| `philosophy.political.equality` | ЦЕНИТЬ | Equality может значить равные права, возможности или результаты. | Разные смыслы конфликтуют. | политика |
| `philosophy.political.legitimacy` | СРОК | Legitimacy — признание власти оправданной. | Не равна одной legal validity. | управление |
| `philosophy.mind.consciousness` | ПРОБЛЕМА | Consciousness — проблема субъективного опыта и его связи с мозгом. | Нельзя честно обещать "сознательный AI". | разум |
| `philosophy.mind.intentionality` | СРОК | Intentionality — направленность мыслей на объекты или содержание. | Не то же, что намерение в быту. | разум |
| `philosophy.mind.embodiment` | ПОЗИЦИЯ | Embodiment подчёркивает роль тела и действия в мышлении. | Не отменяет абстрактное мышление. | познание |
| `philosophy.language.meaning_use` | ПОЗИЦИЯ | Meaning as use связывает значение слова с практикой употребления. | Не единственная теория значения. | язык |
| `philosophy.language.reference` | СРОК | Reference связывает выражение с объектом или классом объектов. | Имена, описания и контекст сложны. | семантика |
| `philosophy.language.speech_act` | МОДЕЛЬ | Speech act рассматривает высказывания как действия: обещание, приказ, вопрос. | Смысл зависит от ситуации. | коммуникация |
| `philosophy.aesthetics.beauty` | ПРОБЛЕМА | Beauty может пониматься как свойство, опыт, культурная норма или отношение. | Не сводить к одному вкусу. | искусство |
| `philosophy.aesthetics.sublime` | КОНЦЕПЦИЯ | Sublime связано с переживанием величия, опасности или бесконечности. | Исторический термин эстетики. | искусство |
| `philosophy.technology.instrumental_view` | ПОЗИЦИЯ | Инструментальный взгляд считает технологию нейтральным средством. | Критика: инструменты меняют поведение и общество. | технология |
| `philosophy.technology.affordance` | КОНЦЕПЦИЯ | Affordance показывает, какие действия вещь делает возможными или очевидными. | Зависит от пользователя и контекста. | дизайн |
| `philosophy.technology.technological_mediation` | МОДЕЛЬ | Технологии посредничают восприятие, действие и социальные отношения. | Важно для AI and interfaces. | СТС |
| `philosophy.ai.alignment` | ПРОБЛЕМА | AI alignment пытается согласовать поведение AI с человеческими целями и нормами. | Цели людей конфликтуют. | AI_безопасность |
| `philosophy.ai.explainability` | ПРИНЦИП | Explainability требует понятного пути от входа к выводу. | Объяснение может быть post-hoc и неверным. | ИИ |
| `philosophy.ai.accountability` | ПРИНЦИП | Подотчетность спрашивает, кто отвечает за решения ИИ и вред. | Нужны роли, logs, governance. | закон |
| `philosophy.ai.personification_risk` | РИСК | Персонификация AI может создавать ложное доверие и зависимость. | Интерфейс должен быть честным. | этика |
| `philosophy.meaning.purpose` | КОНЦЕПЦИЯ | Purpose связывает действие с желаемым направлением и ценностью. | Может быть личным, социальным, институциональным. | значение |
| `philosophy.meaning.narrative_identity` | МОДЕЛЬ | Narrative identity связывает жизнь человека через истории о себе. | История может исцелять или ограничивать. | психология |
| `philosophy.meaning.absurd` | КОНЦЕПЦИЯ | Абсурд описывает конфликт между поиском смысла и безразличным миром. | Разные философы отвечают по-разному. | экзистенциальный |
| `philosophy.practical_wisdom` | КОНЦЕПЦИЯ | Practical wisdom — умение применять правила к конкретной ситуации. | Не заменяется списком норм. | этика |
| `philosophy.argument.steelman` | МЕТОД | Steelman усиливает позицию оппонента перед критикой. | Помогает честному спору. | коммуникация |
| `philosophy.argument.charity` | ПРИНЦИП | Principle of charity интерпретирует аргумент в разумной сильной форме. | Не означает игнорировать ошибки. | рассуждение |
| `philosophy.argument.burden_of_proof` | ПРИНЦИП | Тот, кто делает claim, обычно несёт burden of proof. | Зависит от контекста. | логика |
| `philosophy.argument.defeater` | СРОК | Defeater — информация, ослабляющая или отменяющая обоснование. | Важно для non-monotonic reasoning. | эпистемология |
| `philosophy.knowledge.negative` | КОНЦЕПЦИЯ | Negative knowledge хранит, что не работает и почему. | Особенно ценно для инженерии и науки. | world_knowledge |
| `philosophy.knowledge.uncertainty_honesty` | ПРИНЦИП | Честная система сообщает неопределённость, а не имитирует уверенность. | Центрально для Velantrim. | ворота истины |

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
