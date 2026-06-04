"""
🌐 Server Endpoints для File Generators
==========================================
Патч для server.py — добавляет endpoints для генерации файлов.

Применение:
1. Скопируй содержимое этого файла в server.py перед if __name__ == "__main__":
2. Или импортируй и зарегистрируй: from server_patch.export_endpoints import register_export_endpoints
   register_export_endpoints(app)

Эти endpoints позволяют:
- POST /export/facts          — экспорт списка фактов в нужный формат
- POST /export/mhi            — генерация MHI dashboard
- POST /export/truthgate      — генерация TruthGate audit
- POST /export/knowledge_base — экспорт всех validated фактов
- GET  /export/formats        — список поддерживаемых форматов
- GET  /export/themes         — список доступных тем
"""

import logging
import os
import tempfile
from typing import Any

from fastapi import Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from starlette.background import BackgroundTask

logger = logging.getLogger("velantrim.server.export")


# ─── Pydantic схемы ───────────────────────────────────────────────────────────

class ExportFactsRequest(BaseModel):
    """Экспорт списка фактов в файл."""
    facts: list[dict[str, Any]] = Field(..., description="Список фактов")
    format: str = Field("pdf", description="Формат: pdf|docx|pptx|xlsx|html|md|epub")
    theme: str = Field("velantrim", description="Тема: clean|scientific|business|dark|velantrim")
    title: str = Field("Velantrim Facts Report", min_length=1, max_length=200)
    author: str = Field("Velantrim ExoCortex", max_length=200)
    include_metadata: bool = Field(True, description="Включить сводку и метаданные")


class ExportTruthGateRequest(BaseModel):
    """Экспорт TruthGate audit отчёта."""
    fact_ids: list[str] | None = Field(
        None,
        description="Список fact_id для аудита. Если None — аудит всех Hypothesized фактов.",
    )
    mode: str = Field(
        "BALANCED",
        description="Cognitive mode: PRECISION|BALANCED|EXPLORATION|CREATIVE",
    )
    format: str = Field("pdf", description="Формат отчёта")
    theme: str = Field("scientific")


class ExportKnowledgeBaseRequest(BaseModel):
    """Экспорт всей базы знаний (Validated + ImmutableCore)."""
    format: str = Field("pdf", description="Формат: pdf|docx|html|md|epub|xlsx")
    theme: str = Field("scientific")
    group_by: str = Field(
        "source",
        description="Группировка: source|epistemic_state|confidence_band|none",
    )
    title: str = Field("Velantrim Knowledge Base", max_length=200)


# ─── Регистрация endpoints ────────────────────────────────────────────────────

