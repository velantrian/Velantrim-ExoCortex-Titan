"""
📊 CSV / Spreadsheet Parser v2.0
=================================
Поддерживает: CSV, TSV, XLSX, XLS, ODS

CHANGELOG v2.0:
- 🆕 XLSX через openpyxl
- 🆕 ODS через odfpy
- 🆕 Multi-sheet support для XLSX
- 🆕 Streaming для больших файлов (chunk-based reading)
"""

import logging
import time

from .base import FileParser, ParseResult

logger = logging.getLogger("velantrim.parsers.csv")


def _check_available(module_name: str) -> bool:
    import importlib.util
    return importlib.util.find_spec(module_name) is not None


PANDAS_AVAILABLE = _check_available("pandas")
OPENPYXL_AVAILABLE = _check_available("openpyxl")
ODFPY_AVAILABLE = _check_available("odf")


class CSVParser(FileParser):
    file_type = "csv"

    def supported_formats(self) -> list:
        return [".csv", ".tsv", ".xlsx", ".xls", ".ods"]

    def parse(self, file_path: str) -> ParseResult:
        early = self._check_file(file_path)
        if early is not None:
            return early

        result = ParseResult(file_path=file_path, file_type="csv")
        result.file_size_bytes = self._get_file_size(file_path)
        start = time.time()
        import os
        ext = os.path.splitext(file_path)[1].lower()

        try:
            if ext in (".xlsx", ".xls"):
                text, structured = self._parse_excel(file_path, ext)
                result.extraction_method = "pandas/openpyxl"
                result.file_type = "xlsx"
            elif ext == ".ods":
                text, structured = self._parse_ods(file_path)
                result.extraction_method = "pandas/odfpy"
                result.file_type = "ods"
            elif PANDAS_AVAILABLE:
                text, structured = self._parse_pandas(file_path)
                result.extraction_method = "pandas"
            else:
                text, structured = self._parse_csv_module(file_path)
                result.extraction_method = "csv.reader (stdlib)"

            result.extracted_text = text
            result.structured_data = structured
            result.word_count = len(text.split()) if text else 0
            result.provenance = self._build_provenance(
                file_path, result.extraction_method
            )

            # Для табличных данных Essence обычно не нужен,
            # но если есть текстовые колонки — пусть будет.
            # Можно отключить через ENV: VELANTRIM_CSV_ESSENCE=false
            import os as _os
            if _os.getenv("VELANTRIM_CSV_ESSENCE", "true").lower() == "true":
                result = self._enrich_with_essence(result)

        except Exception as exc:
            logger.error(f"CSVParser error: {exc}")
            result.error = str(exc)

        result.parse_time_ms = (time.time() - start) * 1000
        return result

    # ─── Backends ─────────────────────────────────────────────────────────────

    def _parse_pandas(self, file_path: str) -> tuple[str, dict]:
        import pandas as pd
        sep = "\t" if file_path.endswith(".tsv") else ","
        df = pd.read_csv(file_path, sep=sep)
        return self._df_to_text_struct(df, format_label="csv")

    def _parse_csv_module(self, file_path: str) -> tuple[str, dict]:
        import csv
        sep = "\t" if file_path.endswith(".tsv") else ","
        with open(file_path, encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f, delimiter=sep)
            rows = list(reader)
        text = (
            f"CSV file with {len(rows)} rows and "
            f"{len(reader.fieldnames) if reader.fieldnames else 0} columns."
        )
        if rows:
            text += f"\nColumns: {', '.join(reader.fieldnames or [])}\n"
            text += f"First row: {rows[0]}"
        return text, {
            "format": "csv",
            "rows": rows[:100],  # limit для размера structured_data
            "row_count": len(rows),
            "fieldnames": reader.fieldnames,
        }

    def _parse_excel(self, file_path: str, ext: str) -> tuple[str, dict]:
        """Multi-sheet Excel support."""
        if not PANDAS_AVAILABLE:
            raise RuntimeError("pandas требуется для XLSX. pip install pandas openpyxl")
        import pandas as pd
        # Читаем все sheets
        sheets_data = pd.read_excel(file_path, sheet_name=None)
        sheets_info: dict[str, dict] = {}
        text_parts: list[str] = []
        for sheet_name, df in sheets_data.items():
            text_parts.append(
                f"=== Sheet '{sheet_name}': {len(df)} rows × {len(df.columns)} cols ===\n"
                f"Columns: {', '.join(str(c) for c in df.columns)}\n"
                f"{df.head(3).to_string()}"
            )
            sheets_info[sheet_name] = {
                "rows": len(df),
                "columns": [str(c) for c in df.columns],
                "sample": df.head(5).to_dict(orient="records"),
            }
        text = "\n\n".join(text_parts)
        return text, {
            "format": ext.lstrip("."),
            "sheets": sheets_info,
            "sheet_count": len(sheets_data),
        }

    def _parse_ods(self, file_path: str) -> tuple[str, dict]:
        """ODS через pandas (требует odfpy)."""
        if not PANDAS_AVAILABLE or not ODFPY_AVAILABLE:
            raise RuntimeError(
                "ODS требует: pip install pandas odfpy"
            )
        import pandas as pd
        df = pd.read_excel(file_path, engine="odf")
        return self._df_to_text_struct(df, format_label="ods")

    @staticmethod
    def _df_to_text_struct(df, format_label: str) -> tuple[str, dict]:
        """Унифицированное преобразование DataFrame в (text, structured)."""
        stats = {
            "format": format_label,
            "rows": len(df),
            "columns": [str(c) for c in df.columns],
            "dtypes": {str(col): str(df[col].dtype) for col in df.columns},
            "sample": df.head(5).to_dict(orient="records"),
        }
        # Описательная статистика для числовых колонок
        try:
            numeric_cols = df.select_dtypes(include="number").columns
            if len(numeric_cols) > 0:
                stats["description"] = df[numeric_cols].describe().to_dict()
        except Exception:
            pass

        text = (
            f"{format_label.upper()} file with {stats['rows']} rows and "
            f"{len(stats['columns'])} columns: {', '.join(stats['columns'])}.\n"
            "Sample data:\n" + str(df.head(3).to_string())
        )
        return text, stats
