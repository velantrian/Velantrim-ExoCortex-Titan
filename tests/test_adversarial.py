# tests/test_adversarial.py
# Velantrim ExoCortex — Adversarial Attack Tests
# v1.0.0
#
# Запуск:
#   pytest tests/test_adversarial.py -v
#   pytest tests/test_adversarial.py -v -k "TruthGate"
#
# Цель: найти слабые места ДО того как их найдёт кто-то другой.
# Все тесты должны PASS — система должна корректно отклонять атаки,
# не падать с необработанным исключением.
#
# Принцип: xfail честнее чем "всё работает"

import os
import threading

import pytest

# ─── ФИКСТУРЫ ────────────────────────────────────────────────────────────────

def _promote_to_validated(store, fact_id: str, by: str = "test") -> None:
    """Observed → Hypothesized → Supported → Validated (матрица ESM V8.8)."""
    store.promote_to_validated(fact_id, by=by)


@pytest.fixture
def store(tmp_path):
    """Изолированный store для каждого теста."""
    from core.memory import make_store
    s = make_store(str(tmp_path / "test.db"))
    yield s
    s.close()


@pytest.fixture
def clean_global(monkeypatch, tmp_path):
    """
    Патчим _GLOBAL_STORE чтобы тесты не писали в боевую БД.
    """
    import core.memory as mem
    from core.memory import make_store
    s = make_store(str(tmp_path / "adversarial.db"))
    monkeypatch.setattr(mem, "_GLOBAL_STORE", s)
    monkeypatch.setattr(mem, "_L0", s._l0)
    yield s
    s.close()


# ═══════════════════════════════════════════════════════════════════════════════
# 1. АТАКИ НА TRUTHGATE
# ═══════════════════════════════════════════════════════════════════════════════

class TestTruthGateAttacks:
    """
    Цель: TruthGate должен отклонять мусор БЕЗ падения с исключением.
    Любой unhandled exception = баг.
    """

    def _pack(self, **kwargs):
        defaults = {"fact_id": "atk1", "claim": "test claim",
                    "source": "test", "confidence": 0.9}
        defaults.update(kwargs)
        return {"facts": [defaults]}

    def test_source_whitespace_only_blocked(self):
        """Пробелы вместо source не должны проходить."""
        from core.pipeline import truth_gate
        ok, reason = truth_gate(self._pack(source="   "))
        assert not ok, "source из пробелов должен блокироваться"

    def test_source_none_blocked(self):
        from core.pipeline import truth_gate
        ok, reason = truth_gate(self._pack(source=None))
        assert not ok

    def test_confidence_nan_blocked(self):
        """NaN confidence не должен пройти."""
        from core.pipeline import truth_gate
        ok, reason = truth_gate(self._pack(confidence=float("nan")))
        assert not ok, "NaN confidence должен блокироваться"

    def test_confidence_inf_blocked(self):
        """Бесконечность не является валидным confidence."""
        from core.pipeline import truth_gate
        ok, reason = truth_gate(self._pack(confidence=float("inf")))
        assert not ok

    def test_confidence_negative_blocked(self):
        from core.pipeline import truth_gate
        ok, reason = truth_gate(self._pack(confidence=-0.1))
        assert not ok

    def test_confidence_zero_blocked(self):
        from core.pipeline import truth_gate
        ok, reason = truth_gate(self._pack(confidence=0.0))
        assert not ok

    def test_empty_facts_blocked(self):
        from core.pipeline import truth_gate
        ok, _ = truth_gate({"facts": []})
        assert not ok

    def test_facts_key_missing_blocked(self):
        """Нет ключа facts вообще."""
        from core.pipeline import truth_gate
        ok, _ = truth_gate({})
        assert not ok

    def test_very_long_source_no_crash(self):
        """Очень длинный source не должен ронять систему."""
        from core.pipeline import truth_gate
        long_source = "s" * 100_000
        try:
            ok, reason = truth_gate(self._pack(source=long_source))
            # Может пройти или нет — главное не упасть
        except Exception as exc:
            pytest.fail(f"truth_gate упал с исключением: {exc}")

    def test_real_truthgate_insufficient_evidence(self, clean_global):
        """
        Реальный TruthGate (BALANCED) требует evidence_count ≥ 2.
        Факт без evidence_refs должен блокироваться.
        """
        from core.pipeline import truth_gate
        pack = self._pack(confidence=0.95)  # высокая уверенность, но нет evidence
        ok, reason = truth_gate(pack, mode="BALANCED")
        assert not ok
        assert "evidence" in reason.lower()

    def test_real_truthgate_with_evidence_passes(self, clean_global):
        """Факт с evidence_refs проходит BALANCED."""
        from core.pipeline import truth_gate
        pack = {"facts": [{
            "fact_id": "ev1", "claim": "test", "source": "test",
            "confidence": 0.9,
            "metadata": {"evidence_refs": ["ref1", "ref2"]},
        }]}
        ok, reason = truth_gate(pack, mode="BALANCED")
        assert ok, f"Должен пройти с evidence: {reason}"


