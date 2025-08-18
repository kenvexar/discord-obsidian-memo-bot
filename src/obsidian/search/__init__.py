"""Search functionality for Obsidian vault."""

from .note_search import NoteSearch
from .search_models import SearchCriteria, SearchResult

__all__ = ["NoteSearch", "SearchCriteria", "SearchResult"]
