from __future__ import annotations

from scripts.check_architecture_freeze import evaluate_freeze, scan_diff


def test_detects_new_feature_flag_without_adr() -> None:
    diff = """diff --git a/core/example.py b/core/example.py
+++ b/core/example.py
+ENABLE_AUTONOMOUS_EXAMPLE = True
"""

    allowed, findings = evaluate_freeze(diff, ("core/example.py",))

    assert allowed is False
    assert findings[0].reason == "new feature flag"


def test_authority_change_is_allowed_with_concrete_adr() -> None:
    diff = """diff --git a/core/example.py b/core/example.py
+++ b/core/example.py
+asyncio.create_task(run_worker())
"""

    allowed, findings = evaluate_freeze(
        diff,
        ("core/example.py", "docs/adr/ADR-0001-example-worker.md"),
    )

    assert allowed is True
    assert findings


def test_template_is_not_a_decision_record() -> None:
    diff = """diff --git a/core/example.py b/core/example.py
+++ b/core/example.py
+ENABLE_AUTONOMOUS_EXAMPLE = True
"""

    allowed, _ = evaluate_freeze(
        diff,
        ("core/example.py", "docs/adr/ADR-TEMPLATE.md"),
    )

    assert allowed is False


def test_docs_and_tests_are_not_scanned_as_runtime_authority() -> None:
    diff = """diff --git a/docs/example.md b/docs/example.md
+++ b/docs/example.md
+ENABLE_AUTONOMOUS_EXAMPLE
+class ExampleWorker
+diff --git a/tests/test_example.py b/tests/test_example.py
+++ b/tests/test_example.py
+asyncio.create_task(fake_worker())
"""

    assert scan_diff(diff) == ()