# ═══════════════════════════════════════════════════════════════════════════════
# 2. АТАКИ НА ESM
# ═══════════════════════════════════════════════════════════════════════════════

class TestESMAttacks:
    """
    ESM должен быть непробиваем: никаких прыжков через состояния,
    никакого изменения ImmutableCore.
    """

    def test_jump_to_immutable_core_blocked(self, store):
        """Нельзя перевести обычный факт в ImmutableCore через transition_esm."""
        from core.memory import ImmutableStateError
        store.store_fact({"fact_id": "regular", "claim": "x",
                          "source": "s", "confidence": 0.5})
        with pytest.raises((ImmutableStateError, ValueError)):
            store.transition_esm("regular", "ImmutableCore", by="attacker")

    def test_invalid_state_name_blocked(self, store):
        """Несуществующее состояние должно отклоняться."""
        store.store_fact({"fact_id": "f1", "claim": "x",
                          "source": "s", "confidence": 0.5})
        with pytest.raises(ValueError):
            store.transition_esm("f1", "Hacked", by="attacker")

    def test_forbidden_transition_blocked(self, store):
        """Observed → ImmutableCore напрямую запрещён."""
        from core.memory import ImmutableStateError
        store.store_fact({"fact_id": "f2", "claim": "x",
                          "source": "s", "confidence": 0.5})
        with pytest.raises((ValueError, ImmutableStateError)):
            store.transition_esm("f2", "ImmutableCore", by="attacker")

    def test_ring_zero_immutable(self, store):
        """VALUES_CORE нельзя изменить ни при каких условиях."""
        from core.memory import ImmutableStateError
        with pytest.raises(ImmutableStateError):
            store.transition_esm("VALUES_CORE", "Contradicted", by="attacker")

    def test_race_condition_two_threads(self, store):
        """
        Два потока одновременно меняют один факт.
        Система не должна упасть — результат любой, но без exception.
        """
        store.store_fact({"fact_id": "race", "claim": "x",
                          "source": "s", "confidence": 0.5})
        errors = []

        def worker(target_state):
            try:
                store.transition_esm("race", target_state, by="thread")
            except Exception as exc:
                errors.append(str(exc))

        t1 = threading.Thread(target=worker, args=("Hypothesized",))
        t2 = threading.Thread(target=worker, args=("Collapsed",))
        t1.start(); t2.start()
        t1.join(); t2.join()

        # Главное — нет segfault или необработанного исключения
        # ValueError за неверный переход — допустимо
        bad = [e for e in errors if "segfault" in e.lower()
               or "database is locked" in e.lower()]
        assert not bad, f"Критические ошибки при race condition: {bad}"

    def test_store_fact_sql_injection_in_claim(self, store):
        """SQL injection в claim не должен ронять БД."""
        injections = [
            "'; DROP TABLE facts; --",
            "' OR '1'='1",
            "'; UPDATE facts SET confidence=0; --",
            "\"; DELETE FROM facts; --",
        ]
        for inj in injections:
            try:
                store.store_fact({"fact_id": f"inj_{hash(inj)}", "claim": inj,
                                  "source": "s", "confidence": 0.5})
                fact = store.get_fact(f"inj_{hash(inj)}")
                assert fact is not None, "Факт должен сохраниться (injection безопасен)"
                assert fact["claim"] == inj, "Claim должен сохраниться как есть"
            except Exception as exc:
                pytest.fail(f"SQL injection вызвал исключение: {exc}")

        # Таблица facts всё ещё существует
        facts = store.get_all_facts()
        assert facts is not None


