"""Test template system functionality"""

import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

# Set up test environment variables before importing modules
os.environ.update(
    {
        "DISCORD_BOT_TOKEN": "test_token",
        "DISCORD_GUILD_ID": "123456789",
        "GEMINI_API_KEY": "test_api_key",
        "OBSIDIAN_VAULT_PATH": "/tmp/test_vault",
        "CHANNEL_INBOX": "111111111",
        "CHANNEL_VOICE": "222222222",
        "CHANNEL_FILES": "333333333",
        "CHANNEL_MONEY": "444444444",
        "CHANNEL_FINANCE_REPORTS": "555555555",
        "CHANNEL_TASKS": "666666666",
        "CHANNEL_PRODUCTIVITY_REVIEWS": "777777777",
        "CHANNEL_NOTIFICATIONS": "888888888",
        "CHANNEL_COMMANDS": "999999999",
    }
)

from src.ai.models import (
    AIProcessingResult,
    CategoryResult,
    ProcessingCategory,
    SummaryResult,
    TagResult,
)
from src.obsidian.template_system import TemplateEngine


@pytest.mark.asyncio
class TestTemplateEngine:
    """Test template engine functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.template_engine = TemplateEngine(self.temp_dir)

    async def test_template_directory_creation(self):
        """Test template directory creation"""
        success = await self.template_engine.ensure_template_directory()
        assert success is True
        assert self.template_engine.template_path.exists()
        assert self.template_engine.template_path.is_dir()

    async def test_create_default_templates(self):
        """Test default template creation"""
        success = await self.template_engine.create_default_templates()
        assert success is True

        # Check if default templates were created
        templates = await self.template_engine.list_available_templates()
        expected_templates = {"daily_note", "idea_note", "meeting_note", "task_note"}
        assert set(templates) == expected_templates

        # Verify template files exist
        for template in expected_templates:
            template_file = self.template_engine.template_path / f"{template}.md"
            assert template_file.exists()

    async def test_template_loading(self):
        """Test template loading functionality"""
        # Create test template
        test_template = self.template_engine.template_path / "test_template.md"
        test_template.parent.mkdir(parents=True, exist_ok=True)

        test_content = """---
title: Test Template
tags: [test]
---

# Test Template

Hello, {{author_name}}!

Content: {{content}}

Created: {{date_format(current_date, "%Y-%m-%d")}}
"""

        with open(test_template, "w", encoding="utf-8") as f:
            f.write(test_content)

        # Load template
        loaded_content = await self.template_engine.load_template("test_template")
        assert loaded_content == test_content

        # Test caching
        cached_content = await self.template_engine.load_template("test_template")
        assert cached_content == test_content

    async def test_template_context_creation(self):
        """Test template context creation"""
        # Create test message data
        message_data = {
            "metadata": {
                "basic": {
                    "id": 123456789,
                    "author": {"display_name": "Test User", "username": "testuser"},
                    "channel": {"id": 987654321, "name": "test-channel"},
                },
                "content": {"raw_content": "This is a test message"},
                "timing": {"created_at": {"iso": "2024-01-15T12:00:00Z"}},
                "attachments": [],
            }
        }

        # Create AI result
        ai_result = AIProcessingResult(
            message_id=123456789,
            processed_at=datetime.now(),
            total_processing_time_ms=225,
            summary=SummaryResult(
                summary="Test summary",
                key_points=["Point 1", "Point 2"],
                processing_time_ms=100,
                model_used="test-model",
            ),
            tags=TagResult(
                tags=["tag1", "tag2"], processing_time_ms=50, model_used="test-model"
            ),
            category=CategoryResult(
                category=ProcessingCategory.IDEA,
                confidence_score=0.95,
                reasoning="This looks like an idea",
                processing_time_ms=75,
                model_used="test-model",
            ),
        )

        # Create context
        context = await self.template_engine.create_template_context(
            message_data, ai_result
        )

        # Verify context contains expected keys
        assert "current_date" in context
        assert "message_id" in context
        assert "content" in context
        assert "author_name" in context
        assert "channel_name" in context
        assert "ai_processed" in context
        assert "ai_summary" in context
        assert "ai_tags" in context
        assert "ai_category" in context

        # Verify values
        assert context["message_id"] == 123456789
        assert context["content"] == "This is a test message"
        assert context["author_name"] == "Test User"
        assert context["channel_name"] == "test-channel"
        assert context["ai_processed"] is True
        assert context["ai_summary"] == "Test summary"
        assert context["ai_tags"] == ["#tag1", "#tag2"]
        assert context["ai_category"] == "アイデア"

    async def test_template_rendering_basic(self):
        """Test basic template rendering"""
        template_content = """# Hello {{author_name}}!

Your message: {{content}}

AI Summary: {{ai_summary}}

Tags: {{tag_list(ai_tags)}}

Date: {{date_format(current_date, "%Y-%m-%d")}}
"""

        context = {
            "author_name": "John Doe",
            "content": "This is a test message",
            "ai_summary": "Test summary",
            "ai_tags": ["tag1", "tag2"],
            "current_date": datetime(2024, 1, 15, 12, 0, 0),
        }

        rendered = await self.template_engine.render_template(template_content, context)

        assert "Hello John Doe!" in rendered
        assert "Your message: This is a test message" in rendered
        assert "AI Summary: Test summary" in rendered
        assert "#tag1 #tag2" in rendered
        assert "Date: 2024-01-15" in rendered

    async def test_conditional_sections(self):
        """Test conditional sections in templates"""
        template_content = """# Test Template

