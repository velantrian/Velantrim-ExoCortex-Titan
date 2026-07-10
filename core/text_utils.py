"""
Text Utilities Module

Consolidated text processing functions used across the application.
Eliminates duplication of fingerprint, normalize_text, etc.
"""

import hashlib
import re
from typing import List


def normalize_text(text: str) -> str:
    """
    Normalize text for fingerprinting and comparison.
    
    - Strips whitespace
    - Collapses multiple spaces
    - Converts to lowercase
    
    Args:
        text: Input text
        
    Returns:
        Normalized text string
    """
    cleaned = re.sub(r"\s+", " ", text.strip())
    return cleaned.lower()


def fingerprint(text: str) -> str:
    """
    Generate SHA256 fingerprint of normalized text.
    
    Used for deduplication of episodes and documents.
    
    Args:
        text: Input text
        
    Returns:
        SHA256 hex digest
    """
    norm = normalize_text(text)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def is_hash_like(value: str) -> bool:
    """
    Check if a string looks like a UUID or hash.
    
    Used to filter out non-human-readable identifiers from display.
    
    Args:
        value: String to check
        
    Returns:
        True if string appears to be a hash/UUID
    """
    if not value:
        return True
    return bool(re.fullmatch(r"[0-9a-fA-F\-]{8,}", value))


def normalize_query(query: str) -> str:
    """
    Normalize search query for fulltext search.
    
    - Lowercase
    - Remove special characters except alphanumeric and spaces
    - Collapse whitespace
    
    Args:
        query: Search query
        
    Returns:
        Normalized query string
    """
    q = query.lower().strip()
    q = re.sub(r"[^\w\sёа-яa-z0-9-]+", " ", q, flags=re.IGNORECASE)
    q = re.sub(r"\s+", " ", q).strip()
    return q


def normalize_fact(text: str) -> str:
    """
    Normalize fact text for deduplication.
    
    Args:
        text: Fact text
        
    Returns:
        Normalized fact string
    """
    t = text.lower().strip()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[^\w\sа-яёa-z0-9]", "", t)
    return t