# ═══════════════════════════════════════════════════════════════════════════════
# 3. АТАКИ НА MEMORY
# ═══════════════════════════════════════════════════════════════════════════════

class TestMemoryAttacks:
    """
    Атаки на store_fact, store_facts_batch, get_fact.
    """

    def test_null_byte_in_claim(self, store):
        """Null byte не должен ронять SQLite."""
        try:
            store.store_fact({"fact_id": "null1", "claim": "test\x00hidden",
                              "source": "s", "confidence": 0.5})
        except Exception as exc:
            # Допустимо если отклоняет — главное не segfault
            assert "null" in str(exc).lower() or "invalid" in str(exc).lower(), \
                f"Неожиданное исключение: {exc}"

    def test_unicode_extremes_no_crash(self, store):
        """Экстремальный unicode не должен ронять систему."""
        claims = [
            "🧠💾🔗" * 100,           # много emoji
            "\u202e reversed text",   # right-to-left override
            "中文日本語한국어" * 50,        # CJK символы
            "\ufffd" * 1000,           # replacement characters
        ]
        for i, claim in enumerate(claims):
            try:
                store.store_fact({"fact_id": f"uni_{i}", "claim": claim,
                                  "source": "s", "confidence": 0.5})
            except Exception as exc:
                pytest.fail(f"Unicode вызвал crash: {exc}")

    def test_confidence_boundary_values(self, store):
        """Граничные значения confidence.

        FIX #28 (Claude audit 2026-07-28): the valid loop used to swallow
        any exception with a bare `except Exception: pass`, asserting
        nothing — a completely broken store_fact() for valid confidence
        values would still pass silently. The invalid loop used
        `pytest.raises((ValueError, Exception))`, which collapses to bare
        Exception (ValueError already is one) — any exception at all
        satisfied it, not specifically confidence validation. Empirically
        verified (not assumed): every value in `valid`, including the
        boundary 0.0, is actually accepted and round-trips; every value in
        `invalid` actually raises ValueError specifically.
        """
        valid = [0.0, 0.001, 0.5, 0.999, 1.0]
        invalid = [-0.001, -1.0, 1.001, 2.0, float("nan"), float("inf")]

        for v in valid:
            fid = f"v_{v}"
            store.store_fact({"fact_id": fid, "claim": "x", "source": "s", "confidence": v})
            stored = store.get_fact(fid)
            assert stored is not None, f"confidence={v} was not stored"
            assert stored["confidence"] == pytest.approx(v)

        for v in invalid:
            with pytest.raises(ValueError):
                store.store_fact({"fact_id": f"inv_{v}", "claim": "x",
                                  "source": "s", "confidence": v})

    def test_store_facts_batch_empty_list(self, store):
        """Пустой batch не должен падать."""
        result = store.store_facts_batch([])
        assert result["stored"] == 0
        assert result["errors"] == 0

    def test_store_facts_batch_with_invalid_facts(self, store):
        """Batch с несколькими фактами где часть невалидная."""
        facts = [
            {"fact_id": "good1", "claim": "valid", "source": "s", "confidence": 0.8},
            {"claim": "no fact_id", "source": "s", "confidence": 0.8},  # нет fact_id
            {"fact_id": "good2", "claim": "valid2", "source": "s", "confidence": 0.7},
        ]
        result = store.store_facts_batch(facts)
        assert result["stored"] >= 2, "Валидные факты должны сохраниться"
        assert result["errors"] >= 1, "Невалидный факт должен дать error"

    def test_very_large_batch_no_crash(self, store):
        """1000 фактов в одном batch не должны ронять систему."""
        facts = [
            {"fact_id": f"large_{i}", "claim": f"claim {i}",
             "source": "stress", "confidence": 0.7}
            for i in range(1000)
        ]
        try:
            result = store.store_facts_batch(facts)
            assert result["stored"] + result["updated"] == 1000
        except Exception as exc:
            pytest.fail(f"Большой batch упал: {exc}")

    def test_duplicate_fact_id_drift_protection(self, store):
        """
        Дважды store_fact с тем же fact_id но разным claim.
        Второй должен вызвать drift protection → Contradicted.
        """
        store.store_fact({"fact_id": "dup1", "claim": "original claim",
                          "source": "s", "confidence": 0.8})
        _promote_to_validated(store, "dup1")

        # Другой claim → drift protection
        store.store_fact({"fact_id": "dup1", "claim": "different claim",
                          "source": "s", "confidence": 0.8})

        fact = store.get_fact("dup1")
        assert fact["epistemic_state"] == "Contradicted", \
            "Изменённый Validated факт должен стать Contradicted"

    def test_get_fact_returns_deepcopy(self, store):
        """Мутация результата get_fact не должна корруптировать L0."""
        store.store_fact({"fact_id": "copy1", "claim": "original",
                          "source": "s", "confidence": 0.5})
        fact = store.get_fact("copy1")
        fact["claim"] = "MUTATED"  # мутируем снаружи

        fact2 = store.get_fact("copy1")
        assert fact2["claim"] == "original", \
            "Мутация результата get_fact не должна менять L0"


