"""
📧 Email Parser v2.0 — Электронная почта (НОВЫЙ)
==================================================
Поддерживает: EML, MSG (Outlook), MBOX

Каскад: email (stdlib) → extract-msg → mailbox
"""

import logging
import time

from .base import FileParser, ParseResult

logger = logging.getLogger("velantrim.parsers.email")


def _check_available(module_name: str) -> bool:
    import importlib.util
    return importlib.util.find_spec(module_name) is not None


EXTRACT_MSG_AVAILABLE = _check_available("extract_msg")


class EmailParser(FileParser):
    file_type = "email"

    def supported_formats(self) -> list:
        return [".eml", ".msg", ".mbox"]

    def parse(self, file_path: str) -> ParseResult:
        early = self._check_file(file_path)
        if early is not None:
            return early

        result = ParseResult(file_path=file_path, file_type="email")
        result.file_size_bytes = self._get_file_size(file_path)
        start = time.time()
        import os
        ext = os.path.splitext(file_path)[1].lower()

        try:
            if ext == ".eml":
                text, structured = self._parse_eml(file_path)
                result.extraction_method = "email (stdlib)"
            elif ext == ".msg":
                if not EXTRACT_MSG_AVAILABLE:
                    result.error = (
                        "MSG files требуют: pip install extract-msg"
                    )
                    return result
                text, structured = self._parse_msg(file_path)
                result.extraction_method = "extract-msg"
            elif ext == ".mbox":
                text, structured = self._parse_mbox(file_path)
                result.extraction_method = "mailbox (stdlib)"
            else:
                result.error = f"Неизвестный email формат: {ext}"
                return result

            result.extracted_text = text
            result.structured_data = structured
            result.word_count = len(text.split()) if text else 0
            result.provenance = self._build_provenance(file_path, result.extraction_method)

            if text.strip():
                result = self._enrich_with_essence(result)

        except Exception as exc:
            logger.error(f"EmailParser error: {exc}")
            result.error = str(exc)

        result.parse_time_ms = (time.time() - start) * 1000
        return result

    def _parse_eml(self, file_path: str) -> tuple[str, dict]:
        """Парсинг .eml через stdlib email модуль."""
        from email import policy
        from email.parser import BytesParser

        with open(file_path, "rb") as f:
            msg = BytesParser(policy=policy.default).parse(f)

        headers = {
            "from": str(msg.get("From", "")),
            "to": str(msg.get("To", "")),
            "cc": str(msg.get("Cc", "")),
            "subject": str(msg.get("Subject", "")),
            "date": str(msg.get("Date", "")),
            "message_id": str(msg.get("Message-ID", "")),
        }

        # Body extraction (предпочитаем plain text)
        body = ""
        attachments: list[dict] = []
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                disposition = str(part.get("Content-Disposition", ""))
                if "attachment" in disposition:
                    attachments.append({
                        "filename": part.get_filename(""),
                        "content_type": ctype,
                        "size": len(part.get_payload(decode=True) or b""),
                    })
                elif ctype == "text/plain":
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        body = payload.decode(
                            part.get_content_charset() or "utf-8",
                            errors="replace",
                        )
                        break  # Первый text/plain — основной
        else:
            payload = msg.get_payload(decode=True)
            if isinstance(payload, bytes):
                body = payload.decode(
                    msg.get_content_charset() or "utf-8",
                    errors="replace",
                )

        text = (
            f"From: {headers['from']}\n"
            f"To: {headers['to']}\n"
            f"Subject: {headers['subject']}\n"
            f"Date: {headers['date']}\n\n"
            f"{body}"
        )
        return text, {
            "headers": headers,
            "body_length": len(body),
            "attachments": attachments,
            "attachment_count": len(attachments),
        }

    def _parse_msg(self, file_path: str) -> tuple[str, dict]:
        """Outlook .msg через extract-msg."""
        import extract_msg
        msg = extract_msg.Message(file_path)
        headers = {
            "from": msg.sender or "",
            "to": msg.to or "",
            "cc": msg.cc or "",
            "subject": msg.subject or "",
            "date": str(msg.date) if msg.date else "",
        }
        body = msg.body or ""
        attachments = [
            {
                "filename": att.longFilename or att.shortFilename,
                "size": len(att.data) if att.data else 0,
            }
            for att in (msg.attachments or [])
        ]
        text = (
            f"From: {headers['from']}\nTo: {headers['to']}\n"
            f"Subject: {headers['subject']}\nDate: {headers['date']}\n\n{body}"
        )
        return text, {
            "headers": headers,
            "body_length": len(body),
            "attachments": attachments,
        }

    def _parse_mbox(self, file_path: str) -> tuple[str, dict]:
        """MBOX через stdlib mailbox."""
        import mailbox
        mbox = mailbox.mbox(file_path)
        messages_info: list[dict] = []
        text_parts: list[str] = []
        for i, msg in enumerate(mbox):
            if i >= 100:  # Лимит для большого mbox
                break
            messages_info.append({
                "subject": msg.get("Subject", ""),
                "from": msg.get("From", ""),
                "date": msg.get("Date", ""),
            })
            text_parts.append(
                f"=== Email #{i+1} ===\n"
                f"From: {msg.get('From', '')}\n"
                f"Subject: {msg.get('Subject', '')}\n"
            )
        return "\n".join(text_parts), {
            "message_count": len(messages_info),
            "messages_preview": messages_info[:20],
        }
