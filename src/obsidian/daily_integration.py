"""
Daily note integration for Discord messages and health data
"""

import re
from datetime import date, datetime
from typing import Any

from src.utils.mixins import LoggerMixin

from .file_manager import ObsidianFileManager
from .models import ObsidianNote, VaultFolder
from .templates import DailyNoteTemplate


class DailyNoteIntegration(LoggerMixin):
    """デイリーノートの統合機能"""

    def __init__(self, file_manager: ObsidianFileManager):
        """
        Initialize daily note integration

        Args:
            file_manager: File manager instance
        """
        self.file_manager = file_manager
        self.daily_template = DailyNoteTemplate(file_manager.vault_path)
        self.logger.info("Daily note integration initialized")

    async def add_activity_log_entry(
        self, message_data: dict[str, Any], date: datetime | None = None
    ) -> bool:
        """
        activity logエントリをデイリーノートに追加

        Args:
            message_data: メッセージデータ
            date: 対象日（指定されない場合は今日）

        Returns:
            追加成功可否
        """
        try:
            if not date:
                date = datetime.now()

            # メッセージ内容の抽出
            metadata = message_data.get("metadata", {})
            content_info = metadata.get("content", {})
            timing_info = metadata.get("timing", {})
            raw_content = content_info.get("raw_content", "").strip()

            if not raw_content:
                self.logger.debug("Empty message content, skipping activity log entry")
                return False

            # デイリーノートの取得または作成
            daily_note = await self._get_or_create_daily_note(date)
            if not daily_note:
                return False

            # Activity Logセクションにエントリを追加
            timestamp = timing_info.get("created_at", {}).get(
                "iso", datetime.now().isoformat()
            )
            time_str = datetime.fromisoformat(
                timestamp.replace("Z", "+00:00")
            ).strftime("%H:%M")

            activity_entry = f"- **{time_str}** {raw_content}"

            # ノート内容を更新
            updated_content = self._add_to_section(
                daily_note.content, "## 📋 Activity Log", activity_entry
            )

            daily_note.content = updated_content
            daily_note.modified_at = datetime.now()

            # ノートを保存
            success = await self.file_manager.update_note(daily_note)

            if success:
                self.logger.info(
                    "Activity log entry added to daily note",
                    date=date.strftime("%Y-%m-%d"),
                    entry_time=time_str,
                )

            return success

        except Exception as e:
            self.logger.error(
                "Failed to add activity log entry",
                date=date.strftime("%Y-%m-%d") if date else "today",
                error=str(e),
                exc_info=True,
            )
            return False

    async def add_daily_task_entry(
        self, message_data: dict[str, Any], date: datetime | None = None
    ) -> bool:
        """
        daily taskエントリをデイリーノートに追加

        Args:
            message_data: メッセージデータ
            date: 対象日（指定されない場合は今日）

        Returns:
            追加成功可否
        """
        try:
            if not date:
                date = datetime.now()

            # メッセージ内容の抽出
            metadata = message_data.get("metadata", {})
            content_info = metadata.get("content", {})
            raw_content = content_info.get("raw_content", "").strip()

            if not raw_content:
                self.logger.debug("Empty message content, skipping daily task entry")
                return False

            # デイリーノートの取得または作成
            daily_note = await self._get_or_create_daily_note(date)
            if not daily_note:
                return False

            # タスクの解析とチェックボックス形式に変換
            task_entries = self._parse_tasks(raw_content)
            if not task_entries:
                # タスク形式でない場合は通常のエントリとして追加
                task_entries = [f"- [ ] {raw_content}"]

            # Daily Tasksセクションにエントリを追加
            updated_content = daily_note.content
            for task_entry in task_entries:
                updated_content = self._add_to_section(
                    updated_content, "## ✅ Daily Tasks", task_entry
                )

            daily_note.content = updated_content
            daily_note.modified_at = datetime.now()

            # ノートを保存
            success = await self.file_manager.update_note(daily_note)

            if success:
                self.logger.info(
                    "Daily task entries added to daily note",
                    date=date.strftime("%Y-%m-%d"),
                    task_count=len(task_entries),
                )

            return success

        except Exception as e:
            self.logger.error(
                "Failed to add daily task entry",
                date=date.strftime("%Y-%m-%d") if date else "today",
                error=str(e),
                exc_info=True,
            )
            return False

    async def _get_or_create_daily_note(self, date: datetime) -> ObsidianNote | None:
        """デイリーノートを取得または作成"""
        try:
            # 既存のデイリーノートを検索
            year = date.strftime("%Y")
            month = date.strftime("%m-%B")
            filename = f"{date.strftime('%Y-%m-%d')}.md"

            daily_note_path = (
                self.file_manager.vault_path
                / VaultFolder.DAILY_NOTES.value
                / year
                / month
                / filename
            )

            # 既存ノートの読み込みを試行
            if daily_note_path.exists():
                existing_note = await self.file_manager.load_note(daily_note_path)
                if existing_note:
                    return existing_note

            # 新しいデイリーノートを作成
            daily_stats = await self._collect_daily_stats(date)
            new_note = self.daily_template.generate_note(date, daily_stats)

            # ベースセクションを追加
            new_note.content = self._ensure_base_sections(new_note.content)

            # Vaultの初期化
            await self.file_manager.initialize_vault()

            # ノートを保存
            success = await self.file_manager.save_note(new_note)
            if success:
                self.logger.info(
                    "New daily note created", date=date.strftime("%Y-%m-%d")
                )
                return new_note

            return None

        except Exception as e:
            self.logger.error(
                "Failed to get or create daily note",
                date=date.strftime("%Y-%m-%d"),
                error=str(e),
                exc_info=True,
            )
            return None

    def _ensure_base_sections(self, content: str) -> str:
        """デイリーノートの基本セクションが存在することを確認"""
        sections_to_ensure = ["## 📋 Activity Log", "## ✅ Daily Tasks"]

        # 各セクションの存在確認と追加
        for section in sections_to_ensure:
            if section not in content:
                content += f"\n\n{section}\n\n"

        return content

    def _add_to_section(self, content: str, section_header: str, entry: str) -> str:
        """指定されたセクションにエントリを追加"""
        lines = content.split("\n")
        section_found = False
        insert_index = len(lines)

        for i, line in enumerate(lines):
            if line.strip() == section_header:
                section_found = True
                # セクションの終わりを見つける（次のセクションまたはファイル末尾）
                j = i + 1
                while j < len(lines):
                    if lines[j].strip().startswith("## ") and j > i:
                        insert_index = j
                        break
                    j += 1
                else:
                    insert_index = len(lines)
                break

        if not section_found:
            # セクションが存在しない場合は末尾に追加
            lines.extend(["", section_header, "", entry])
        else:
            # セクション内の適切な位置に挿入
            # 空行をスキップして最初の内容行を見つける
            content_start = None
            for k in range(i + 1, insert_index):
                if lines[k].strip():
                    content_start = k
                    break

            if content_start is None:
                # セクションが空の場合
                lines.insert(i + 1, "")
                lines.insert(i + 2, entry)
            else:
                # 既存の内容の後に追加
                lines.insert(insert_index, entry)

        return "\n".join(lines)

    def _parse_tasks(self, content: str) -> list[str]:
        """メッセージ内容からタスクを解析"""
        task_patterns = [
            r"^[-*+]\s+(.+)$",  # リスト形式
            r"^(\d+\.)\s+(.+)$",  # 番号付きリスト
            r"^[-*+]\s*\[[ x]\]\s+(.+)$",  # チェックボックス付き
            r"^TODO:\s*(.+)$",  # TODO形式
            r"^タスク[:：]\s*(.+)$",  # 日本語タスク形式
        ]

        tasks = []
        lines = content.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            for pattern in task_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    if len(match.groups()) == 1:
                        task_content = match.group(1).strip()
                    else:
                        task_content = match.group(2).strip()

                    # チェックボックス形式に変換
                    if not task_content.startswith(
                        "[ ]"
                    ) and not task_content.startswith("[x]"):
                        tasks.append(f"- [ ] {task_content}")
                    else:
                        tasks.append(f"- {task_content}")
                    break
            else:
                # パターンにマッチしない場合、複数行の場合は全体を1つのタスクとして扱う
                if len(lines) == 1:
                    tasks.append(f"- [ ] {line}")

        return tasks

    async def update_health_data_in_daily_note(
        self, target_date: date, health_data_markdown: str
    ) -> bool:
        """
        デイリーノートに健康データを追加/更新

        Args:
            target_date: 対象日付
            health_data_markdown: 健康データのMarkdown形式

        Returns:
            bool: 更新成功フラグ
        """
        try:
            self.logger.info(
                "Updating health data in daily note", date=target_date.isoformat()
            )

            # デイリーノートを取得または作成
            daily_note = await self._get_or_create_daily_note(
                datetime.combine(target_date, datetime.min.time())
            )
            if not daily_note:
                self.logger.error(
                    "Failed to get or create daily note for health data update"
                )
                return False

            # 既存のコンテンツを読み込み
            content = daily_note.content

            # Health Dataセクションを更新
            content = self._update_health_data_section(content, health_data_markdown)

            # ノートを更新
            updated_note = ObsidianNote(
                filename=daily_note.filename,
                file_path=daily_note.file_path,
                frontmatter=daily_note.frontmatter,
                content=content,
            )

            success = await self.file_manager.save_note(updated_note, overwrite=True)

            if success:
                self.logger.info(
                    "Successfully updated health data in daily note",
                    date=target_date.isoformat(),
                    file_path=str(
                        daily_note.file_path.relative_to(self.file_manager.vault_path)
                    ),
                )
                return True
            else:
                self.logger.error("Failed to save updated daily note with health data")
                return False

        except Exception as e:
            self.logger.error(
                "Error updating health data in daily note",
                date=target_date.isoformat(),
                error=str(e),
                exc_info=True,
            )
            return False

    def _update_health_data_section(
        self, content: str, health_data_markdown: str
    ) -> str:
        """Health Dataセクションを更新"""
        lines = content.split("\n")
        health_section_start = None
        health_section_end = len(lines)

        # Health Dataセクションを検索
        for i, line in enumerate(lines):
            if line.strip().startswith("## ") and "Health Data" in line:
                health_section_start = i
                # 次のセクションを探す
                for j in range(i + 1, len(lines)):
                    if lines[j].strip().startswith("## "):
                        health_section_end = j
                        break
                break

        if health_section_start is not None:
            # 既存のHealth Dataセクションを置換
            new_lines = (
                lines[:health_section_start]
                + health_data_markdown.split("\n")
                + [""]  # 空行を追加
                + lines[health_section_end:]
            )
        else:
            # Health Dataセクションが存在しない場合は末尾に追加
            new_lines = lines + [""] + health_data_markdown.split("\n")

        return "\n".join(new_lines)

    async def update_health_analysis_in_daily_note(
        self, target_date: date, analysis_markdown: str
    ) -> bool:
        """
        デイリーノートに健康分析結果を追加/更新

        Args:
            target_date: 対象日付
            analysis_markdown: 健康分析のMarkdown形式

        Returns:
            bool: 更新成功フラグ
        """
        try:
            self.logger.info(
                "Updating health analysis in daily note", date=target_date.isoformat()
            )

            # デイリーノートを取得または作成
            daily_note = await self._get_or_create_daily_note(
                datetime.combine(target_date, datetime.min.time())
            )
            if not daily_note:
                self.logger.error(
                    "Failed to get or create daily note for health analysis update"
                )
                return False

            # 既存のコンテンツを読み込み
            content = daily_note.content

            # Health Analysisセクションを更新
            content = self._update_health_analysis_section(content, analysis_markdown)

            # ノートを更新
            updated_note = ObsidianNote(
                filename=daily_note.filename,
                file_path=daily_note.file_path,
                frontmatter=daily_note.frontmatter,
                content=content,
            )

            success = await self.file_manager.save_note(updated_note, overwrite=True)

            if success:
                self.logger.info(
                    "Successfully updated health analysis in daily note",
                    date=target_date.isoformat(),
                    file_path=str(
                        daily_note.file_path.relative_to(self.file_manager.vault_path)
                    ),
                )
                return True
            else:
                self.logger.error(
                    "Failed to save updated daily note with health analysis"
                )
                return False

        except Exception as e:
            self.logger.error(
                "Error updating health analysis in daily note",
                date=target_date.isoformat(),
                error=str(e),
                exc_info=True,
            )
            return False

    def _update_health_analysis_section(
        self, content: str, analysis_markdown: str
    ) -> str:
        """Health Analysisセクションを更新"""
        lines = content.split("\n")
        analysis_section_start = None
        analysis_section_end = len(lines)

        # Health Analysisセクションを検索
        for i, line in enumerate(lines):
            if line.strip().startswith("## ") and "Health Analysis" in line:
                analysis_section_start = i
                # 次のセクションを探す
                for j in range(i + 1, len(lines)):
                    if lines[j].strip().startswith("## "):
                        analysis_section_end = j
                        break
                break

        if analysis_section_start is not None:
            # 既存のHealth Analysisセクションを置換
            new_lines = (
                lines[:analysis_section_start]
                + analysis_markdown.split("\n")
                + [""]  # 空行を追加
                + lines[analysis_section_end:]
            )
        else:
            # Health Analysisセクションが存在しない場合は末尾に追加
            new_lines = lines + [""] + analysis_markdown.split("\n")

        return "\n".join(new_lines)

    async def get_health_data_for_date(self, target_date: date) -> str | None:
        """
        指定日のデイリーノートからHealth Dataセクションを抽出

        Args:
            target_date: 対象日付

        Returns:
            Health Dataセクションの内容（存在しない場合はNone）
        """
        try:
            daily_note = await self._get_or_create_daily_note(
                datetime.combine(target_date, datetime.min.time())
            )
            if not daily_note:
                return None

            lines = daily_note.content.split("\n")
            health_section_start = None
            health_section_end = len(lines)

            # Health Dataセクションを検索
            for i, line in enumerate(lines):
                if line.strip().startswith("## ") and "Health Data" in line:
                    health_section_start = i
                    # 次のセクションを探す
                    for j in range(i + 1, len(lines)):
                        if lines[j].strip().startswith("## "):
                            health_section_end = j
                            break
                    break

            if health_section_start is not None:
                health_section_lines = lines[health_section_start:health_section_end]
                return "\n".join(health_section_lines).strip()

            return None

        except Exception as e:
            self.logger.error(
                "Error retrieving health data from daily note",
                date=target_date.isoformat(),
                error=str(e),
            )
            return None

    async def _collect_daily_stats(self, date: datetime) -> dict[str, Any]:
        """指定日の統計情報を収集"""
        try:
            from datetime import timedelta

            start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)

            # その日のノートを検索
            daily_notes = await self.file_manager.search_notes(
                date_from=start_date, date_to=end_date, limit=1000
            )

            stats = {
                "total_messages": len(daily_notes),
                "processed_messages": 0,
                "ai_processing_time_total": 0,
                "categories": {},
                "tags": {},
            }

            for note in daily_notes:
                # AI処理済みノートの統計
                if (
                    hasattr(note.frontmatter, "ai_processed")
                    and note.frontmatter.ai_processed
                ):
                    if isinstance(stats["processed_messages"], int):
                        stats["processed_messages"] += 1

                    if (
                        hasattr(note.frontmatter, "ai_processing_time")
                        and note.frontmatter.ai_processing_time
                        and isinstance(stats["ai_processing_time_total"], int)
                    ):
                        stats["ai_processing_time_total"] += int(
                            note.frontmatter.ai_processing_time
                        )

                # カテゴリ統計
                if (
                    hasattr(note.frontmatter, "ai_category")
                    and note.frontmatter.ai_category
                ):
                    category = str(note.frontmatter.ai_category)
                    if isinstance(stats["categories"], dict):
                        stats["categories"][category] = (
                            stats["categories"].get(category, 0) + 1
                        )

                # タグ統計
                ai_tags = getattr(note.frontmatter, "ai_tags", []) or []
                tags = getattr(note.frontmatter, "tags", []) or []
                for tag in ai_tags + tags:
                    clean_tag = str(tag).lstrip("#")
                    if isinstance(stats["tags"], dict):
                        stats["tags"][clean_tag] = stats["tags"].get(clean_tag, 0) + 1

            return stats

        except Exception as e:
            self.logger.error(
                "Failed to collect daily stats",
                date=date.strftime("%Y-%m-%d"),
                error=str(e),
                exc_info=True,
            )
            return {
                "total_messages": 0,
                "processed_messages": 0,
                "ai_processing_time_total": 0,
                "categories": {},
                "tags": {},
            }

    async def create_daily_note_if_not_exists(
        self, date: datetime | None = None
    ) -> ObsidianNote | None:
        """指定日のデイリーノートが存在しない場合に作成"""
        if not date:
            date = datetime.now()

        return await self._get_or_create_daily_note(date)