def truncate_text(text: str, max_length: int = 240, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with suffix.
    
    Args:
        text: Input text
        max_length: Maximum length before truncation
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated text
    """
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_length:
        return text
    return text[:max_length].strip() + suffix


def split_into_paragraphs(
    text: str, 
    max_len: int = 1800, 
    overlap: int = 200
) -> List[str]:
    """
    Split text into paragraphs with optional overlap.
    
    Splits on double newlines first, then by max_len if needed.
    
    Args:
        text: Input text
        max_len: Maximum paragraph length
        overlap: Overlap between chunks when splitting long paragraphs
        
    Returns:
        List of paragraph strings
    """
    parts = []
    for block in text.split("\n\n"):
        blk = block.strip()
        if not blk:
            continue
        if len(blk) <= max_len:
            parts.append(blk)
            continue
        # Split long blocks with overlap
        start = 0
        while start < len(blk):
            end = min(len(blk), start + max_len)
            parts.append(blk[start:end])
            if end == len(blk):
                break
            start = max(0, end - overlap)
    return parts


def split_into_semantic_chunks(
    text: str,
    max_chunk_size: int = 1500,
    min_chunk_size: int = 100
) -> List[str]:
    """
    Split text into semantic chunks based on structure.
    
    Tries to split on:
    1. Double newlines (paragraphs)
    2. Single newlines
    3. Sentences (. ! ?)
    4. Hard split at max_chunk_size
    
    Args:
        text: Input text
        max_chunk_size: Maximum chunk size
        min_chunk_size: Minimum chunk size (avoid tiny chunks)
        
    Returns:
        List of chunk strings
    """
    if len(text) <= max_chunk_size:
        return [text.strip()] if text.strip() else []
    
    chunks = []
    current_chunk = ""
    
    # First split by paragraphs
    paragraphs = text.split("\n\n")
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # If adding this paragraph exceeds max, save current and start new
        if len(current_chunk) + len(para) + 2 > max_chunk_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            # If paragraph itself is too long, split it further
            if len(para) > max_chunk_size:
                # Split by sentences
                sentences = re.split(r'(?<=[.!?])\s+', para)
                current_chunk = ""
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 1 > max_chunk_size:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        # If single sentence is too long, hard split
                        if len(sentence) > max_chunk_size:
                            for i in range(0, len(sentence), max_chunk_size):
                                chunk = sentence[i:i + max_chunk_size].strip()
                                if chunk:
                                    chunks.append(chunk)
                            current_chunk = ""
                        else:
                            current_chunk = sentence
                    else:
                        current_chunk = (current_chunk + " " + sentence).strip()
            else:
                current_chunk = para
        else:
            current_chunk = (current_chunk + "\n\n" + para).strip()
    
    # Don't forget the last chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    # Filter out chunks that are too small (merge with previous if possible)
    final_chunks: List[str] = []
    for chunk in chunks:
        if len(chunk) < min_chunk_size and final_chunks:
            # Merge with previous chunk if it won't exceed max
            if len(final_chunks[-1]) + len(chunk) + 2 <= max_chunk_size:
                final_chunks[-1] = final_chunks[-1] + "\n\n" + chunk
                continue
        if chunk:
            final_chunks.append(chunk)
    
    return final_chunks


def extract_names_from_text(text: str) -> List[str]:
    """
    Extract potential entity names from text.
    
    Looks for capitalized words that might be names.
    
    Args:
        text: Input text
        
    Returns:
        List of potential names
    """
    # Russian names (capitalized Cyrillic)
    russian_names = re.findall(r'\b[А-ЯЁ][а-яё]+\b', text)
    
    # English names (capitalized Latin)
    english_names = re.findall(r'\b[A-Z][a-z]+\b', text)
    
    # Filter common words that aren't names
    common_words = {
        'The', 'This', 'That', 'What', 'When', 'Where', 'How', 'Why',
        'Это', 'Что', 'Как', 'Где', 'Когда', 'Почему', 'Который'
    }
    
    names = []
    for name in russian_names + english_names:
        if name not in common_words and len(name) > 1:
            names.append(name)
    
    return list(set(names))


def is_correction_text(text: str) -> bool:
    """
    Determine if text is a correction/update to previous information.
    
    Looks for markers like "это ошибка", "на самом деле", etc.
    
    Args:
        text: Input text
        
    Returns:
        True if text appears to be a correction
    """
    text_lower = text.lower()
    
    correction_markers = [
        "это ошибка",
        "ошибка",
        "неправильно",
        "раньше я говорил",
        "на самом деле",
        "правильно так",
        "не сотрудничает",
        "не занимается",
        "исправление",
        "коррекция",
        "обновление",
        "теперь",
        "в действительности",
        "actually",
        "correction",
        "update",
        "wrong",
        "mistake"
    ]
    
    return any(marker in text_lower for marker in correction_markers)


# Banned/stop words for entity filtering
ENTITY_STOP_WORDS = {
    "project", "system", "data", "memory", "graph", "ai", "model",
    "user", "assistant", "chat", "summary", "context", "fact",
    "проект", "система", "данные", "память", "граф", "ии", "модель",
    "пользователь", "ассистент", "чат", "саммари", "контекст", "факт",
    "unknown", "none", "null"
}


def normalize_entity_name(name: str) -> str | None:
    """
    Normalize entity name for cross-layer linking.
    
    Args:
        name: Entity name
        
    Returns:
        Normalized name or None if invalid
    """
    if not name:
        return None
    
    # Lowercase and trim
    norm = name.lower().strip()
    
    # Cyrillic normalization
    norm = norm.replace('ё', 'е')
    
    # Remove punctuation (keep alphanumeric and spaces)
    norm = re.sub(r'[^\w\s]', '', norm)
    
    # Collapse whitespace
    norm = re.sub(r'\s+', ' ', norm).strip()
    
    # Check length and stop words
    if len(norm) < 3:
        return None
    
    if norm in ENTITY_STOP_WORDS:
        return None
    
    return norm


# ─── V8.7 HYPERIA V5.5: JSON extraction from mixed LLM output ─────────────

import json as _json

_JSON_RE = re.compile(r"\{.*?\}", re.DOTALL)


def extract_json_from_text(text: str) -> dict:
    """
    V8.7 HYPERIA V5.5 (C-2): извлечь первый валидный JSON-объект из текста LLM.

    Проблема: tiny-модели (Gemma, SmolLM) часто добавляют пояснительный текст
    ПОСЛЕ JSON-объекта. Стандартный json.loads() падает → response rejected.

    Решение: re.search первого {...} в любом месте ответа + fallback на весь текст.

    Returns:
        Распарсенный dict, или {} если JSON не найден.
    """
    if not text or not text.strip():
        return {}

    # Попробовать найти первый JSON-объект
    match = _JSON_RE.search(text)
    if match:
        try:
            return _json.loads(match.group(0))
        except _json.JSONDecodeError:
            pass

    # Fallback: попробовать весь текст
    try:
        return _json.loads(text)
    except _json.JSONDecodeError:
        return {}


def extract_json_list_from_text(text: str) -> list:
    """
    Извлечь первый валидный JSON-массив из текста LLM.
    """
    if not text or not text.strip():
        return []

    list_re = re.compile(r"\[.*?\]", re.DOTALL)
    match = list_re.search(text)
    if match:
        try:
            result = _json.loads(match.group(0))
            return result if isinstance(result, list) else []
        except _json.JSONDecodeError:
            pass
    return []
