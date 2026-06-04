"""
Long-polling Telegram-бот (опционально, dev).

Запуск:
  python -m app.telegram_bot

Требует TELEGRAM_BOT_TOKEN и загруженный ENV (VELANTRIM_DB_PATH и т.д.).
"""

from __future__ import annotations

import asyncio
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("telegram_bot")


async def _poll_loop() -> None:
    from app.telegram_ingest import (
        get_bot_token,
        ingest_telegram_message,
        parse_telegram_update,
        send_telegram_reply,
    )

    token = get_bot_token()
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не задан")
        sys.exit(1)

    try:
        import httpx
    except ImportError:
        logger.error("Установите httpx: pip install httpx")
        sys.exit(1)

    offset = 0
    base = f"https://api.telegram.org/bot{token}"
    logger.info("Telegram polling запущен")

    async with httpx.AsyncClient(timeout=35.0) as client:
        while True:
            try:
                r = await client.get(
                    f"{base}/getUpdates",
                    params={"timeout": 25, "offset": offset},
                )
                r.raise_for_status()
                data = r.json()
                for upd in data.get("result") or []:
                    offset = max(offset, int(upd.get("update_id", 0)) + 1)
                    parsed = parse_telegram_update(upd)
                    if not parsed:
                        continue
                    try:
                        result = await asyncio.to_thread(
                            ingest_telegram_message,
                            parsed["text"],
                            chat_id=parsed["chat_id"],
                            user_id=parsed.get("user_id"),
                            message_id=parsed.get("message_id"),
                            username=parsed.get("username"),
                        )
                        reply = (
                            f"✅ В память: {result['fact_id']}\n"
                            f"L0: {result['raw_id']}"
                        )
                    except Exception as exc:  # noqa: BLE001
                        reply = f"❌ Ошибка ingest: {exc}"
                    await send_telegram_reply(
                        parsed["chat_id"], reply, token=token
                    )
            except Exception as exc:  # noqa: BLE001
                logger.warning("poll error: %s", exc)
                await asyncio.sleep(3)


def main() -> None:
    asyncio.run(_poll_loop())


if __name__ == "__main__":
    main()
