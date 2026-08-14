# 📂 Velantrim File Parsers v2.0

> Универсальный модуль для парсинга 60+ форматов файлов в Velantrim ExoCortex.
> Этап 1 аудита: модернизация парсера до best-of-2026.

---

## 🎯 Что нового в v2.0

| Изменение | Эффект |
|---|---|
| 🏆 **Marker** (Surya OCR) для PDF | Лучший универсальный инструмент 2026 |
| ⚡ **PyMuPDF primary + pypdf last-resort** | Быстрый основной fallback и поддерживаемый универсальный последний fallback |
| 🚀 **faster-whisper** для аудио | 4× быстрее openai-whisper, 50% меньше RAM |
| 💾 **Lazy singleton** моделей | Whisper грузится **один раз** за процесс (раньше — на каждый файл) |
| 🗂️ **ParserRegistry** | Добавление нового парсера = одна строка |
| 🆕 **4 новых парсера** | EPUB, Email, HTML, Archive (с recursion) |
| 🆕 **PPTX парсер** | Презентации с заметками докладчика |
| 🧹 **DRY enrichment** | `_enrich_with_essence` вынесен в base (было 6 дубликатов) |
| 🔒 **SHA256** вместо BLAKE3 | Без внешних зависимостей, работает везде |
| 🛡️ **MAX_FILE_SIZE** | Защита от OOM на больших файлах |
| ⚡ **Parallel ingest** | Многопоточная обработка директорий |

---

## 📋 Поддерживаемые форматы

| Категория | Расширения |
|---|---|
| 📄 Документы | `.pdf` `.docx` `.docm` `.pptx` `.pptm` `.odp` `.rtf` |
| 📚 Книги | `.epub` `.mobi` `.azw` `.azw3` `.fb2` |
| 📝 Текст | `.txt` `.md` `.markdown` `.rst` `.json` `.jsonl` `.ndjson` `.yaml` `.yml` `.toml` |
| 💻 Код | `.py` `.js` `.ts` `.go` `.rs` `.cpp` `.java` `.html` `.css` `.sql` (всего 25+) |
| 📊 Таблицы | `.csv` `.tsv` `.xlsx` `.xls` `.ods` (multi-sheet) |
| 📧 Email | `.eml` `.msg` `.mbox` |
| 🌐 Web | `.html` `.htm` `.xhtml` `.mhtml` `.xml` |
| 🖼️ Изображения | `.jpg` `.jpeg` `.png` `.gif` `.webp` `.bmp` `.tiff` `.heic` `.heif` |
| 🎤 Аудио | `.mp3` `.wav` `.flac` `.ogg` `.m4a` `.aac` `.opus` `.aiff` `.wma` |
| 🎬 Видео | `.mp4` `.mov` `.avi` `.mkv` `.webm` `.m4v` `.ts` `.mts` |
| 📦 Архивы | `.zip` `.tar` `.gz` `.tgz` `.tar.gz` `.tar.bz2` `.7z` `.rar` |

---

## 🚀 Использование

### Парсинг одного файла

```python
from core.file_parsers import FileIngester

ingester = FileIngester()
result = ingester.ingest("document.pdf")

if result.error:
    print(f"❌ {result.error}")
else:
    print(f"✅ {result.file_type} → {result.extraction_method}")
    print(f"   Текст: {result.extracted_text[:200]}")
    print(f"   Страниц: {result.page_count}")
    print(f"   Слов: {result.word_count}")

# Готовый формат для store_fact()
fact = ingester.to_fact(result)
```

### Пакетная обработка с параллелизмом

```python
def on_progress(done, total, current):
    print(f"[{done}/{total}] {current}")

results = ingester.ingest_directory(
    "/docs",
    recursive=True,
    workers=4,
    progress=on_progress,
)

facts = ingester.to_facts(results)
```

### Прямое использование конкретного парсера

```python
from core.file_parsers.pdf_parser import PDFParser

parser = PDFParser()
result = parser.parse("report.pdf")
```

---

## ⚙️ Конфигурация через ENV