{{#if ai_processed}}
## AI Analysis
Summary: {{ai_summary}}
{{/if}}

{{#if has_attachments}}
## Attachments
Found {{attachment_count}} attachments.
{{/if}}
"""

        # Test with AI processed
        context_with_ai = {
            "ai_processed": True,
            "ai_summary": "AI summary here",
            "has_attachments": False,
            "attachment_count": 0,
        }

        rendered = await self.template_engine.render_template(
            template_content, context_with_ai
        )
        assert "## AI Analysis" in rendered
        assert "Summary: AI summary here" in rendered
        assert "## Attachments" not in rendered

        # Test without AI
        context_without_ai = {
            "ai_processed": False,
            "has_attachments": True,
            "attachment_count": 2,
        }

        rendered = await self.template_engine.render_template(
            template_content, context_without_ai
        )
        assert "## AI Analysis" not in rendered
        assert "## Attachments" in rendered
        assert "Found 2 attachments" in rendered

    async def test_each_sections(self):
        """Test each sections in templates"""
        template_content = """# Key Points

{{#each ai_key_points}}
{{@index}}. {{@item}}
{{/each}}

## Items

{{#each items}}
- Name: {{name}}, Value: {{value}}
{{/each}}
"""

        context = {
            "ai_key_points": ["First point", "Second point", "Third point"],
            "items": [{"name": "Item1", "value": 100}, {"name": "Item2", "value": 200}],
        }

        rendered = await self.template_engine.render_template(template_content, context)

        assert "0. First point" in rendered
        assert "1. Second point" in rendered
        assert "2. Third point" in rendered
        assert "Name: Item1, Value: 100" in rendered
        assert "Name: Item2, Value: 200" in rendered

    async def test_custom_functions(self):
        """Test custom functions in templates"""
        template_content = """# Template with Functions

Truncated: {{truncate(content, 10)}}

Date formatted: {{date_format(test_date, "%B %d, %Y")}}

Tags: {{tag_list(tags)}}
"""

        context = {
            "content": "This is a very long message that should be truncated",
            "test_date": datetime(2024, 12, 25, 15, 30, 0),
            "tags": ["important", "work", "meeting"],
        }

        rendered = await self.template_engine.render_template(template_content, context)

        assert "Truncated: This is a ..." in rendered
        # The date_format function looks for the key in context, not the object itself
        # Since test_date is passed directly, it should work
        assert "December 25" in rendered  # Check for the actual formatted output
        assert "Tags: #important #work #meeting" in rendered

    async def test_frontmatter_parsing(self):
        """Test YAML frontmatter parsing"""
        template_content = """---
title: Test Note
type: idea
tags:
  - test
  - template
created: 2024-01-15
---

# Test Content

This is the main content.
"""

        frontmatter, content = self.template_engine._parse_template_content(
            template_content
        )

        assert frontmatter["title"] == "Test Note"
        assert frontmatter["type"] == "idea"
        assert frontmatter["tags"] == ["test", "template"]
        # PyYAML automatically converts dates, so we check the actual date object
        from datetime import date

        assert frontmatter["created"] == date(2024, 1, 15)
        assert "# Test Content" in content
        assert "This is the main content." in content

    async def test_note_generation_from_template(self):
        """Test complete note generation from template"""
        # Create a test template
        await self.template_engine.create_default_templates()

        # Create message data
        message_data = {
            "metadata": {
                "basic": {
                    "id": 123456789,
                    "author": {"display_name": "Test User", "username": "testuser"},
                    "channel": {"id": 987654321, "name": "test-channel"},
                },
                "content": {"raw_content": "I have a great idea for a new project!"},
                "timing": {"created_at": {"iso": "2024-01-15T12:00:00Z"}},
                "attachments": [],
            }
        }

        # Generate note from idea template
        note = await self.template_engine.generate_note_from_template(
            "idea_note", message_data
        )

        assert note is not None
        assert note.filename.endswith(".md")
        assert "idea" in note.content.lower()
        assert "great idea for a new project" in note.content
        assert note.frontmatter.ai_processed is False  # No AI result provided


def test_value_formatting():
    """Test value formatting functionality"""
    template_engine = TemplateEngine(Path("/tmp"))

    # Test None
    assert template_engine._format_value(None) == ""

    # Test boolean
    assert template_engine._format_value(True) == "true"
    assert template_engine._format_value(False) == "false"

    # Test numbers
    assert template_engine._format_value(42) == "42"
    assert template_engine._format_value(3.14) == "3.14"

    # Test datetime
    dt = datetime(2024, 1, 15, 12, 30, 45)
    assert template_engine._format_value(dt) == "2024-01-15 12:30:45"

    # Test list
    assert template_engine._format_value(["a", "b", "c"]) == "a, b, c"

    # Test string
    assert template_engine._format_value("hello") == "hello"


def test_template_loading_nonexistent():
    """Test loading non-existent template"""
    template_engine = TemplateEngine(Path("/tmp/nonexistent"))

    # This should be tested in async context, but we'll test the path logic
    assert template_engine.template_path == Path("/tmp/nonexistent/99_Meta/Templates")