# ═══════════════════════════════════════════════════════════════════════════════
# 4. АТАКИ НА PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

class TestPipelineAttacks:
    """
    Pipeline должен возвращать error-ответ, а не падать.
    """

    def test_empty_query_no_crash(self, clean_global):
        """Пустая строка не должна ронять pipeline."""
        from core.pipeline import run
        try:
            result = run("")
            # Должен вернуть error, а не упасть
            assert "error" in result or "answer" in result
        except Exception as exc:
            pytest.fail(f"Pipeline упал на пустой строке: {exc}")

    def test_very_long_query_no_crash(self, clean_global):
        """100K символов не должны ронять pipeline."""
        from core.pipeline import run
        try:
            result = run("q" * 100_000)
            assert "error" in result or "answer" in result
        except Exception as exc:
            pytest.fail(f"Pipeline упал на длинном запросе: {exc}")

    def test_special_chars_query_no_crash(self, clean_global):
        """Спецсимволы в query."""
        from core.pipeline import run
        attacks = [
            "'; DROP TABLE facts; --",
            "<script>alert(1)</script>",
            "{{7*7}}",              # template injection
            "\x00\x01\x02",         # control chars
            "🧠" * 1000,
        ]
        for attack in attacks:
            try:
                result = run(attack)
                assert isinstance(result, dict), "Должен вернуть dict"
            except Exception as exc:
                pytest.fail(f"Pipeline упал на '{attack[:20]}...': {exc}")

    def test_idempotent_repeated_runs(self, clean_global):
        """10 одинаковых запросов подряд не ронят систему."""
        from core.pipeline import run
        results = []
        for _ in range(10):
            try:
                r = run("quantum entanglement")
                results.append(r)
            except Exception as exc:
                pytest.fail(f"Повторный run() упал: {exc}")

        [r for r in results if r.get("error")]
        # Первые запросы могут иметь ошибку (пустой store),
        # но не должно быть unhandled exception
        assert len(results) == 10

    def test_concurrent_pipeline_runs(self, clean_global):
        """5 параллельных run() не ронят систему."""
        from core.pipeline import run
        errors = []
        results = []

        def worker():
            try:
                r = run("DNA genetic information")
                results.append(r)
            except Exception as exc:
                errors.append(str(exc))

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads: t.start()
        for t in threads: t.join()

        critical = [e for e in errors
                    if "database is locked" not in e
                    and "segfault" not in e.lower()
                    and "duplicate column name" not in e.lower()]
        assert not critical, f"Критические ошибки при параллельном запуске: {critical}"

    def test_guardian_all_edge_cases(self):
        """Guardian должен обрабатывать все граничные случаи."""
        from core.pipeline import guardian

        # Нет фактов
        ok, reason = guardian({"facts": []}, [])
        assert not ok

        # Факт без fact_id
        pack = {"facts": [{"claim": "x", "source": "s"}]}
        trace = [{"fact_id": None}]
        ok, reason = guardian(pack, trace)
        assert not ok

        # Trace пустой
        pack = {"facts": [{"fact_id": "f1", "claim": "x", "source": "s"}]}
        ok, reason = guardian(pack, [])
        assert not ok

        # Факт не покрыт trace
        pack = {"facts": [{"fact_id": "f1", "claim": "x", "source": "s"}]}
        trace = [{"fact_id": "OTHER"}]
        ok, reason = guardian(pack, trace)
        assert not ok