| Переменная | Дефолт | Описание |
|---|---|---|
| `VELANTRIM_MAX_FILE_SIZE_MB` | 500 | Максимальный размер файла (защита OOM) |
| `VELANTRIM_ESSENCE_SAMPLE` | 5000 | Размер выборки для EssenceExtractor |
| `VELANTRIM_DISABLE_PARSERS` | "" | Список через запятую (например `video,audio`) |
| `VELANTRIM_PDF_USE_MARKER_LLM` | false | Включает Marker `--use_llm` |
| `VELANTRIM_PDF_STRATEGY` | hi_res | Unstructured strategy (`hi_res` или `fast`) |
| `VELANTRIM_WHISPER_MODEL` | small | tiny\|base\|small\|medium\|large-v3 |
| `VELANTRIM_WHISPER_LANG` | auto | Язык транскрипции (`auto` = autodetect) |
| `VELANTRIM_WHISPER_DEVICE` | cpu | cpu\|cuda |
| `VELANTRIM_WHISPER_COMPUTE_TYPE` | int8 | int8\|float16\|float32 |
| `VELANTRIM_OCR_LANG` | rus+eng | Языки Tesseract (например `rus+eng+jpn`) |
| `VELANTRIM_OCR_OSD` | true | Автоопределение поворота |
| `VELANTRIM_VISION_LLM` | false | Vision-LLM для изображений (Sprint 2c) |
| `VELANTRIM_VIDEO_OCR` | false | OCR на кадрах видео |
| `VELANTRIM_CSV_ESSENCE` | true | Применять EssenceExtractor к CSV |

---

## 🛠️ Установка зависимостей

Все зависимости **опциональные** — модуль работает с любым подмножеством, каскад автоматически выберет лучший доступный метод.

```bash
# Минимум (всё работает на базовом уровне)
pip install pymupdf python-docx Pillow

# Рекомендуется (best of 2026)
pip install -r requirements_parsers.txt

# Для видео нужен ffmpeg
sudo apt install ffmpeg      # Ubuntu
brew install ffmpeg          # macOS
```

---

## 🏗️ Архитектура

```
core/file_parsers/
├── __init__.py                  ← публичное API
├── base.py                      ← FileParser ABC, ParseResult, ParserRegistry
├── file_ingester.py             ← главный оркестратор
│
├── pdf_parser.py        🆙      ← Marker → Docling → MinerU → Unstructured → PyMuPDF → pypdf
├── docx_parser.py       🆙      ← Unstructured → python-docx
├── pptx_parser.py       🆕      ← python-pptx → Unstructured
├── text_parser.py       🆙      ← TXT, MD, JSON, YAML, code
├── csv_parser.py        🆙      ← CSV, XLSX, ODS (multi-sheet)
├── image_parser.py      🆙      ← Vision-LLM → Tesseract → PIL
├── audio_parser.py      🆙      ← faster-whisper → openai-whisper
├── video_parser.py      🆙      ← ffmpeg → AudioParser + frames
│
├── epub_parser.py       🆕      ← EPUB, MOBI, FB2
├── email_parser.py      🆕      ← EML, MSG, MBOX
├── html_parser.py       🆕      ← trafilatura → BS4
└── archive_parser.py    🆕      ← ZIP/TAR/7Z/RAR с recursion
```

Легенда: 🆕 новый, 🆙 улучшен в v2.0

---

## 🔱 Закрытые баги из аудита

| Баг (v1.x) | Решение (v2.0) |
|---|---|
| `hashlib.blake3` — нет в stdlib | → SHA256 |
| `_enrich_with_essence` × 6 дубликатов | → Вынесен в `FileParser._enrich_with_essence` |
| Whisper грузился на каждый файл | → `_ModelSingleton` |
| OCR хардкод `lang="rus+eng"` | → ENV `VELANTRIM_OCR_LANG` |
| `essence_extractor.extract(text[:5000])` хардкод | → `self.essence_sample_size`, переопределяется |
| Нет проверки размера → OOM на больших файлах | → `_check_file()` с `max_file_size_bytes` |
| Encrypted PDF crash без понятной ошибки | → `_is_encrypted()` детекция |
| PyPDF2 в каскаде (медленный) | → PyMuPDF primary fallback; поддерживаемый `pypdf` остаётся last-resort |
| Нет parallel processing | → `ThreadPoolExecutor` в `ingest_directory()` |
| Архивы не поддерживались | → `ArchiveParser` с recursion |
