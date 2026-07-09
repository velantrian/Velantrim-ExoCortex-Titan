# BATCH_127 — Material Degradation Failure Modes Detail
# world_skills_core · source: world_skills_core:batch_127:material_degradation_detail
# KnowledgeUnits: 44

| ID | KnowledgeUnit | Тип | Суть | Практический смысл |
|----|---------------|-----|------|--------------------|
| matdeg.metal.uniform_corrosion | Uniform corrosion | invariant | Равномерная коррозия уменьшает толщину металла по большой площади и часто прогнозируется по скорости потери материала. | расчет остаточной толщины |
| matdeg.metal.pitting_corrosion | Pitting corrosion | invariant | Питтинговая коррозия создаёт локальные глубокие ямки, которые могут пробить стенку при малой общей потере массы. | опасна для труб и сосудов |
| matdeg.metal.crevice_corrosion | Crevice corrosion | invariant | Щелевая коррозия развивается в узких зазорах, где задерживается электролит и меняется локальная химия среды. | учитывать стыки и прокладки |
| matdeg.metal.galvanic_corrosion | Galvanic corrosion | invariant | Гальваническая коррозия возникает при контакте разных металлов через электролит, когда менее благородный металл растворяется быстрее. | подбор совместимых материалов |
| matdeg.metal.stress_corrosion_cracking | Stress corrosion cracking | invariant | Коррозионное растрескивание под напряжением требует сочетания растягивающего напряжения, чувствительного материала и специфической среды. | трещины без сильной общей коррозии |
| matdeg.metal.hydrogen_embrittlement | Hydrogen embrittlement | invariant | Водородное охрупчивание снижает пластичность металла и может вызвать внезапное разрушение под нагрузкой. | риск для высокопрочных сталей |
| matdeg.metal.intergranular_corrosion | Intergranular corrosion | invariant | Межкристаллитная коррозия разрушает границы зерен, когда химический состав или термоистория делают их уязвимыми. | контроль сварки и термообработки |
| matdeg.metal.microbiologically_influenced | Microbiologically influenced corrosion | variant | Микробиологически индуцированная коррозия возникает, когда микроорганизмы меняют локальную химию поверхности металла. | трубопроводы, резервуары, вода |
| matdeg.metal.freting_wear | Fretting wear | invariant | Fretting wear появляется при малых колебательных перемещениях между контактирующими поверхностями под нагрузкой. | болтовые соединения и посадки |
| matdeg.metal.thermal_fatigue | Thermal fatigue | invariant | Термическая усталость возникает от повторных температурных циклов, создающих переменные напряжения в материале. | горячие узлы и печи |
| matdeg.metal.creep_deformation | Creep deformation | invariant | Ползучесть — медленная деформация материала под постоянной нагрузкой при значимой температуре относительно температуры плавления. | ресурс высокотемпературных деталей |
| matdeg.metal.oxidation_scale | Oxidation scale | variant | Оксидная окалина может защищать металл или отслаиваться, открывая свежую поверхность для дальнейшего окисления. | оценка жаростойкости |
| matdeg.polymer.uv_degradation | UV degradation | invariant | Ультрафиолет разрушает химические связи в полимерах и вызывает хрупкость, выцветание или растрескивание. | наружные пластики требуют стабилизаторов |
| matdeg.polymer.thermal_oxidation | Polymer thermal oxidation | invariant | Термоокисление полимера ускоряет старение при высокой температуре и доступе кислорода. | ресурс изоляции и уплотнений |
| matdeg.polymer.hydrolysis | Polymer hydrolysis | invariant | Гидролиз разрушает чувствительные полимерные связи под действием воды, особенно при повышенной температуре или кислотности. | выбор материала во влажной среде |
| matdeg.polymer.plasticizer_loss | Plasticizer loss | variant | Потеря пластификатора делает некоторые пластики и резины более твердыми, хрупкими или усаженными. | старение кабелей и прокладок |
| matdeg.polymer.environmental_stress_cracking | Environmental stress cracking | invariant | Environmental stress cracking возникает, когда химическая среда и механическое напряжение вместе вызывают трещины в полимере. | бытовая химия может вредить пластику |
| matdeg.polymer.swelling_solvent | Solvent swelling | invariant | Растворитель может проникать в полимер, вызывая набухание, потерю прочности и изменение размеров. | совместимость с жидкостями |
| matdeg.rubber.ozone_cracking | Ozone cracking | invariant | Озон вызывает трещины в напряженной резине, особенно на растянутых поверхностях. | хранение и выбор эластомеров |
| matdeg.rubber.compression_set | Compression set | invariant | Compression set показывает остаточную деформацию эластомера после длительного сжатия. | уплотнение может потерять герметичность |
| matdeg.composite.delamination | Composite delamination | invariant | Деламинация композита — расслоение между слоями, которое снижает жесткость и несущую способность. | важен контроль ударов и дефектов |
| matdeg.composite.matrix_cracking | Matrix cracking | invariant | Трещины матрицы в композите могут появляться раньше разрушения волокон и открывать путь влаге. | ранний признак повреждения |
| matdeg.composite.fiber_breakage | Fiber breakage | invariant | Разрыв волокон в композите напрямую снижает способность слоя нести нагрузку вдоль направления волокон. | критичный дефект |
| matdeg.composite.moisture_ingress | Moisture ingress | variant | Влага в композите может снижать свойства матрицы, вызывать набухание и ухудшать адгезию слоев. | защита кромок и покрытий |
| matdeg.concrete.carbonation | Concrete carbonation | invariant | Карбонизация бетона снижает щелочность и может лишить арматуру пассивной защиты от коррозии. | диагностика старых конструкций |
| matdeg.concrete.chloride_ingress | Chloride ingress | invariant | Хлориды проникают в бетон и могут запускать коррозию арматуры даже при достаточной толщине защитного слоя. | дороги, мосты, морская среда |
| matdeg.concrete.alkali_silica_reaction | Alkali-silica reaction | invariant | Щелочно-кремнеземная реакция образует расширяющийся гель и может вызывать трещины в бетоне. | совместимость заполнителей |
| matdeg.concrete.freeze_thaw_scaling | Freeze-thaw scaling | invariant | Циклы замерзания и оттаивания повреждают насыщенный водой бетон, особенно без достаточной воздушной пористости. | долговечность наружных поверхностей |
| matdeg.concrete.sulfate_attack | Sulfate attack | invariant | Сульфатная атака меняет продукты цементного камня и может вызвать расширение, размягчение или трещины бетона. | выбор цемента и среды |
| matdeg.wood.fungal_decay | Wood fungal decay | invariant | Грибковое разрушение древесины требует влаги, питательной среды, кислорода и подходящей температуры. | контроль влажности важнее покраски |
| matdeg.wood.insect_damage | Wood insect damage | variant | Насекомые могут разрушать древесину ходами и галереями, снижая сечение и прочность элемента. | обследование скрытых полостей |
| matdeg.wood.moisture_movement | Wood moisture movement | invariant | Древесина меняет размеры при изменении влажности, причем поперечное изменение обычно больше продольного. | учитывать усушку и разбухание |
| matdeg.glass.thermal_shock | Glass thermal shock | invariant | Термошок стекла возникает, когда температурный градиент создает растягивающие напряжения выше прочности стекла. | избегать резкого нагрева |
| matdeg.glass.surface_scratches | Glass surface scratches | invariant | Поверхностные царапины на стекле концентрируют напряжения и снижают фактическую прочность. | защита кромок и поверхности |
| matdeg.coating.adhesion_failure | Coating adhesion failure | invariant | Отказ адгезии покрытия происходит, когда связь покрытия с подложкой слабее эксплуатационных напряжений или среды. | подготовка поверхности |
| matdeg.coating.underfilm_corrosion | Underfilm corrosion | invariant | Подпленочная коррозия развивается под покрытием после проникновения влаги или дефекта барьера. | дефект может расширяться скрыто |
| matdeg.coating.chalking | Coating chalking | variant | Меление покрытия возникает при разрушении связующего на поверхности и образовании порошкообразного слоя. | признак старения краски |
| matdeg.electronics.electromigration | Electromigration | invariant | Электромиграция переносит атомы проводника под действием высокой плотности тока и может разрушать микропроводники. | надежность микросхем |
| matdeg.electronics.tin_whiskers | Tin whiskers | variant | Оловянные whiskers — тонкие металлические кристаллы, способные вызывать короткие замыкания в электронике. | риск бессвинцовых покрытий |
| matdeg.electronics.solder_fatigue | Solder fatigue | invariant | Усталость пайки возникает от циклов температуры и различия коэффициентов теплового расширения компонентов. | отказ BGA и разъемов |
| matdeg.electronics.caf_growth | Conductive anodic filament | variant | Conductive anodic filament может расти внутри печатной платы при влаге, напряжении и загрязнении, создавая утечку или короткое замыкание. | надежность PCB |
| matdeg.storage.shelf_life | Material shelf life | variant | Shelf life материала ограничивает срок, в течение которого свойства сохраняются при заданных условиях хранения. | клеи, резины, химия |
| matdeg.inspection.damage_mapping | Damage mapping | invariant | Карта повреждений фиксирует тип, размер, место и развитие дефектов, чтобы отличать случайный дефект от тренда деградации. | план ремонта |
| matdeg.design.material_compatibility | Material compatibility | invariant | Совместимость материалов учитывает химическую среду, температуру, контактные пары, влажность и механические нагрузки. | предотвращение преждевременного отказа |
