"""P0-B post-merge hotfix — P2 regression: base/server installs (no
embeddings extra, no numpy) must be able to import ToolRegistry and the
erasure modules.

core/erasure_coordinator.py previously did `from core.embedding_store
import EmbeddingStore` at module level, and core/embedding_store.py does
`import numpy as np` at module level — so any base/server install without
numpy failed to import core.erasure_coordinator (and therefore
core.erasure and core.tool_registry's real startup path,
register_velantrim_tools()), even though numpy is only needed for the
OPTIONAL embeddings backend, never for erasure bookkeeping or tool
registration.

This must run in a genuinely fresh subprocess: numpy is installed in this
test environment and other test modules import it before this one could
run, so blocking it in-process would be a no-op once it's already cached
in sys.modules. A subprocess with `numpy` import blocked via a
`builtins.__import__` override gives an honest, clean read on whether
these modules have a REAL (not accidentally-satisfied) hard dependency on
numpy.
"""
from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest

_BLOCK_NUMPY_PRELUDE = textwrap.dedent(
    """
    import builtins, sys
    _real_import = builtins.__import__

    def _blocking_import(name, *a, **k):
        if name == "numpy" or name.startswith("numpy."):
            raise ModuleNotFoundError("No module named 'numpy' (blocked for test)")
        return _real_import(name, *a, **k)

    builtins.__import__ = _blocking_import
    sys.modules.pop("numpy", None)
    """
)

_IMPORT_MODULE = _BLOCK_NUMPY_PRELUDE + textwrap.dedent(
    """
    import {module}
    print("IMPORT_OK")
    """
)

_RUN_REGISTRATION = _BLOCK_NUMPY_PRELUDE + textwrap.dedent(
    """
    import core.tool_registry as tr

    registry = tr.ToolRegistry()
    tr.register_velantrim_tools(registry)
    print("REGISTRATION_OK")
    """
)


def _run(script: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True, timeout=30,
    )


@pytest.mark.parametrize(
    "module", ["core.erasure_coordinator", "core.erasure", "core.tool_registry"]
)
def test_module_imports_without_numpy(module):
    proc = _run(_IMPORT_MODULE.format(module=module))
    assert proc.returncode == 0, (
        f"import {module} failed with numpy unavailable:\n"
        f"stdout={proc.stdout}\nstderr={proc.stderr}"
    )
    assert "IMPORT_OK" in proc.stdout


def test_register_velantrim_tools_succeeds_without_numpy():
    """The real server-startup path (register_velantrim_tools(), which
    eagerly imports core.erasure_coordinator for its erase_fact_durable
    tool) must also succeed without numpy — a bare module import of
    core.tool_registry alone is not sufficient coverage, since its own
    erasure_coordinator import is function-local (lazy)."""
    proc = _run(_RUN_REGISTRATION)
    assert proc.returncode == 0, (
        f"register_velantrim_tools() failed with numpy unavailable:\n"
        f"stdout={proc.stdout}\nstderr={proc.stderr}"
    )
    assert "REGISTRATION_OK" in proc.stdout
