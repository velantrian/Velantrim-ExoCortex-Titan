#!/usr/bin/env python3
"""Apply exact SAFE_MODE auxiliary mutation gates; removed before final PR."""

from pathlib import Path


def replace_once(path: str, old: str, new: str, label: str) -> None:
    target = Path(path)
    source = target.read_text(encoding="utf-8")
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one marker, found {count}")
    target.write_text(source.replace(old, new, 1), encoding="utf-8")


replace_once(
    "core/goal_stack.py",
    """    ) -> Goal:\n        gid = goal_id or f\"goal_{uuid.uuid4().hex[:12]}\"\n""",
    """    ) -> Goal:\n        from core.mutation_gate import ensure_user_mutations_allowed\n\n        ensure_user_mutations_allowed(\"goal_stack.create\")\n        gid = goal_id or f\"goal_{uuid.uuid4().hex[:12]}\"\n""",
    "goal create",
)
replace_once(
    "core/goal_stack.py",
    """    def update_status(self, goal_id: str, status: str) -> Goal | None:\n        allowed = {\"active\", \"done\", \"cancelled\"}\n""",
    """    def update_status(self, goal_id: str, status: str) -> Goal | None:\n        from core.mutation_gate import ensure_user_mutations_allowed\n\n        ensure_user_mutations_allowed(\"goal_stack.update_status\")\n        allowed = {\"active\", \"done\", \"cancelled\"}\n""",
    "goal status",
)

replace_once(
    "core/console_notes.py",
    """    def create_note(\n        self,\n        content: str,\n        title: str = \"\",\n        tags: list[str] | None = None,\n    ) -> dict[str, Any]:\n        now = int(time.time() * 1000)\n""",
    """    def create_note(\n        self,\n        content: str,\n        title: str = \"\",\n        tags: list[str] | None = None,\n    ) -> dict[str, Any]:\n        from core.mutation_gate import ensure_user_mutations_allowed\n\n        ensure_user_mutations_allowed(\"console_notes.create\")\n        now = int(time.time() * 1000)\n""",
    "note create",
)
replace_once(
    "core/console_notes.py",
    """    ) -> dict[str, Any] | None:\n        note = self.get_note(note_id)\n""",
    """    ) -> dict[str, Any] | None:\n        from core.mutation_gate import ensure_user_mutations_allowed\n\n        ensure_user_mutations_allowed(\"console_notes.update\")\n        note = self.get_note(note_id)\n""",
    "note update",
)
replace_once(
    "core/console_notes.py",
    """    def delete_note(self, note_id: str) -> bool:\n        with self._connect() as conn:\n""",
    """    def delete_note(self, note_id: str) -> bool:\n        from core.mutation_gate import ensure_user_mutations_allowed\n\n        ensure_user_mutations_allowed(\"console_notes.delete\")\n        with self._connect() as conn:\n""",
    "note delete",
)

replace_once(
    "core/memory_ops.py",
    """    ) -> dict[str, Any]:\n        if not source_type.strip():\n            raise ValueError(\"source_type is required\")\n""",
    """    ) -> dict[str, Any]:\n        from core.mutation_gate import ensure_user_mutations_allowed\n\n        ensure_user_mutations_allowed(\"memory_ops.register_source\")\n        if not source_type.strip():\n            raise ValueError(\"source_type is required\")\n""",
    "memory ops register source",
)
replace_once(
    "core/memory_ops.py",
    """    ) -> dict[str, Any]:\n        if not claim.strip():\n            raise ValueError(\"claim is required\")\n""",
    """    ) -> dict[str, Any]:\n        from core.mutation_gate import ensure_user_mutations_allowed\n\n        ensure_user_mutations_allowed(\"memory_ops.enqueue_fact\")\n        if not claim.strip():\n            raise ValueError(\"claim is required\")\n""",
    "memory ops enqueue",
)
replace_once(
    "core/memory_ops.py",
    """    ) -> dict[str, Any] | None:\n        self._validate_status(status)\n        now = _now()\n""",
    """    ) -> dict[str, Any] | None:\n        from core.mutation_gate import ensure_user_mutations_allowed\n\n        ensure_user_mutations_allowed(\"memory_ops.set_inbox_status\")\n        self._validate_status(status)\n        now = _now()\n""",
    "memory ops status",
)
replace_once(
    "core/memory_ops.py",
    """    def promote_inbox_item(\n        self,\n        inbox_id: str,\n        *,\n        fact_id: str | None = None,\n        epistemic_state: str = \"Observed\",\n    ) -> dict[str, Any]:\n        item = self.get_inbox_item(inbox_id)\n""",
    """    def promote_inbox_item(\n        self,\n        inbox_id: str,\n        *,\n        fact_id: str | None = None,\n        epistemic_state: str = \"Observed\",\n    ) -> dict[str, Any]:\n        from core.mutation_gate import ensure_user_mutations_allowed\n\n        ensure_user_mutations_allowed(\"memory_ops.promote_inbox_item\")\n        item = self.get_inbox_item(inbox_id)\n""",
    "memory ops promote",
)
replace_once(
    "core/memory_ops.py",
    """    ) -> dict[str, Any]:\n        if not query.strip():\n            raise ValueError(\"query is required\")\n        tid = trace_id or f\"trace_{uuid.uuid4().hex[:12]}\"\n""",
    """    ) -> dict[str, Any]:\n        from core.mutation_gate import ensure_user_mutations_allowed\n\n        ensure_user_mutations_allowed(\"memory_ops.save_trace\")\n        if not query.strip():\n            raise ValueError(\"query is required\")\n        tid = trace_id or f\"trace_{uuid.uuid4().hex[:12]}\"\n""",
    "memory ops trace",
)