# ═══════════════════════════════════════════════════════════════════════════════
# 5. АТАКИ НА SERVER (требует запущенного server.py)
# ═══════════════════════════════════════════════════════════════════════════════

# AUDIT-FIX v8.4.0: убран @pytest.mark.skip — теперь тесты запускаются автоматически.
# Если сервер не доступен — отдельные тесты skip'аются через httpx.ConnectError,
# что более информативно чем "весь класс skipped".
class TestServerAttacks:
    """
    HTTP-level атаки на server.py.
    Запускать когда сервер поднят:
        VELANTRIM_API_KEY=test-key uvicorn server:app --port 8000
        pytest tests/test_adversarial.py::TestServerAttacks -v
    """

    BASE = "http://localhost:8000"
    KEY  = os.environ.get("VELANTRIM_API_KEY", "test-key")

    @classmethod
    def setup_class(cls):
        """Skip всего класса если сервер не доступен."""
        try:
            import httpx
            httpx.get(f"{cls.BASE}/", timeout=2)
        except Exception:
            pytest.skip(
                f"Server не запущен на {cls.BASE}. "
                f"Запусти: VELANTRIM_API_KEY={cls.KEY} uvicorn server:app --port 8000"
            )

    def _headers(self, key=None):
        return {"X-Api-Key": key or self.KEY, "Content-Type": "application/json"}

    def test_no_api_key_returns_401(self):
        import httpx
        r = httpx.post(f"{self.BASE}/query", json={"query": "test"})
        assert r.status_code == 401

    def test_wrong_api_key_returns_401(self):
        import httpx
        r = httpx.post(f"{self.BASE}/query",
                       headers=self._headers("wrong-key"),
                       json={"query": "test"})
        assert r.status_code == 401

    def test_health_no_auth_required(self):
        """Health endpoint доступен без ключа."""
        import httpx
        r = httpx.get(f"{self.BASE}/health")
        assert r.status_code in (200, 503)  # degraded тоже ок

    def test_very_large_query_handled(self):
        """100K символов в query не ронят сервер."""
        import httpx
        r = httpx.post(f"{self.BASE}/query",
                       headers=self._headers(),
                       json={"query": "q" * 100_000},
                       timeout=30)
        assert r.status_code in (200, 400, 422, 500)
        # Главное — не 502/504 (сервер жив)

    def test_invalid_mode_returns_422(self):
        """Невалидный mode → 422 Unprocessable Entity."""
        import httpx
        r = httpx.post(f"{self.BASE}/query",
                       headers=self._headers(),
                       json={"query": "test", "mode": "HACKED"})
        assert r.status_code == 422

    def test_sql_injection_in_query_safe(self):
        """SQL injection в query не должен ронять сервер."""
        import httpx
        r = httpx.post(f"{self.BASE}/query",
                       headers=self._headers(),
                       json={"query": "'; DROP TABLE facts; --"},
                       timeout=30)
        assert r.status_code in (200, 400, 500)
        # Не 502/504

    def test_concurrent_health_requests(self):
        """50 параллельных /health — сервер держит."""
        import concurrent.futures

        import httpx
        def do_health():
            return httpx.get(f"{self.BASE}/health", timeout=10).status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
            codes = list(ex.map(lambda _: do_health(), range(50)))

        bad = [c for c in codes if c not in (200, 503)]
        assert not bad, f"Неожиданные коды ответа: {set(bad)}"

    def test_ingest_huge_text(self):
        """1MB текст через /ingest/text."""
        import httpx
        r = httpx.post(f"{self.BASE}/ingest/text",
                       headers=self._headers(),
                       json={"text": "word " * 200_000,
                             "source": "stress_test",
                             "confidence": 0.7},
                       timeout=60)
        assert r.status_code in (200, 201, 400, 413, 500)


