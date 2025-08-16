"""
Advanced template system for Obsidian notes
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import aiofiles

from ..ai.models import AIProcessingResult
from ..utils.mixins import LoggerMixin
from .models import NoteFrontmatter, ObsidianNote, VaultFolder


class TemplateEngine(LoggerMixin):
    """高度なテンプレートエンジン"""

    def __init__(self, vault_path: Path):
        """
        Initialize template engine

        Args:
            vault_path: Obsidian vault path
        """
        self.vault_path = vault_path
        self.template_path = vault_path / "99_Meta" / "Templates"
        self.cached_templates: dict[str, str] = {}
        self.logger.info("Template engine initialized")

    async def load_template(self, template_name: str) -> str | None:
        """
        テンプレートを読み込み

        Args:
            template_name: テンプレート名（拡張子なし）

        Returns:
            テンプレート内容、見つからない場合はNone
        """
        try:
            # キャッシュから取得を試行
            if template_name in self.cached_templates:
                self.logger.debug("Template loaded from cache", template=template_name)
                return self.cached_templates[template_name]

            # ファイルからテンプレートを読み込み
            template_file = self.template_path / f"{template_name}.md"

            if not template_file.exists():
                self.logger.warning(
                    "Template file not found",
                    template=template_name,
                    path=str(template_file),
                )
                return None

            async with aiofiles.open(template_file, encoding="utf-8") as f:
                content = await f.read()

            # キャッシュに保存
            self.cached_templates[template_name] = content

            self.logger.info("Template loaded successfully", template=template_name)
            return content

        except Exception as e:
            self.logger.error(
                "Failed to load template",
                template=template_name,
                error=str(e),
                exc_info=True,
            )
            return None

    async def render_template(
        self, template_content: str, context: dict[str, Any]
    ) -> str:
        """
        テンプレートをレンダリング

        Args:
            template_content: テンプレート内容
            context: 置換用コンテキスト

        Returns:
            レンダリング済み内容
        """
        try:
            rendered = template_content

            # プレースホルダーの置換
            for placeholder, value in context.items():
                # 基本的なプレースホルダー: {{placeholder}}
                pattern = r"\{\{\s*" + re.escape(placeholder) + r"\s*\}\}"
                replacement = self._format_value(value)
                rendered = re.sub(pattern, replacement, rendered)

            # 条件付きセクション: {{#if condition}}content{{/if}}
            rendered = await self._process_conditional_sections(rendered, context)

            # 繰り返しセクション: {{#each items}}content{{/each}}
            rendered = await self._process_each_sections(rendered, context)

            # カスタム関数: {{function_name(args)}}
            rendered = await self._process_custom_functions(rendered, context)

            self.logger.debug("Template rendered successfully")
            return rendered

        except Exception as e:
            self.logger.error("Failed to render template", error=str(e), exc_info=True)
            return template_content  # 失敗した場合は元のテンプレートを返す

    def _format_value(self, value: Any) -> str:
        """値をフォーマット"""
        if value is None:
            return ""
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, int | float):
            return str(value)
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(value, list):
            return ", ".join(str(item) for item in value)
        return str(value)

    async def _process_conditional_sections(
        self, content: str, context: dict[str, Any]
    ) -> str:
        """条件付きセクションを処理"""
        pattern = r"\{\{\#if\s+(\w+)\s*\}\}(.*?)\{\{\/if\}\}"

        def replace_conditional(match: re.Match[str]) -> str:
            condition = match.group(1)
            section_content = match.group(2)

            # 条件を評価
            if condition in context and context[condition]:
                return section_content
            return ""

        return str(re.sub(pattern, replace_conditional, content, flags=re.DOTALL))

    async def _process_each_sections(
        self, content: str, context: dict[str, Any]
    ) -> str:
        """繰り返しセクションを処理"""
        pattern = r"\{\{\#each\s+(\w+)\s*\}\}(.*?)\{\{\/each\}\}"

        def replace_each(match: re.Match[str]) -> str:
            items_key = match.group(1)
            section_content = match.group(2)

            if items_key not in context:
                return ""

            items = context[items_key]
            if not isinstance(items, list):
                return ""

            results = []
            for i, item in enumerate(items):
                # 各アイテムに対して置換
                item_content = section_content

                # アイテムが辞書の場合
                if isinstance(item, dict):
                    for key, value in item.items():
                        item_pattern = r"\{\{\s*" + re.escape(key) + r"\s*\}\}"
                        item_content = re.sub(
                            item_pattern, self._format_value(value), item_content
                        )

                # インデックスとアイテム全体の置換
                item_content = re.sub(r"\{\{\s*@index\s*\}\}", str(i), item_content)
                item_content = re.sub(
                    r"\{\{\s*@item\s*\}\}", self._format_value(item), item_content
                )

                results.append(item_content)

            return "\n".join(results)

        return str(re.sub(pattern, replace_each, content, flags=re.DOTALL))

    async def _process_custom_functions(
        self, content: str, context: dict[str, Any]
    ) -> str:
        """カスタム関数を処理"""

        # 日付フォーマット: {{date_format(date, format)}}
        def date_format_func(match: re.Match[str]) -> str:
            args = match.group(1).split(",")
            if len(args) >= 2:
                date_key = args[0].strip()
                format_str = args[1].strip().strip("\"'")

                if date_key in context and isinstance(context[date_key], datetime):
                    date_value = cast("datetime", context[date_key])
                    return date_value.strftime(format_str)
            return ""

        content = re.sub(r"\{\{date_format\((.*?)\)\}\}", date_format_func, content)

        # タグリスト: {{tag_list(tags)}}
        def tag_list_func(match: re.Match[str]) -> str:
            tags_key = match.group(1).strip()
            if tags_key in context and isinstance(context[tags_key], list):
                tags = context[tags_key]
                return " ".join(f"#{tag}" for tag in tags if tag)
            return ""

        content = re.sub(r"\{\{tag_list\((.*?)\)\}\}", tag_list_func, content)

        # 文字数制限: {{truncate(text, length)}}
        def truncate_func(match: re.Match[str]) -> str:
            args = match.group(1).split(",")
            if len(args) >= 2:
                text_key = args[0].strip()
                length = int(args[1].strip())

                if text_key in context:
                    text = str(context[text_key])
                    return text[:length] + "..." if len(text) > length else text
            return ""

        content = re.sub(r"\{\{truncate\((.*?)\)\}\}", truncate_func, content)

        return content

    async def create_template_context(
        self,
        message_data: dict[str, Any],
        ai_result: AIProcessingResult | None = None,
        additional_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        テンプレート用のコンテキストを作成

        Args:
            message_data: メッセージデータ
            ai_result: AI処理結果
            additional_context: 追加のコンテキスト

        Returns:
            テンプレート置換用コンテキスト
        """
        context = {}

        # 基本情報
        now = datetime.now()
        context.update(
            {
                "current_date": now,
                "current_time": now,
                "date_iso": now.isoformat(),
                "date_ymd": now.strftime("%Y-%m-%d"),
                "date_japanese": now.strftime("%Y年%m月%d日"),
                "time_hm": now.strftime("%H:%M"),
            }
        )

        # メッセージデータから抽出
        if message_data:
            metadata = message_data.get("metadata", {})
            basic_info = metadata.get("basic", {})
            content_info = metadata.get("content", {})
            timing_info = metadata.get("timing", {})
            attachments = metadata.get("attachments", [])

            context.update(
                {
                    "message_id": basic_info.get("id"),
                    "content": content_info.get("raw_content", ""),
                    "content_length": len(content_info.get("raw_content", "")),
                    "author_name": basic_info.get("author", {}).get("display_name", ""),
                    "author_username": basic_info.get("author", {}).get("username", ""),
                    "channel_name": basic_info.get("channel", {}).get("name", ""),
                    "attachments": attachments,
                    "attachment_count": len(attachments),
                    "has_attachments": len(attachments) > 0,
                    "message_created_at": timing_info.get("created_at", {}),
                }
            )

        # AI処理結果から抽出
        if ai_result:
            context.update(
                {
                    "ai_processed": True,
                    "ai_summary": (
                        ai_result.summary.summary if ai_result.summary else ""
                    ),
                    "ai_key_points": (
                        ai_result.summary.key_points if ai_result.summary else []
                    ),
                    "ai_tags": ai_result.tags.tags if ai_result.tags else [],
                    "ai_category": (
                        ai_result.category.category.value if ai_result.category else ""
                    ),
                    "ai_confidence": (
                        ai_result.category.confidence_score
                        if ai_result.category
                        else 0.0
                    ),
                    "ai_reasoning": (
                        ai_result.category.reasoning if ai_result.category else ""
                    ),
                    "processing_time": (
                        ai_result.processing_time_ms
                        if hasattr(ai_result, "processing_time_ms")
                        else 0
                    ),
                }
            )
        else:
            context.update(
                {
                    "ai_processed": False,
                    "ai_summary": "",
                    "ai_key_points": [],
                    "ai_tags": [],
                    "ai_category": "",
                    "ai_confidence": 0.0,
                    "ai_reasoning": "",
                    "processing_time": 0,
                }
            )

        # 追加のコンテキスト
        if additional_context:
            context.update(additional_context)

        return context

    async def generate_note_from_template(
        self,
        template_name: str,
        message_data: dict[str, Any],
        ai_result: AIProcessingResult | None = None,
        additional_context: dict[str, Any] | None = None,
    ) -> ObsidianNote | None:
        """
        テンプレートからノートを生成

        Args:
            template_name: テンプレート名
            message_data: メッセージデータ
            ai_result: AI処理結果
            additional_context: 追加のコンテキスト

        Returns:
            生成されたObsidianNote、失敗した場合はNone
        """
        try:
            # テンプレートを読み込み
            template_content = await self.load_template(template_name)
            if not template_content:
                return None

            # コンテキストを作成
            context = await self.create_template_context(
                message_data, ai_result, additional_context
            )

            # テンプレートをレンダリング
            rendered_content = await self.render_template(template_content, context)

            # フロントマターと本文を分離
            frontmatter_dict, content = self._parse_template_content(rendered_content)

            # NoteFrontmatterオブジェクトを作成
            # 必要なフィールドが不足している場合はデフォルト値を設定
            self._prepare_frontmatter_dict(frontmatter_dict, context)
            frontmatter = NoteFrontmatter(**frontmatter_dict)

            # ファイル名とパスを生成
            filename = context.get(
                "filename", f"{context['date_ymd']}-{template_name}.md"
            )
            if not filename.endswith(".md"):
                filename += ".md"

            file_path = self.vault_path / VaultFolder.INBOX.value / filename

            # ObsidianNoteオブジェクトを作成
            note = ObsidianNote(
                filename=filename,
                file_path=file_path,
                frontmatter=frontmatter,
                content=content,
                created_at=datetime.now(),
                modified_at=datetime.now(),
            )

            self.logger.info(
                "Note generated from template",
                template=template_name,
                filename=filename,
            )

            return note

        except Exception as e:
            self.logger.error(
                "Failed to generate note from template",
                template=template_name,
                error=str(e),
                exc_info=True,
            )
            return None

    def _parse_template_content(self, content: str) -> tuple[dict[str, Any], str]:
        """テンプレート内容からフロントマターと本文を分離"""
        frontmatter_dict: dict[str, Any] = {}
        main_content = content

        # YAMLフロントマターの検出と解析
        frontmatter_pattern = r"^---\n(.*?)\n---\n(.*)"
        match = re.match(frontmatter_pattern, content, re.DOTALL)

        if match:
            try:
                import yaml

                frontmatter_yaml = match.group(1)
                main_content = match.group(2)
                frontmatter_dict = yaml.safe_load(frontmatter_yaml) or {}
            except ImportError:
                self.logger.warning(
                    "PyYAML not available, skipping frontmatter parsing"
                )
            except Exception as e:
                self.logger.warning("Failed to parse YAML frontmatter", error=str(e))

        return frontmatter_dict, main_content

    def _prepare_frontmatter_dict(
        self, frontmatter_dict: dict[str, Any], context: dict[str, Any]
    ) -> None:
        """フロントマターディクショナリを NoteFrontmatter モデルに適合するよう準備"""
        # 必須フィールドの設定
        if "obsidian_folder" not in frontmatter_dict:
            # note typeに基づいてフォルダを決定
            note_type = frontmatter_dict.get("type", "general")
            folder_mapping = {
                "idea": VaultFolder.IDEAS.value,
                "task": VaultFolder.PROJECTS.value,
                "meeting": VaultFolder.WORK.value,
                "daily": VaultFolder.DAILY_NOTES.value,
            }
            frontmatter_dict["obsidian_folder"] = folder_mapping.get(
                note_type, VaultFolder.INBOX.value
            )

        # 日時フィールドの文字列化
        for field in ["created", "modified"]:
            if field in frontmatter_dict:
                value = frontmatter_dict[field]
                if isinstance(value, datetime):
                    frontmatter_dict[field] = value.isoformat()
                elif not isinstance(value, str):
                    frontmatter_dict[field] = str(value)

        # 必須の created フィールドがない場合は現在時刻を設定
        if "created" not in frontmatter_dict:
            frontmatter_dict["created"] = datetime.now().isoformat()

        # modified フィールドがない場合は created と同じ値を設定
        if "modified" not in frontmatter_dict:
            frontmatter_dict["modified"] = frontmatter_dict["created"]

        # tags リストの清理 (None を除去)
        if "tags" in frontmatter_dict and isinstance(frontmatter_dict["tags"], list):
            frontmatter_dict["tags"] = [
                tag for tag in frontmatter_dict["tags"] if tag is not None and tag != ""
            ]

        # ai_tags リストの清理
        if "ai_tags" in frontmatter_dict and isinstance(
            frontmatter_dict["ai_tags"], list
        ):
            frontmatter_dict["ai_tags"] = [
                tag
                for tag in frontmatter_dict["ai_tags"]
                if tag is not None and tag != ""
            ]

    async def ensure_template_directory(self) -> bool:
        """テンプレートディレクトリが存在することを確認"""
        try:
            self.template_path.mkdir(parents=True, exist_ok=True)
            self.logger.info("Template directory ensured", path=str(self.template_path))
            return True
        except Exception as e:
            self.logger.error(
                "Failed to create template directory",
                path=str(self.template_path),
                error=str(e),
                exc_info=True,
            )
            return False

    async def list_available_templates(self) -> list[str]:
        """利用可能なテンプレート一覧を取得"""
        try:
            if not self.template_path.exists():
                await self.ensure_template_directory()
                return []

            templates = []
            for template_file in self.template_path.glob("*.md"):
                templates.append(template_file.stem)

            self.logger.debug("Available templates listed", count=len(templates))
            return sorted(templates)

        except Exception as e:
            self.logger.error("Failed to list templates", error=str(e), exc_info=True)
            return []

    async def create_default_templates(self) -> bool:
        """デフォルトテンプレートを作成"""
        try:
            await self.ensure_template_directory()

            # デフォルトテンプレートの定義
            default_templates = {
                "daily_note": self._get_daily_note_template(),
                "idea_note": self._get_idea_note_template(),
                "meeting_note": self._get_meeting_note_template(),
                "task_note": self._get_task_note_template(),
            }

            for template_name, template_content in default_templates.items():
                template_file = self.template_path / f"{template_name}.md"

                # 既存のテンプレートは上書きしない
                if template_file.exists():
                    continue

                async with aiofiles.open(template_file, "w", encoding="utf-8") as f:
                    await f.write(template_content)

                self.logger.info("Default template created", template=template_name)

            return True

        except Exception as e:
            self.logger.error(
                "Failed to create default templates", error=str(e), exc_info=True
            )
            return False

    def _get_daily_note_template(self) -> str:
        """デイリーノートテンプレート"""
        return """---
type: daily
date: {{date_ymd}}
tags:
  - daily
  - {{date_format(current_date, "%Y-%m")}}
---

# {{date_format(current_date, "%Y年%m月%d日")}} - Daily Note

## 📋 Activity Log

{{#if ai_processed}}
### AI処理済みメッセージ
- **要約**: {{ai_summary}}
- **カテゴリ**: {{ai_category}}
- **タグ**: {{tag_list(ai_tags)}}
{{/if}}

## ✅ Daily Tasks

{{#each ai_key_points}}
- [ ] {{@item}}
{{/each}}

## 📊 統計

- **処理時間**: {{processing_time}}ms
- **メッセージ数**: 1件
- **AI処理**: {{#if ai_processed}}済み{{else}}未処理{{/if}}

## 💭 振り返り

今日の振り返りをここに記録する。

## 🔗 関連リンク

- [[Yesterday|{{date_format(current_date, "%Y-%m-%d")}}]]
- [[Tomorrow|{{date_format(current_date, "%Y-%m-%d")}}]]
"""

    def _get_idea_note_template(self) -> str:
        """アイデアノートテンプレート"""
        return """---
type: idea
created: {{date_iso}}
tags:
  - idea
  - {{ai_category}}
{{#if ai_tags}}
{{#each ai_tags}}
  - {{@item}}
{{/each}}
{{/if}}
ai_processed: {{ai_processed}}
{{#if ai_processed}}
ai_summary: "{{ai_summary}}"
ai_confidence: {{ai_confidence}}
{{/if}}
---

# 💡 {{#if ai_summary}}{{truncate(ai_summary, 50)}}{{else}}新しいアイデア{{/if}}

## 📝 概要

{{#if content}}
{{content}}
{{else}}
アイデアの内容をここに記録する。
{{/if}}

{{#if ai_processed}}
## 🤖 AI分析

**要約**: {{ai_summary}}

{{#if ai_key_points}}
### 主要ポイント
{{#each ai_key_points}}
- {{@item}}
{{/each}}
{{/if}}

**分類**: {{ai_category}} (信頼度: {{ai_confidence}})

{{#if ai_reasoning}}
**根拠**: {{ai_reasoning}}
{{/if}}
{{/if}}

## 🔄 次のアクション

- [ ] アイデアを詳細化する
- [ ] 実現可能性を検討する
- [ ] 関連する情報を収集する

## 🏷️ タグ

{{tag_list(ai_tags)}}

## 📅 作成日時

{{date_format(current_date, "%Y年%m月%d日 %H:%M")}}
"""

    def _get_meeting_note_template(self) -> str:
        """会議ノートテンプレート"""
        return """---
type: meeting
date: {{date_ymd}}
tags:
  - meeting
  - {{ai_category}}
ai_processed: {{ai_processed}}
participants: []
---

# 🏢 会議メモ - {{date_format(current_date, "%Y-%m-%d")}}

## ℹ️ 基本情報

- **日時**: {{date_format(current_date, "%Y年%m月%d日 %H:%M")}}
- **参加者**:
- **場所**:

## 📋 議題

{{#if ai_key_points}}
{{#each ai_key_points}}
1. {{@item}}
{{/each}}
{{else}}
1. 議題項目1
2. 議題項目2
{{/if}}

## 💬 討議内容

{{#if content}}
{{content}}
{{else}}
会議の内容をここに記録する。
{{/if}}

{{#if ai_processed}}
## 🤖 AI要約

{{ai_summary}}

**カテゴリ**: {{ai_category}} ({{ai_confidence}})
{{/if}}

## ✅ アクションアイテム

- [ ] TODO項目1
- [ ] TODO項目2

## 📝 次回までの課題

-

## 🔗 関連資料

-
"""

    def _get_task_note_template(self) -> str:
        """タスクノートテンプレート"""
        return """---
type: task
created: {{date_iso}}
status: pending
priority: medium
tags:
  - task
  - {{ai_category}}
{{#if ai_tags}}
{{#each ai_tags}}
  - {{@item}}
{{/each}}
{{/if}}
due_date:
ai_processed: {{ai_processed}}
---

# ✅ {{#if ai_summary}}{{truncate(ai_summary, 60)}}{{else}}新しいタスク{{/if}}

## 📋 タスク詳細

{{#if content}}
{{content}}
{{else}}
タスクの詳細をここに記録する。
{{/if}}

{{#if ai_processed}}
## 🤖 AI分析

**要約**: {{ai_summary}}

{{#if ai_key_points}}
### アクションポイント
{{#each ai_key_points}}
- [ ] {{@item}}
{{/each}}
{{/if}}

**カテゴリ**: {{ai_category}} (信頼度: {{ai_confidence}})
{{/if}}

## ⏰ スケジュール

- **作成日**: {{date_format(current_date, "%Y-%m-%d")}}
- **期限**: 未設定
- **見積時間**:

## 📊 進捗

- [ ] 準備段階
- [ ] 実行中
- [ ] レビュー
- [ ] 完了

## 💭 メモ

作業中のメモや気づきをここに記録する。

## 🔗 関連リンク

-
"""
