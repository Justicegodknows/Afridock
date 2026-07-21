import enum


class ConversationStatus(enum.StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class MessageRole(enum.StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class MessageStatus(enum.StrEnum):
    NORMAL = "normal"
    ERROR = "error"
    PAUSED = "paused"
