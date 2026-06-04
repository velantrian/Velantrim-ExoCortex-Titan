# BATCH_129 — Civic Systems, Electoral & Institution Detail
# world_skills_core · source: world_skills_core:batch_129:civic_systems_electoral_detail
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| civsys.government.unitary_state | Unitary state | invariant | Унитарное государство концентрирует суверенную власть на центральном уровне, хотя может делегировать полномочия регионам. | отличать от федерации |
| civsys.government.federal_state | Federal state | invariant | Федерация разделяет власть между общим уровнем и субъектами, которые имеют конституционно защищенные полномочия. | понимать уровни права |
| civsys.government.confederation | Confederation | variant | Конфедерация обычно является союзом государств с ограниченными общими органами и сильной автономией участников. | редкая форма интеграции |
| civsys.government.devolution | Devolution | variant | Devolution передает полномочия региональным органам без полного изменения суверенитета государства. | региональная автономия |
| civsys.government.separation_of_powers | Separation of powers | invariant | Разделение властей распределяет законодательные, исполнительные и судебные функции между разными институтами. | защита от концентрации власти |
| civsys.government.checks_balances | Checks and balances | invariant | Checks and balances дают ветвям власти инструменты ограничивать и контролировать друг друга. | предотвращение злоупотреблений |
| civsys.government.parliamentary_system | Parliamentary system | invariant | В парламентской системе правительство обычно зависит от доверия парламента и может быть сменено парламентским голосованием. | понять ответственность кабинета |
| civsys.government.presidential_system | Presidential system | invariant | В президентской системе глава исполнительной власти обычно избирается отдельно от парламента и имеет фиксированный срок. | источник мандата президента |
| civsys.government.semi_presidential | Semi-presidential system | variant | Полупрезидентская система сочетает избранного президента и правительство, ответственное перед парламентом в разной степени. | возможна двойная исполнительная власть |
| civsys.legislature.unicameral | Unicameral legislature | invariant | Однопалатный парламент принимает законы через одну законодательную палату. | проще процедура |
| civsys.legislature.bicameral | Bicameral legislature | invariant | Двухпалатный парламент разделяет законодательный процесс между двумя палатами с разными функциями или представительством. | дополнительный фильтр законов |
| civsys.legislature.upper_house_role | Upper house role | variant | Верхняя палата часто представляет регионы, пересматривает законы или выполняет особые конституционные функции. | зависит от конституции |
| civsys.legislature.committee_system | Legislative committees | invariant | Парламентские комитеты детально рассматривают проекты, проводят слушания и контролируют профильные сферы. | работа парламента не только пленарная |
| civsys.legislature.public_hearing | Public hearing | variant | Публичное слушание позволяет собрать позиции экспертов, граждан или организаций перед решением. | участие и легитимность |
| civsys.executive.cabinet_collective | Cabinet collective responsibility | variant | Коллективная ответственность кабинета означает публичную поддержку общего решения правительства его членами. | дисциплина правительства |
| civsys.executive.caretaker_government | Caretaker government | variant | Временное правительство обычно ограничивает спорные решения до формирования полноценного кабинета. | управление переходом |
| civsys.executive.civil_service_neutrality | Civil service neutrality | invariant | Политическая нейтральность госслужбы требует исполнения закона и профессиональных решений независимо от партийной смены власти. | устойчивость государства |
| civsys.judiciary.judicial_review | Judicial review | invariant | Судебный контроль позволяет суду оценивать соответствие актов конституции или закону. | защита прав и иерархии норм |
| civsys.judiciary.constitutional_court | Constitutional court | variant | Конституционный суд специализируется на вопросах конституционности и полномочиях государственных органов. | отдельный фильтр законов |
| civsys.judiciary.independence | Judicial independence | invariant | Независимость суда требует защиты от неправомерного давления, конфликта интересов и произвольного смещения судей. | доверие к правосудию |
| civsys.election.first_past_post | First-past-the-post | invariant | First-past-the-post выбирает кандидата с наибольшим числом голосов в округе без требования абсолютного большинства. | простота и диспропорции |
| civsys.election.two_round_system | Two-round system | invariant | Двухтуровая система проводит второй тур, если в первом никто не достиг требуемого порога. | добивается более широкой поддержки |
| civsys.election.proportional_representation | Proportional representation | invariant | Пропорциональное представительство распределяет места между списками или партиями в зависимости от доли голосов. | отражает партийные доли |
| civsys.election.mixed_member | Mixed-member system | variant | Смешанная система сочетает одномандатные округа и партийные списки в одной модели представительства. | баланс локального и партийного |
| civsys.election.rank_choice | Ranked-choice voting | variant | Ranked-choice voting позволяет избирателю ранжировать кандидатов, а подсчет перераспределяет голоса по правилам системы. | снижает потерю голоса |
| civsys.election.threshold | Electoral threshold | variant | Избирательный барьер требует минимальной доли голосов для получения мест в представительном органе. | ограничивает фрагментацию |
| civsys.election.district_magnitude | District magnitude | invariant | District magnitude показывает число мест в округе и сильно влияет на пропорциональность результата. | ключевой параметр системы |
| civsys.election.gerrymandering | Gerrymandering | variant | Gerrymandering манипулирует границами округов для политического преимущества одной группы. | риск нечестного представительства |
| civsys.election.independent_commission | Electoral boundary commission | variant | Независимая комиссия по границам округов снижает риск партийной манипуляции округами. | доверие к карте округов |
| civsys.election.voter_registration | Voter registration | variant | Регистрация избирателей определяет, кто включен в список голосующих, и влияет на доступность участия. | административный барьер или защита |
| civsys.election.secret_ballot | Secret ballot | invariant | Тайное голосование защищает избирателя от давления, покупки голоса и наказания за выбор. | основа свободных выборов |
| civsys.election.observer_role | Election observer | variant | Наблюдатель за выборами фиксирует соответствие процедур правилам, но не заменяет избирательную администрацию. | прозрачность процесса |
| civsys.election.turnout_metric | Voter turnout | invariant | Явка измеряет долю участвовавших избирателей среди имеющих право или зарегистрированных, в зависимости от методики. | сравнения требуют определения базы |
| civsys.party.party_system | Party system | invariant | Партийная система описывает устойчивую структуру конкуренции между партиями и их связь с обществом. | понять политическую динамику |
| civsys.party.coalition_government | Coalition government | variant | Коалиционное правительство формируется несколькими партиями, согласующими программу и распределение должностей. | частый результат пропорциональных систем |
| civsys.party.whip_discipline | Party whip | variant | Party whip координирует голосование членов партии и поддерживает дисциплину фракции. | связь партии и парламента |
| civsys.rights.bill_of_rights | Bill of rights | invariant | Билль о правах закрепляет основные права и свободы как ограничение публичной власти. | правовая защита граждан |
| civsys.rights.due_process | Due process | invariant | Due process требует справедливой процедуры перед лишением человека прав, свободы или собственности. | процедурная защита |
| civsys.rights.equal_protection | Equal protection | invariant | Equal protection требует, чтобы государство не применяло закон произвольно или дискриминационно к сопоставимым людям. | равенство перед законом |
| civsys.budget.appropriation | Budget appropriation | invariant | Appropriation дает органу власти законное разрешение расходовать деньги на определенные цели. | деньги требуют мандата |
| civsys.budget.audit_institution | Supreme audit institution | invariant | Высший орган аудита проверяет законность, эффективность или достоверность использования публичных средств. | контроль бюджета |
| civsys.local.municipal_government | Municipal government | invariant | Муниципальное управление отвечает за локальные услуги, инфраструктуру и правила в пределах предоставленных полномочий. | ближний уровень государства |
| civsys.local.public_consultation | Public consultation | variant | Общественная консультация собирает обратную связь до принятия решения, но её юридическая сила зависит от правил процедуры. | участие без прямого голосования |
| civsys.accountability.ombudsman | Ombudsman | variant | Омбудсмен рассматривает жалобы на органы власти или защищает определенную группу прав в рамках установленного мандата. | мягкий механизм контроля |
