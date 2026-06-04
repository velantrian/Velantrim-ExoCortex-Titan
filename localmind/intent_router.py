"""Intent routing for local/offline console messages."""

from __future__ import annotations

import re


def _norm(text: str) -> str:
    return " ".join((text or "").lower().split())


def intent_for(message: str) -> str:
    q = _norm(message)
    if not q:
        return "empty"
    if re.search(r"\b(hi|hello|hey|good morning|good evening)\b", q) or re.search(
        r"\b(привет|здравствуй|добрый день|доброе утро|добрый вечер)\b", q
    ):
        return "greeting"
    if re.search(r"(как ты устроен|из чего ты состоишь|что ты такое|how are you built|how do you work|what are you made of)", q):
        return "system"
    if re.search(r"(как дела|что делаешь|how are you|what are you doing)", q):
        return "status"
    if re.search(r"(проект|projects?|над чем|репозитор)", q):
        return "projects"
    if re.search(r"(заметк|notes?)", q):
        return "notes"
    if re.search(
        r"(что ты знаешь обо мне|расскажи обо мне|что думаешь обо мне|какая информация.*сохран|"
        r"что.*сохранено|what do you know about me|tell me about me|saved information|what.*saved)",
        q,
    ):
        return "about_user"
    if re.search(r"(какая информация|вся информация|что у тебя есть|what information|what do you have)", q):
        return "inventory"
    return "none"