def register_export_endpoints(app, require_api_key=None):
    """
    Регистрирует все export endpoints в FastAPI приложении.

    Args:
        app: FastAPI инстанс
        require_api_key: dependency для API key (опционально)

    Использование в server.py:
        from server_patch.export_endpoints import register_export_endpoints
        register_export_endpoints(app, require_api_key=require_api_key)
    """
    # Зависимости
    deps = [Depends(require_api_key)] if require_api_key else []

    # ─── Lazy imports чтобы не падать при отсутствии генераторов ──────────

    def _get_exporter():
        try:
            from core.file_generators import FileExporter
            return FileExporter()
        except ImportError as exc:
            raise HTTPException(
                status_code=503,
                detail=f"file_generators не установлен: {exc}",
            )

    def _format_to_ext(format_str: str) -> str:
        """Конвертирует format в extension с точкой."""
        f = format_str.lower().strip()
        if not f.startswith("."):
            f = "." + f
        # Алиасы
        aliases = {".markdown": ".md", ".htm": ".html"}
        return aliases.get(f, f)

    def _save_and_return(spec, format_str: str, filename_base: str):
        """Генерирует временный файл и возвращает FileResponse."""
        exporter = _get_exporter()
        ext = _format_to_ext(format_str)

        # Временный файл
        with tempfile.NamedTemporaryFile(
            suffix=ext, delete=False,
        ) as tmp:
            tmp_path = tmp.name

        result = exporter.export(spec, tmp_path)
        if result.error:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
            raise HTTPException(status_code=500, detail=result.error)

        # MIME types
        mime_types = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".html": "text/html",
            ".md": "text/markdown",
            ".epub": "application/epub+zip",
            ".rtf": "application/rtf",
            ".odt": "application/vnd.oasis.opendocument.text",
        }
        media_type = mime_types.get(ext, "application/octet-stream")

        filename = f"{filename_base}{ext}"
        # FIX v8.5.3 (Claude audit + Gemini finding): /tmp leak prevention.
        # Раньше background=None с комментарием "FastAPI отдаст и удалит позже"
        # — это фактически неверно. NamedTemporaryFile(delete=False) ОСТАВЛЯЕТ
        # файл на диске после отдачи клиенту. 1000 запросов на /export = 1000
        # файлов в /tmp → переполнение диска → падение сервера.
        # Решение: BackgroundTask из starlette удаляет файл ПОСЛЕ того, как
        # FileResponse завершил отправку клиенту. missing_ok=True добавлен
        # на случай race (одновременное unlink из двух мест).
        def _cleanup_tmp(path: str) -> None:
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass  # уже удалён — нормально
            except Exception as exc:
                logger.warning("Не удалось удалить tmp %s: %s", path, exc)

        return FileResponse(
            tmp_path,
            media_type=media_type,
            filename=filename,
            background=BackgroundTask(_cleanup_tmp, tmp_path),
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # POST /export/facts — экспорт произвольного списка фактов
    # ═══════════════════════════════════════════════════════════════════════════

    @app.post("/export/facts", tags=["Export"], dependencies=deps)
    async def export_facts(req: ExportFactsRequest):
        """
        Экспорт списка фактов в указанный формат.

        Body:
            {
                "facts": [{...}, ...],
                "format": "pdf",
                "theme": "velantrim",
                "title": "Q1 Report"
            }

        Returns: бинарный файл нужного формата.
        """
        from core.file_generators import GenerationSpec
        spec = GenerationSpec.from_facts(
            facts=req.facts,
            title=req.title,
            theme=req.theme,
            include_metadata=req.include_metadata,
        )
        spec.metadata.author = req.author
        filename = req.title.replace(" ", "_").replace("/", "_")[:50] or "facts_report"
        return _save_and_return(spec, req.format, filename)

    # ═══════════════════════════════════════════════════════════════════════════
    # POST /export/mhi — MHI dashboard
    # ═══════════════════════════════════════════════════════════════════════════

    @app.post("/export/mhi", tags=["Export"], dependencies=deps)
    async def export_mhi(
        format: str = Query("pdf"),
        theme: str = Query("velantrim"),
    ):
        """
        Генерация MHI dashboard в указанном формате.

        Текущий MHI считается через MHICalculator, затем превращается
        в красивый отчёт через core.velantrim_reports.generate_mhi_report.
        """
        try:
            from core.memory import _GLOBAL_STORE
            from core.mhi import MHICalculator
            from core.velantrim_reports import generate_mhi_report

            if _GLOBAL_STORE is None:
                raise HTTPException(
                    status_code=503,
                    detail="GraphStore не инициализирован",
                )

            mhi = MHICalculator(_GLOBAL_STORE).calculate()
            spec = generate_mhi_report(mhi, theme=theme)
            from datetime import datetime
            filename = f"mhi_{datetime.now().strftime('%Y%m%d')}"
            return _save_and_return(spec, format, filename)

        except ImportError as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Модули не доступны: {exc}",
            )

    # ═══════════════════════════════════════════════════════════════════════════
    # POST /export/truthgate — TruthGate audit
    # ═══════════════════════════════════════════════════════════════════════════

    @app.post("/export/truthgate", tags=["Export"], dependencies=deps)
    async def export_truthgate(req: ExportTruthGateRequest):
        """
        Аудит TruthGate для указанных фактов (или всех Hypothesized).
        """
        try:
            from core.memory import _GLOBAL_STORE, get_all_facts, get_fact
            from core.truth_gate import CognitiveMode, TruthGate
            from core.velantrim_reports import generate_truthgate_audit

            if _GLOBAL_STORE is None:
                raise HTTPException(status_code=503, detail="Store не инициализирован")

            try:
                mode_enum = CognitiveMode[req.mode]
            except KeyError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Неизвестный mode: {req.mode}. "
                           f"Допустимые: PRECISION, BALANCED, EXPLORATION, CREATIVE",
                )

            # Собираем факты для аудита
            if req.fact_ids:
                facts = []
                for fid in req.fact_ids:
                    f = get_fact(fid)
                    if f:
                        facts.append(f)
            else:
                # Все Hypothesized — кандидаты в Validated
                facts = get_all_facts(epistemic_state="Hypothesized") or []

            if not facts:
                raise HTTPException(
                    status_code=404,
                    detail="Нет фактов для аудита",
                )

            # Прогоняем через TruthGate
            gate = TruthGate(_GLOBAL_STORE)
            verdicts = [gate.evaluate(f, mode=mode_enum) for f in facts]

            spec = generate_truthgate_audit(verdicts, theme=req.theme)
            from datetime import datetime
            filename = f"truthgate_audit_{datetime.now().strftime('%Y%m%d')}"
            return _save_and_return(spec, req.format, filename)

        except ImportError as exc:
            raise HTTPException(status_code=503, detail=str(exc))

    # ═══════════════════════════════════════════════════════════════════════════
    # POST /export/knowledge_base — все validated факты
    # ═══════════════════════════════════════════════════════════════════════════

    @app.post("/export/knowledge_base", tags=["Export"], dependencies=deps)
    async def export_knowledge_base(req: ExportKnowledgeBaseRequest):
        """
        Экспорт всей базы Validated/ImmutableCore фактов в книгу знаний.
        """
        try:
            from core.memory import get_all_facts
            from core.velantrim_reports import generate_knowledge_base

            facts = []
            for state in ("Validated", "ImmutableCore"):
                state_facts = get_all_facts(epistemic_state=state) or []
                facts.extend(state_facts)

            if not facts:
                raise HTTPException(
                    status_code=404,
                    detail="В памяти нет Validated/ImmutableCore фактов",
                )

            spec = generate_knowledge_base(
                facts=facts,
                theme=req.theme,
                group_by=req.group_by,
                title=req.title,
            )
            from datetime import datetime
            filename = f"kb_{datetime.now().strftime('%Y%m%d')}"
            return _save_and_return(spec, req.format, filename)

        except ImportError as exc:
            raise HTTPException(status_code=503, detail=str(exc))

    # ═══════════════════════════════════════════════════════════════════════════
    # GET /export/formats — список поддерживаемых форматов
    # ═══════════════════════════════════════════════════════════════════════════

    @app.get("/export/formats", tags=["Export"])
    async def list_formats():
        """Список поддерживаемых форматов экспорта."""
        try:
            from core.file_generators import FileExporter
            exporter = FileExporter()
            return {
                "extensions": exporter.get_supported_formats(),
                "categories": {
                    "documents": [".pdf", ".docx", ".rtf", ".odt"],
                    "presentations": [".pptx"],
                    "spreadsheets": [".xlsx"],
                    "web": [".html", ".htm"],
                    "markdown": [".md", ".markdown"],
                    "books": [".epub"],
                    "academic": [".tex", ".latex", ".rst"],
                },
            }
        except ImportError:
            return {"extensions": [], "error": "file_generators не установлен"}

    @app.get("/export/themes", tags=["Export"])
    async def list_themes():
        """Список доступных тем оформления."""
        try:
            from core.file_generators import THEMES
            return {
                "themes": {
                    name: {
                        "primary": f"#{theme.primary}",
                        "secondary": f"#{theme.secondary}",
                        "accent": f"#{theme.accent}",
                        "description": _theme_description(name),
                    }
                    for name, theme in THEMES.items()
                }
            }
        except ImportError:
            return {"themes": {}, "error": "file_generators не установлен"}

    logger.info("✅ Export endpoints зарегистрированы")


def _theme_description(name: str) -> str:
    descs = {
        "clean":      "Светлая, минимализм. Default для большинства задач.",
        "scientific": "Академический Times-Roman, blue-800. Для статей и аудитов.",
        "business":   "Строгий slate-900 + orange-700. Для корпоративных отчётов.",
        "dark":       "Тёмная с cyan + violet. Для презентаций в тёмном зале.",
        "velantrim":  "Фирменная cyan-600 + indigo + pink. Для внутренних отчётов.",
    }
    return descs.get(name, "")
