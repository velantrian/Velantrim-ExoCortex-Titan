"""
L0 Conversation Buffer - RAM storage for recent conversation messages.
Maintains conversation context without database queries.
"""

import uuid
from collections import deque
from datetime import UTC, datetime
from typing import Any

# Global storage: user_id -> ConversationBuffer
_conversation_buffers: dict[str, "ConversationBuffer"] = {}

class ConversationBuffer:
    """
    RAM buffer for conversation messages per user.
    Maintains recent messages to preserve conversation context.
    """

    def __init__(self, max_messages: int = 12) -> None:
        self.conversation_id = str(uuid.uuid4())[:8]
        self.buffer: deque[dict[str, Any]] = deque(maxlen=max_messages)
        self.turn_index = 0
        self.last_activity = datetime.now(UTC)

    def add_message(self, role: str, content: str) -> int:
        """Add message to buffer and return current turn index."""
        self.buffer.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now(UTC)
        })
        self.last_activity = datetime.now(UTC)
        return self.turn_index

    def add_turn(self, user_message: str, assistant_response: str) -> int:
        """Add complete turn (user + assistant) and increment turn index."""
        self.add_message('user', user_message)
        self.add_message('assistant', assistant_response)
        self.turn_index += 1
        return self.turn_index

    def get_recent_messages(self, limit: int = 6) -> list[dict[str, Any]]:
        """Get recent messages for context (without timestamps)."""
        recent = list(self.buffer)[-limit:]
        return [{'role': msg['role'], 'content': msg['content']} for msg in recent]

    def get_recent_turns(self, num_turns: int = 3) -> list[dict[str, str]]:
        """Get recent complete turns (user + assistant pairs)."""
        messages = list(self.buffer)
        turns: list[dict[str, str]] = []

        # Process messages in pairs (user, assistant)
        i = 0
        while i < len(messages) - 1 and len(turns) < num_turns:
            if (messages[i]['role'] == 'user' and
                messages[i + 1]['role'] == 'assistant'):
                turns.append({
                    'user': messages[i]['content'],
                    'assistant': messages[i + 1]['content']
                })
                i += 2
            else:
                i += 1

        return turns

    def should_create_summary(self) -> bool:
        """Check if we should create a summary (every 10 turns)."""
        return self.turn_index > 0 and self.turn_index % 10 == 0

    def get_last_n_turns(self, n: int) -> list[tuple[str, str]]:
        """Get last N complete turns as (uuid, content) for summarization."""
        turns = self.get_recent_turns(n)
        # Generate UUIDs for turns (simplified - in real implementation would track UUIDs)
        return [(str(uuid.uuid4()), f"User: {t['user']}\nAssistant: {t['assistant']}") for t in turns]

def get_user_conversation_buffer(user_id: str) -> ConversationBuffer:
    """Get or create conversation buffer for user."""
    if user_id not in _conversation_buffers:
        _conversation_buffers[user_id] = ConversationBuffer()
    return _conversation_buffers[user_id]

def cleanup_inactive_buffers(max_age_hours: int = 24):
    """Remove conversation buffers for inactive users."""
    now = datetime.now(UTC)
    to_remove = []

    for user_id, buffer in _conversation_buffers.items():
        age_hours = (now - buffer.last_activity).total_seconds() / 3600
        if age_hours > max_age_hours:
            to_remove.append(user_id)

    for user_id in to_remove:
        del _conversation_buffers[user_id]

    return len(to_remove)

def clear_user_buffer(user_id: str) -> int:
    """
    Clear conversation buffer for a specific user.
    Returns number of cleared messages (if any).
    """
    if user_id in _conversation_buffers:
        count = len(_conversation_buffers[user_id].buffer)
        del _conversation_buffers[user_id]
        return count
    return 0
