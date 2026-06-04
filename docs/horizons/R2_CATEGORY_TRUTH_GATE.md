# R2 — Category-Theoretic Formalization Truth Gate (Horizons)

> **Статус: 🔬 research** — в **VELANTRIM V8.6 Complex** runtime Truth Gate (`core/truth_gate.py`) работает **императивно**. Категориальная формализация ESM-переходов — **только в спеке V9 (§R2)**, без compile-time проверки.

## Зачем R2

Сегодня переходы ESM (Promote / Demote / Invalidate) проверяются в Python в runtime. Ошибки композиции правил (недопустимый морфизм, конфликт Cognitive Mode) обнаруживаются **тестами и инцидентами**, не при сборке.

**R2** переносит часть гарантий на **compile-time**:

- объекты = пары (Layer, ESM state);
- морфизмы = допустимые переходы;
- композиция переходов = типобезопасная цепочка;
- смена стратегии валидации = естественное преобразование между функторами.

Цель: **невозможные** epistemic transitions не собираются в проект, а не падают в production.

## Конструкция (план V9)

| Элемент | Смысл |
|---------|--------|
| **Категория Velantrim** | Obj = (Layer, ESM); Hom = Promote, Demote, Invalidate, … |
| **Функторы F** | Сохраняют допустимые transitions при смене политики |
| **TruthMonad T** | return + bind для цепочек проверок (Kleisli) |
| **GATs** | Обобщённые алгебраические теории для `compose(f, g)` |

Пример (Julia / Catlab):

```julia
compose(f::Hom(A,B), g::Hom(B,C)) :: Hom(A,C)
```

## Планируемые артефакты

| Артефакт | Назначение |
|----------|------------|
| **ESMCategory.spec** | Канонический граф переходов |
| **Catlab прототип** | Верификация коммутативных диаграмм |
| **Python stubs** | `Protocol` + `TypeVar` + `mypy --strict` |
| **PyJulia bridge** | Опционально для production parity |

## Связь с V8.6 сегодня

| Сейчас (runtime) | Роль при R2 |
|------------------|-------------|
| `core/truth_gate.py` | Источник истины для извлечения морфизмов |
| `core/memory.py` | ESM storage + transition log |
| Cognitive Modes | Естественные преобразования между функторами |
| `tests/test_truth_gate*.py` | Ground truth для категориальной модели |

Runtime Truth Gate **остаётся**; R2 — **дополнительный** слой верификации, не замена.

## Будущие инварианты

I104–I110 (V9).

## Чего R2 **не** делает

- Не отменяет runtime проверки (defense in depth).
- Не заменяет LLM semantic validation.
- Не требует Julia в hot path (только CI / proto).

## Этапы

| Этап | Статус |
|------|--------|
| V9 §R2 описание | ✅ |
| Экспорт ESM transition table из кода | 🔬 research |
| Catlab прототип | 🔬 research |
| mypy plugin / stubs | 🔜 V10+ |

## Источники

- V9 §R2
- Fong & Spivak, *Seven Sketches in Compositionality*, arXiv:1803.05316
- Cartmell, *Generalised algebraic theories*, 1986
- Gavranović et al., *Categorical Deep Learning*, ICML 2024

Индекс: [`../HORIZONS.md`](../HORIZONS.md) · карта: [`../LAYERS_AND_HORIZONS.ru.md`](../LAYERS_AND_HORIZONS.ru.md)
