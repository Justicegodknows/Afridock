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


class UserRole(enum.StrEnum):
    """Matches apps/web/src/lib/permissions.ts's `Role` type exactly, so the
    frontend's flat Role -> Capability map needs no translation layer."""

    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
