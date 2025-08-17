"""
Obsidian vault management module
"""

from .daily_integration import DailyNoteIntegration
from .file_manager import ObsidianFileManager
from .metadata import MetadataManager
from .models import (
    FileOperation,
    NoteFrontmatter,
    ObsidianNote,
    OperationType,
    VaultStats,
)
from .organizer import VaultOrganizer
from .template_system import TemplateEngine

# 古いテンプレートシステムは非推奨、TemplateEngineを使用
# from .templates import DailyNoteTemplate, MessageNoteTemplate, NoteTemplate

__all__ = [
    # File management
    "ObsidianFileManager",
    # Templates (new system)
    "TemplateEngine",
    # Templates (legacy - deprecated)
    # "NoteTemplate",
    # "MessageNoteTemplate",
    # "DailyNoteTemplate",
    # Models
    "ObsidianNote",
    "NoteFrontmatter",
    "VaultStats",
    "FileOperation",
    "OperationType",
    # Organization
    "VaultOrganizer",
    "MetadataManager",
    "DailyNoteIntegration",
]
