"""Refactored Obsidian file manager using modular components."""

from pathlib import Path
from typing import Any

import structlog

from .analytics import VaultStatistics
from .backup import BackupConfig, BackupManager
from .core import FileOperations, VaultManager
from .models import ObsidianNote
from .search import NoteSearch, SearchCriteria

logger = structlog.get_logger(__name__)


class ObsidianFileManager:
    """
    Refactored file manager that orchestrates modular components.

    This class now follows the Single Responsibility Principle by delegating
    specific tasks to specialized components while maintaining a unified interface.
    """

    def __init__(self, vault_path: Path | str):
        self.vault_path = Path(vault_path)

        # Initialize core components
        self.file_operations = FileOperations(self.vault_path)
        self.vault_manager = VaultManager(self.vault_path)
        self.note_search = NoteSearch(self.vault_path)
        self.statistics = VaultStatistics(self.vault_path)

        # Initialize backup manager with default config
        backup_config = BackupConfig(
            backup_directory=self.vault_path.parent / "backups",
            max_backups=10,
            compress=True,
        )
        self.backup_manager = BackupManager(self.vault_path, backup_config)

        logger.info("ObsidianFileManager initialized", vault_path=str(self.vault_path))

    # Vault Management
    async def initialize_vault(self) -> bool:
        """Initialize vault structure and templates."""
        return await self.vault_manager.initialize_vault()

    # File Operations
    async def save_note(self, note: ObsidianNote, subfolder: str | None = None) -> Path:
        """Save a note to the vault."""
        file_path = await self.file_operations.save_note(note, subfolder)
        # Invalidate stats cache when adding new notes
        self.statistics.invalidate_cache()
        return file_path

    async def load_note(self, file_path: Path) -> ObsidianNote | None:
        """Load a note from the vault."""
        return await self.file_operations.load_note(file_path)

    async def update_note(self, file_path: Path, note: ObsidianNote) -> bool:
        """Update an existing note."""
        success = await self.file_operations.update_note(file_path, note)
        if success:
            self.statistics.invalidate_cache()
        return success

    async def append_to_note(
        self,
        file_path: Path,
        content: str,
        section_header: str | None = None,
    ) -> bool:
        """Append content to an existing note."""
        success = await self.file_operations.append_to_note(
            file_path, content, section_header
        )
        if success:
            self.statistics.invalidate_cache()
        return success

    async def delete_note(self, file_path: Path, backup: bool = True) -> bool:
        """Delete a note from the vault."""
        success = await self.file_operations.delete_note(file_path, backup)
        if success:
            self.statistics.invalidate_cache()
        return success

    # Daily Note Integration (preserved for compatibility)
    async def save_or_append_daily_note(
        self,
        note: ObsidianNote,
        target_date: str | None = None,
    ) -> Path:
        """Save or append to daily note."""
        from datetime import date

        # Use provided date or today
        if target_date:
            daily_date = target_date
        else:
            daily_date = date.today().strftime("%Y-%m-%d")

        # Ensure daily notes folder exists
        daily_folder = await self.vault_manager.ensure_folder_exists("Daily Notes")
        daily_file_path = daily_folder / f"{daily_date}.md"

        if daily_file_path.exists():
            # Append to existing daily note
            await self.append_to_note(daily_file_path, note.content, note.title)
            return daily_file_path
        else:
            # Create new daily note
            from .models import NoteFrontmatter

            daily_frontmatter = NoteFrontmatter(
                obsidian_folder="Daily Notes",
                created=daily_date,
                tags=["daily-note"] + (note.frontmatter.tags or []),
                ai_category="Daily",
            )

            daily_note = ObsidianNote(
                filename=f"daily-{daily_date}.md",
                file_path=Path(f"Daily Notes/daily-{daily_date}.md"),
                frontmatter=daily_frontmatter,
                content=f"## {note.title}\n\n{note.content}",
            )
            return await self.file_operations.save_note(daily_note, "Daily Notes")

    # Search Operations
    async def search_notes(
        self,
        query: str | None = None,
        tags: list[str] | None = None,
        category: str | None = None,
        max_results: int = 50,
    ) -> list[dict[str, Any]]:
        """Search notes in the vault."""
        criteria = SearchCriteria(
            query=query,
            tags=tags,
            category=category,
            max_results=max_results,
        )

        results = await self.note_search.search_notes(criteria)

        # Convert to dict format for compatibility
        return [result.to_dict() for result in results]

    # Statistics Operations
    async def get_vault_stats(self, force_refresh: bool = False) -> dict[str, Any]:
        """Get comprehensive vault statistics."""
        stats = await self.statistics.get_vault_stats(force_refresh)
        return stats.to_dict()

    # Backup Operations
    async def backup_vault(self, description: str | None = None) -> dict[str, Any]:
        """Create a backup of the vault."""
        result = await self.backup_manager.create_backup(description)
        return result.to_dict()

    async def list_backups(self) -> list[dict[str, Any]]:
        """List available backups."""
        return await self.backup_manager.list_backups()

    async def restore_backup(self, backup_name: str) -> bool:
        """Restore vault from backup."""
        backup_path = self.backup_manager.config.backup_directory / backup_name
        success = await self.backup_manager.restore_backup(backup_path)
        if success:
            self.statistics.invalidate_cache()
        return success

    # Operation History (preserved for compatibility)
    def get_operation_history(self) -> list[dict[str, Any]]:
        """Get file operation history."""
        return self.file_operations.get_operation_history()

    def clear_operation_history(self) -> None:
        """Clear file operation history."""
        self.file_operations.clear_operation_history()

    # Helper Methods for Backwards Compatibility
    async def _ensure_vault_structure(self) -> None:
        """Ensure vault structure (backwards compatibility)."""
        await self.vault_manager.initialize_vault()

    def _invalidate_stats_cache(self) -> None:
        """Invalidate stats cache (backwards compatibility)."""
        self.statistics.invalidate_cache()

    # Configuration
    def configure_backup(self, backup_config: BackupConfig) -> None:
        """Configure backup settings."""
        self.backup_manager = BackupManager(self.vault_path, backup_config)
        logger.info(
            "Backup configuration updated",
            backup_dir=str(backup_config.backup_directory),
        )

    def configure_statistics_cache(self, cache_duration: int) -> None:
        """Configure statistics cache duration."""
        self.statistics = VaultStatistics(self.vault_path, cache_duration)
        logger.info("Statistics cache duration updated", duration=cache_duration)
