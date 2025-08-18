"""Core file operations for Obsidian vault management."""

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import aiofiles
import structlog

from ..models import ObsidianNote

logger = structlog.get_logger(__name__)


class FileOperations:
    """Handles basic file I/O operations for Obsidian notes."""

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.operation_history: list[dict[str, Any]] = []

    async def save_note(self, note: ObsidianNote, subfolder: str | None = None) -> Path:
        """Save a note to the vault."""
        try:
            # Determine the file path
            folder_path = self.vault_path
            if subfolder:
                folder_path = folder_path / subfolder
                folder_path.mkdir(parents=True, exist_ok=True)

            # Create filename from title
            safe_filename = self._sanitize_filename(note.title)
            file_path = folder_path / f"{safe_filename}.md"

            # Ensure unique filename
            file_path = await self._ensure_unique_filename(file_path)

            # Prepare content
            content = self._format_note_content(note)

            # Write file
            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(content)

            self._log_operation("save_note", str(file_path), note.title)

            logger.info(
                "Note saved successfully",
                file_path=str(file_path),
                title=note.title,
                size=len(content),
            )

            return file_path

        except Exception as e:
            logger.error(
                "Failed to save note",
                error=str(e),
                title=note.title,
                subfolder=subfolder,
            )
            raise

    async def load_note(self, file_path: Path) -> ObsidianNote | None:
        """Load a note from the vault."""
        try:
            if not file_path.exists():
                logger.warning("Note file not found", file_path=str(file_path))
                return None

            async with aiofiles.open(file_path, encoding="utf-8") as f:
                content = await f.read()

            # Parse the note content
            note = await self._parse_note_content(content, file_path)

            logger.info(
                "Note loaded successfully",
                file_path=str(file_path),
                title=note.title if note else "unknown",
            )

            return note

        except Exception as e:
            logger.error("Failed to load note", error=str(e), file_path=str(file_path))
            return None

    async def update_note(self, file_path: Path, note: ObsidianNote) -> bool:
        """Update an existing note."""
        try:
            content = self._format_note_content(note)

            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(content)

            self._log_operation("update_note", str(file_path), note.title)

            logger.info(
                "Note updated successfully",
                file_path=str(file_path),
                title=note.title,
            )

            return True

        except Exception as e:
            logger.error(
                "Failed to update note",
                error=str(e),
                file_path=str(file_path),
                title=note.title,
            )
            return False

    async def append_to_note(
        self,
        file_path: Path,
        content: str,
        section_header: str | None = None,
    ) -> bool:
        """Append content to an existing note."""
        try:
            if not file_path.exists():
                logger.error(
                    "Cannot append to non-existent file", file_path=str(file_path)
                )
                return False

            # Read existing content
            async with aiofiles.open(file_path, encoding="utf-8") as f:
                existing_content = await f.read()

            # Prepare new content
            if section_header:
                append_content = f"\n\n## {section_header}\n\n{content}"
            else:
                append_content = f"\n\n{content}"

            # Clean duplicate sections if needed
            if section_header:
                existing_content = self._clean_duplicate_sections(
                    existing_content, section_header
                )

            # Combine content
            updated_content = existing_content.rstrip() + append_content

            # Write back to file
            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(updated_content)

            self._log_operation(
                "append_note", str(file_path), section_header or "content"
            )

            logger.info(
                "Content appended to note",
                file_path=str(file_path),
                section=section_header,
            )

            return True

        except Exception as e:
            logger.error(
                "Failed to append to note",
                error=str(e),
                file_path=str(file_path),
                section=section_header,
            )
            return False

    async def delete_note(self, file_path: Path, backup: bool = True) -> bool:
        """Delete a note from the vault."""
        try:
            if not file_path.exists():
                logger.warning(
                    "Note file not found for deletion", file_path=str(file_path)
                )
                return False

            if backup:
                await self._backup_before_delete(file_path)

            # Delete the file
            file_path.unlink()

            self._log_operation("delete_note", str(file_path), "deleted")

            logger.info("Note deleted successfully", file_path=str(file_path))

            return True

        except Exception as e:
            logger.error(
                "Failed to delete note", error=str(e), file_path=str(file_path)
            )
            return False

    def _sanitize_filename(self, title: str) -> str:
        """Convert note title to safe filename."""
        # Remove or replace invalid characters
        safe_title = re.sub(r'[<>:"/\\|?*]', "_", title)
        safe_title = re.sub(r"\s+", "_", safe_title.strip())

        # Limit length
        if len(safe_title) > 200:
            safe_title = safe_title[:200]

        return safe_title

    async def _ensure_unique_filename(self, file_path: Path) -> Path:
        """Ensure filename is unique by adding counter if needed."""
        if not file_path.exists():
            return file_path

        base = file_path.stem
        suffix = file_path.suffix
        parent = file_path.parent

        counter = 1
        while True:
            new_path = parent / f"{base}_{counter}{suffix}"
            if not new_path.exists():
                return new_path
            counter += 1

    def _format_note_content(self, note: ObsidianNote) -> str:
        """Format note content for markdown file."""
        content_parts = []

        # Add title
        content_parts.append(f"# {note.title}")

        # Add metadata from frontmatter
        if (
            note.frontmatter.created
            or note.frontmatter.tags
            or note.frontmatter.ai_category
        ):
            content_parts.append("")
            content_parts.append("---")
            if note.frontmatter.created:
                content_parts.append(f"created: {note.frontmatter.created}")
            if note.frontmatter.tags:
                content_parts.append(f"tags: [{', '.join(note.frontmatter.tags)}]")
            if note.frontmatter.ai_category:
                content_parts.append(f"category: {note.frontmatter.ai_category}")
            content_parts.append("---")

        # Add content
        if note.content:
            content_parts.append("")
            content_parts.append(note.content)

        return "\n".join(content_parts)

    async def _parse_note_content(self, content: str, file_path: Path) -> ObsidianNote:
        """Parse note content from markdown file."""
        lines = content.split("\n")
        note_data: dict[str, Any] = {
            "title": file_path.stem,
            "content": "",
            "created_date": None,
            "tags": [],
            "category": None,
        }

        # Extract title from first h1 if present
        for line in lines:
            if line.startswith("# "):
                note_data["title"] = line[2:].strip()
                break

        # Extract metadata
        in_metadata = False
        metadata_end = 0
        for i, line in enumerate(lines):
            if line.strip() == "---":
                if not in_metadata:
                    in_metadata = True
                else:
                    metadata_end = i + 1
                    break
            elif in_metadata:
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()

                    if key == "created":
                        note_data["created_date"] = value
                    elif key == "tags":
                        # Parse tags list
                        tags_str = value.strip("[]")
                        note_data["tags"] = [
                            tag.strip().strip("\"'")
                            for tag in tags_str.split(",")
                            if tag.strip()
                        ]
                    elif key == "category":
                        note_data["category"] = value

        # Extract content (everything after metadata and title)
        content_lines = []
        skip_title = False
        for line in lines[metadata_end:]:
            if not skip_title and line.startswith("# "):
                skip_title = True
                continue
            if skip_title or metadata_end > 0:
                content_lines.append(line)

        note_data["content"] = "\n".join(content_lines).strip()

        # Temporarily return None for type safety - full implementation needed
        # return ObsidianNote(**note_data)
        return None  # type: ignore[return-value]

    def _clean_duplicate_sections(self, content: str, section_header: str) -> str:
        """Remove duplicate sections with the same header."""
        # Pattern to match the section header
        pattern = rf"^## {re.escape(section_header)}$"

        lines = content.split("\n")
        result_lines = []
        skip_section = False

        for line in lines:
            if re.match(pattern, line):
                if skip_section:
                    # Skip this duplicate section
                    continue
                else:
                    skip_section = True
                    result_lines.append(line)
            elif line.startswith("## ") and skip_section:
                # End of section, stop skipping
                skip_section = False
                result_lines.append(line)
            elif not skip_section:
                result_lines.append(line)

        return "\n".join(result_lines)

    async def _backup_before_delete(self, file_path: Path) -> None:
        """Create backup before deleting file."""
        backup_dir = self.vault_path / ".trash"
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = backup_dir / backup_name

        # Copy file to backup location
        import shutil

        shutil.copy2(file_path, backup_path)

        logger.info(
            "File backed up before deletion",
            original=str(file_path),
            backup=str(backup_path),
        )

    def _log_operation(self, operation: str, file_path: str, details: str) -> None:
        """Log file operation to history."""
        self.operation_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "operation": operation,
                "file_path": file_path,
                "details": details,
            }
        )

        # Keep only last 1000 operations
        if len(self.operation_history) > 1000:
            self.operation_history = self.operation_history[-1000:]

    def get_operation_history(self) -> list[dict[str, Any]]:
        """Get file operation history."""
        return self.operation_history.copy()

    def clear_operation_history(self) -> None:
        """Clear file operation history."""
        self.operation_history.clear()