# ═══════════════════════════════════════════════════════════════════════════════
# 6. NEW v8.4.0: Regression tests для всех audit-fixes
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuditFixesRegression:
    """
    Regression-тесты для каждого фикса v8.4.0.
    Эти тесты проверяют что найденные в аудите баги не вернутся.
    """

    def test_mhi_threshold_degraded_is_used(self):
        """v8.4.0: THRESHOLD_DEGRADED=0.50 больше не мёртвая константа."""
        import tempfile

        from core.memory import make_store
        from core.mhi import MHICalculator, MHIStatus
        with tempfile.TemporaryDirectory() as d:
            s = make_store(os.path.join(d, "mhi.db"))
            calc = MHICalculator(s)
            # Проверка границ — должна быть строгая трёх-зонная разбивка
            assert calc._status(0.65) == MHIStatus.HEALTHY
            assert calc._status(0.60) == MHIStatus.HEALTHY
            assert calc._status(0.55) == MHIStatus.DEGRADED  # между 0.50 и 0.60
            assert calc._status(0.50) == MHIStatus.DEGRADED
            assert calc._status(0.45) == MHIStatus.DEGRADED
            assert calc._status(0.30) == MHIStatus.DEGRADED
            assert calc._status(0.29) == MHIStatus.SAFE_MODE
            assert calc._status(0.0)  == MHIStatus.SAFE_MODE

    @pytest.mark.xfail(
        strict=True,
        reason="Naive contradiction detector даёт false positives. "
               "v8.4.0: detector='none' по умолчанию — стадия пропущена. "
               "При detector='naive' этот пример ловится как ложное противоречие. "
               "Будет закрыто через NLI cross-encoder в Sprint 2c (ATLAS-OS)."
    )
    def test_naive_contradiction_false_positive_water_temperatures(self):
        """
        Регрессия: 'вода кипит при 100°C' и 'вода не кипит при 0°C'
        не должны считаться противоречием (оба истинны при разных температурах).

        v8.4.0: naive детектор отключён по умолчанию. Этот тест
        включает его явно и проверяет известный false positive.
        Он xfail-strict — поведение naive детектора зафиксировано.
        """
        import tempfile

        import core.memory as mem
        from core.memory import make_store
        from core.truth_gate import CognitiveMode, TruthGate

        with tempfile.TemporaryDirectory() as d:
            s = make_store(os.path.join(d, "tg.db"))
            mem._GLOBAL_STORE = s
            try:
                mem.store_fact({
                    "fact_id": "boil1",
                    "claim": "вода кипит при 100 градусах",
                    "source": "physics", "confidence": 0.99,
                })
                _promote_to_validated(s, "boil1")

                gate = TruthGate(s, contradiction_detector="naive")
                new_fact = {
                    "fact_id": "boil2",
                    "claim": "вода не кипит при 0 градусах",
                    "source": "physics", "confidence": 0.99,
                    "metadata": {"evidence_refs": ["r1", "r2"]},
                }
                v = gate.evaluate(new_fact, mode=CognitiveMode.BALANCED)
                # Оба факта истинны — должно пройти. С naive — упадёт как false positive.
                assert v.passed, (
                    f"False positive в naive contradiction: водa-кипит-100 и вода-не-кипит-0 — "
                    f"не противоречие. reason={v.reason} contradictions={v.contradictions}"
                )
            finally:
                s.close()
                mem._GLOBAL_STORE = None

    def test_truth_gate_default_skips_naive_contradiction(self):
        """v8.4.0: по умолчанию contradiction-stage пропускается."""
        import tempfile

        import core.memory as mem
        from core.memory import make_store
        from core.truth_gate import CognitiveMode, TruthGate

        with tempfile.TemporaryDirectory() as d:
            s = make_store(os.path.join(d, "tg.db"))
            mem._GLOBAL_STORE = s
            try:
                mem.store_fact({
                    "fact_id": "boil1",
                    "claim": "вода кипит при 100 градусах",
                    "source": "physics", "confidence": 0.99,
                })
                _promote_to_validated(s, "boil1")

                # Default detector="none" — naive false positive не активен
                gate = TruthGate(s)
                new_fact = {
                    "fact_id": "boil2",
                    "claim": "вода не кипит при 0 градусах",
                    "source": "physics", "confidence": 0.99,
                    "metadata": {"evidence_refs": ["r1", "r2"]},
                }
                v = gate.evaluate(new_fact, mode=CognitiveMode.BALANCED)
                assert v.passed, "Default detector должен пропустить (без false positive)"
            finally:
                s.close()
                mem._GLOBAL_STORE = None

    def test_truth_gate_rejects_invalid_detector(self):
        """v8.4.0: contradiction_detector валидируется."""
        import tempfile

        from core.memory import make_store
        from core.truth_gate import TruthGate
        with tempfile.TemporaryDirectory() as d:
            s = make_store(os.path.join(d, "tg.db"))
            with pytest.raises(ValueError, match="contradiction_detector"):
                TruthGate(s, contradiction_detector="invalid_value")

    def test_truth_gate_nli_not_implemented(self):
        """v8.4.0: 'nli' detector явно поднимает NotImplementedError до Sprint 2c."""
        import tempfile

        from core.memory import make_store
        from core.truth_gate import TruthGate
        with tempfile.TemporaryDirectory() as d:
            s = make_store(os.path.join(d, "tg.db"))
            with pytest.raises(NotImplementedError, match="NLI"):
                TruthGate(s, contradiction_detector="nli")

    def test_sleep_worker_handles_async_llm_fn(self):
        """v8.4.0: SleepTimeWorker._llm_complete поддерживает async-callable."""
        import asyncio
        import tempfile

        from core.sleep_time_worker import make_sleep_time_worker

        async def async_llm(prompt: str) -> str:
            await asyncio.sleep(0)
            return "async-result"

        async def run_test():
            with tempfile.TemporaryDirectory() as d:
                w = make_sleep_time_worker(
                    project_id="async-test",
                    core_blocks_db=os.path.join(d, "b.db"),
                    notebook_db=os.path.join(d, "n.db"),
                    llm_fn=async_llm,
                )
                # До v8.4.0 это возвращало coroutine, не строку
                result = await w._llm_complete("any prompt")
                assert isinstance(result, str), f"Должен быть str, got {type(result)}"
                assert result == "async-result"

        asyncio.run(run_test())

    def test_sleep_worker_make_does_not_accept_store_kwarg(self):
        """v8.4.0 regression: make_sleep_time_worker НЕ должен принимать store=.

        Это была причина того что SleepTimeWorker молча не запускался в server.py.
        После фикса server.py убрал store= из вызова. Тест проверяет что сигнатура
        фабрики не имеет такого параметра — чтобы случайно не вернули обратно.
        """
        import inspect

        from core.sleep_time_worker import make_sleep_time_worker
        sig = inspect.signature(make_sleep_time_worker)
        assert "store" not in sig.parameters, (
            "make_sleep_time_worker() не должен принимать store= "
            "(если нужна интеграция со store — делать через явный параметр graph_store)"
        )

    def test_ngram_path_synced_with_env(self, monkeypatch):
        """v8.4.0: NGRAM_DB_PATH читается из VELANTRIM_NGRAM_DB env."""
        # Симулируем перезагрузку модуля с конкретным ENV
        custom_path = "/tmp/test_ngram_env.db"
        monkeypatch.setenv("VELANTRIM_NGRAM_DB", custom_path)
        # Импортируем заново чтобы подхватить env
        import importlib

        import core.ngram_index as ngram_mod
        importlib.reload(ngram_mod)
        assert ngram_mod.NGRAM_DB_PATH == custom_path

    def test_ngram_set_global_di(self, tmp_path):
        """v8.4.0: set_global_ngram() позволяет инжектировать singleton."""
        from core.ngram_index import NGramIndex, get_global_ngram, set_global_ngram
        custom = NGramIndex(str(tmp_path / "custom.db"))
        original = get_global_ngram()
        try:
            set_global_ngram(custom)
            assert get_global_ngram() is custom
        finally:
            set_global_ngram(original)
