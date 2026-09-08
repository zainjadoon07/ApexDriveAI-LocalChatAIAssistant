# memory.py - Session State & Sliding Window Context Management

import time

class SessionState:
    """Stores the conversation history for a single user."""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.history: list[dict] = []  # Stores {"role": "user"|"assistant", "content": "..."}
        self.last_active = time.time()

    def add_user_message(self, message: str):
        self.history.append({"role": "user", "content": message.strip()})
        self.last_active = time.time()

    def add_assistant_message(self, message: str):
        self.history.append({"role": "assistant", "content": message.strip()})
        self.last_active = time.time()

    def get_sliding_window_history(self, max_turns: int = 8) -> list[dict]:
        """
        Sliding Window:
        1 turn = 1 user message + 1 assistant message (2 messages total).
        If history has 20 messages and max_turns=8 (16 messages),
        this returns only the LAST 16 messages.
        """
        max_messages = max_turns * 2
        return self.history[-max_messages:]

    def clear(self):
        """Resets history when user clicks 'New Chat'."""
        self.history = []
        self.last_active = time.time()


class ConversationManager:
    """Manages all active user sessions in memory."""
    def __init__(self, max_turns: int = 8):
        self.sessions: dict[str, SessionState] = {}
        self.max_turns = max_turns

    def get_or_create_session(self, session_id: str) -> SessionState:
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionState(session_id)
        return self.sessions[session_id]

    def reset_session(self, session_id: str):
        if session_id in self.sessions:
            self.sessions[session_id].clear()


# Create one global manager instance we can import anywhere
memory_manager = ConversationManager()
