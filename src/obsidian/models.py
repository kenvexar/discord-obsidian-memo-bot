"""
Obsidian vault data models
"""

import json
import re
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OperationType(Enum):
    """ファイル操作の種類"""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    MOVE = "move"
    ARCHIVE = "archive"


class NoteStatus(Enum):
    """ノートのステータス"""

    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"
    TEMPLATE = "template"


class VaultFolder(Enum):
    """Vault 内のフォルダ構造"""

    # 基本フォルダ（ CLAUDE.md + docs/user/examples.md に基づく）
    INBOX = "00_Inbox"
    PROJECTS = "01_Projects"
    DAILY_NOTES = "02_DailyNotes"
    IDEAS = "03_Ideas"
    ARCHIVE = "04_Archive"
    RESOURCES = "05_Resources"
    FINANCE = "06_Finance"
    TASKS = "07_Tasks"
    HEALTH = "08_Health"
    KNOWLEDGE = "09_Knowledge"  # チーム知識・ナレッジベース

    # アタッチメント用フォルダ
    ATTACHMENTS = "10_Attachments"
    IMAGES = "10_Attachments/Images"
    AUDIO = "10_Attachments/Audio"
    DOCUMENTS = "10_Attachments/Documents"
    OTHER_FILES = "10_Attachments/Other"

    # メタデータフォルダ
    META = "99_Meta"
    TEMPLATES = "99_Meta/Templates"

    # サブフォルダ定義（階層構造の改善）
    # Inbox subfolders
    INBOX_UNPROCESSED = "00_Inbox/unprocessed"
    INBOX_PENDING = "00_Inbox/pending"
    INBOX_STAGED = "00_Inbox/staged"

    # Projects subfolders
    PROJECTS_ACTIVE = "01_Projects/active"
    PROJECTS_PLANNING = "01_Projects/planning"
    PROJECTS_ON_HOLD = "01_Projects/on-hold"
    PROJECTS_COMPLETED = "01_Projects/completed"

    # Finance subfolders
    FINANCE_EXPENSES = "06_Finance/expenses"
    FINANCE_INCOME = "06_Finance/income"
    FINANCE_SUBSCRIPTIONS = "06_Finance/subscriptions"
    FINANCE_BUDGETS = "06_Finance/budgets"
    FINANCE_REPORTS = "06_Finance/reports"

    # Tasks subfolders
    TASKS_BACKLOG = "07_Tasks/backlog"
    TASKS_ACTIVE = "07_Tasks/active"
    TASKS_WAITING = "07_Tasks/waiting"
    TASKS_COMPLETED = "07_Tasks/completed"
    TASKS_TEMPLATES = "07_Tasks/templates"

    # Health subfolders
    HEALTH_ACTIVITIES = "08_Health/activities"
    HEALTH_SLEEP = "08_Health/sleep"
    HEALTH_WELLNESS = "08_Health/wellness"
    HEALTH_MEDICAL = "08_Health/medical"
    HEALTH_ANALYTICS = "08_Health/analytics"

    # Knowledge subfolders （ team-knowledge 対応）
    KNOWLEDGE_TECHNICAL = "09_Knowledge/technical"
    KNOWLEDGE_PROCESSES = "09_Knowledge/processes"
    KNOWLEDGE_TOOLS = "09_Knowledge/tools"
    KNOWLEDGE_LEARNINGS = "09_Knowledge/learnings"


class NoteFrontmatter(BaseModel):
    """Obsidian ノートのフロントマター"""

    # Discord 関連情報
    discord_message_id: int | None = None
    discord_channel: str | None = None
    discord_author: str | None = None
    discord_author_id: int | None = None
    discord_timestamp: str | None = None
    discord_guild: str | None = None

    # AI 処理結果
    ai_processed: bool = False
    ai_processing_time: int | None = None
    ai_summary: str | None = None
    ai_tags: list[str] = Field(default_factory=list)
    ai_category: str | None = None
    ai_subcategory: str | None = None
    ai_confidence: float | None = None

    # Obsidian 管理情報
    created: str = Field(default_factory=lambda: datetime.now().isoformat())
    modified: str = Field(default_factory=lambda: datetime.now().isoformat())
    status: NoteStatus = NoteStatus.ACTIVE
    obsidian_folder: str
    source_type: str = "discord_message"

    # 階層構造メタデータ
    vault_hierarchy: str | None = None
    organization_level: str | None = None

    # メタデータ
    tags: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)
    cssclass: str | None = "discord-note"

    # 統計情報（日次ノート用）
    total_messages: int | None = None
    processed_messages: int | None = None
    ai_processing_time_total: int | None = None
    categories: dict[str, int] | None = None

    model_config = ConfigDict()

    @field_validator("ai_tags")
    @classmethod
    def validate_ai_tags(cls, v: list[str]) -> list[str]:
        """AI タグの正規化"""
        validated_tags = []
        for tag in v:
            if tag and isinstance(tag, str):
                # #を確実に付ける
                if not tag.startswith("#"):
                    tag = f"#{tag}"
                validated_tags.append(tag)
        return validated_tags

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """タグの正規化（#なし）"""
        validated_tags = []
        for tag in v:
            if tag and isinstance(tag, str):
                # #を除去
                clean_tag = tag.lstrip("#")
                if clean_tag:
                    validated_tags.append(clean_tag)
        return validated_tags


class ObsidianNote(BaseModel):
    """Obsidian ノートの完全な表現"""

    filename: str
    file_path: Path
    frontmatter: NoteFrontmatter
    content: str
    created_at: datetime = Field(default_factory=datetime.now)
    modified_at: datetime = Field(default_factory=datetime.now)

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """ファイル名の検証"""
        if not v.endswith(".md"):
            raise ValueError("Filename must end with .md")

        # 無効な文字をチェック
        invalid_chars = r'[<>:"/\\|?*]'
        if re.search(invalid_chars, v):
            raise ValueError(f"Filename contains invalid characters: {v}")

        return v

    @property
    def title(self) -> str:
        """ファイル名からタイトルを抽出"""
        # YYYYMMDDHHMM_[カテゴリ]_[タイトル].md から [タイトル] を抽出
        basename = self.filename.replace(".md", "")
        parts = basename.split("_", 2)

        if len(parts) >= 3:
            return parts[2]  # タイトル部分
        if len(parts) == 2:
            return parts[1]  # カテゴリなしの場合
        return basename  # フォーマットが異なる場合

    @property
    def category_from_filename(self) -> str | None:
        """ファイル名からカテゴリを抽出"""
        basename = self.filename.replace(".md", "")
        parts = basename.split("_", 2)

        if len(parts) >= 2 and not parts[1].isdigit():
            return parts[1]  # カテゴリ部分

        return None

    def to_markdown(self) -> str:
        """完全な Markdown ファイル内容を生成"""
        frontmatter_yaml = self._frontmatter_to_yaml()

        return f"""---
{frontmatter_yaml}---

{self.content}"""

    def _frontmatter_to_yaml(self) -> str:
        """フロントマターを YAML 形式に変換"""
        import yaml

        # Pydantic モデルを辞書に変換
        data = self.frontmatter.model_dump(exclude_none=True)

        # Enum を Value に変換
        if "status" in data:
            data["status"] = (
                data["status"].value
                if hasattr(data["status"], "value")
                else str(data["status"])
            )

        return yaml.dump(
            data, default_flow_style=False, allow_unicode=True, sort_keys=False
        )


class FileOperation(BaseModel):
    """ファイル操作の記録"""

    operation_type: OperationType
    file_path: Path
    timestamp: datetime = Field(default_factory=datetime.now)
    success: bool = True
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True)


class VaultStats(BaseModel):
    """Vault 統計情報"""

    total_notes: int = 0
    total_size_bytes: int = 0
    notes_by_category: dict[str, int] = Field(default_factory=dict)
    notes_by_folder: dict[str, int] = Field(default_factory=dict)
    notes_by_status: dict[str, int] = Field(default_factory=dict)

    # 期間別統計
    notes_created_today: int = 0
    notes_created_this_week: int = 0
    notes_created_this_month: int = 0

    # AI 処理統計
    ai_processed_notes: int = 0
    total_ai_processing_time: int = 0
    average_ai_processing_time: float = 0.0

    # タグ統計
    most_common_tags: dict[str, int] = Field(default_factory=dict)

    last_updated: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict()


class AttachmentInfo(BaseModel):
    """添付ファイル情報"""

    original_filename: str
    saved_filename: str
    file_path: Path
    file_size: int
    content_type: str | None = None
    discord_url: str
    vault_folder: VaultFolder

    created_at: datetime = Field(default_factory=datetime.now)
    linked_note_path: Path | None = None

    model_config = ConfigDict(use_enum_values=True)


class FolderMapping:
    """フォルダマッピングの管理"""

    # カテゴリベースのマッピング（改善版）
    CATEGORY_FOLDER_MAPPING = {
        "仕事": VaultFolder.PROJECTS,
        "学習": VaultFolder.KNOWLEDGE,  # LEARNING → KNOWLEDGE に変更
        "プロジェクト": VaultFolder.PROJECTS,
        "生活": VaultFolder.DAILY_NOTES,
        "アイデア": VaultFolder.IDEAS,
        "金融": VaultFolder.FINANCE,
        "タスク": VaultFolder.TASKS,
        "健康": VaultFolder.HEALTH,
        "その他": VaultFolder.INBOX,
        # 英語カテゴリも追加
        "work": VaultFolder.PROJECTS,
        "learning": VaultFolder.KNOWLEDGE,  # LEARNING → KNOWLEDGE に変更
        "knowledge": VaultFolder.KNOWLEDGE,  # 新規追加
        "project": VaultFolder.PROJECTS,
        "life": VaultFolder.DAILY_NOTES,
        "idea": VaultFolder.IDEAS,
        "finance": VaultFolder.FINANCE,
        "task": VaultFolder.TASKS,
        "health": VaultFolder.HEALTH,
        "other": VaultFolder.INBOX,
    }

    # サブカテゴリベースのマッピング（階層構造対応）
    SUBCATEGORY_FOLDER_MAPPING = {
        # Finance subcategories
        "expenses": VaultFolder.FINANCE_EXPENSES,
        "income": VaultFolder.FINANCE_INCOME,
        "subscriptions": VaultFolder.FINANCE_SUBSCRIPTIONS,
        "budget": VaultFolder.FINANCE_BUDGETS,
        "financial_report": VaultFolder.FINANCE_REPORTS,
        # Task subcategories
        "backlog": VaultFolder.TASKS_BACKLOG,
        "active_task": VaultFolder.TASKS_ACTIVE,
        "waiting": VaultFolder.TASKS_WAITING,
        "completed_task": VaultFolder.TASKS_COMPLETED,
        # Project subcategories
        "active_project": VaultFolder.PROJECTS_ACTIVE,
        "planning": VaultFolder.PROJECTS_PLANNING,
        "on_hold": VaultFolder.PROJECTS_ON_HOLD,
        "completed_project": VaultFolder.PROJECTS_COMPLETED,
        # Health subcategories
        "activity": VaultFolder.HEALTH_ACTIVITIES,
        "sleep": VaultFolder.HEALTH_SLEEP,
        "wellness": VaultFolder.HEALTH_WELLNESS,
        "medical": VaultFolder.HEALTH_MEDICAL,
        "health_analytics": VaultFolder.HEALTH_ANALYTICS,
        # Knowledge subcategories （ LEARNING → KNOWLEDGE に変更）
        "technical": VaultFolder.KNOWLEDGE_TECHNICAL,
        "processes": VaultFolder.KNOWLEDGE_PROCESSES,
        "tools": VaultFolder.KNOWLEDGE_TOOLS,
        "learnings": VaultFolder.KNOWLEDGE_LEARNINGS,
        "course": VaultFolder.KNOWLEDGE_LEARNINGS,  # 後方互換性
        "book": VaultFolder.KNOWLEDGE_LEARNINGS,  # 後方互換性
        "skill": VaultFolder.KNOWLEDGE_LEARNINGS,  # 後方互換性
        "study_note": VaultFolder.KNOWLEDGE_LEARNINGS,  # 後方互換性
        # Inbox subcategories
        "unprocessed": VaultFolder.INBOX_UNPROCESSED,
        "pending": VaultFolder.INBOX_PENDING,
        "staged": VaultFolder.INBOX_STAGED,
    }

    # ファイル種別のマッピング
    FILE_TYPE_FOLDER_MAPPING = {
        "image": VaultFolder.IMAGES,
        "audio": VaultFolder.AUDIO,
        "video": VaultFolder.IMAGES,  # 動画も画像フォルダに
        "document": VaultFolder.DOCUMENTS,
        "archive": VaultFolder.DOCUMENTS,
        "code": VaultFolder.DOCUMENTS,
        "other": VaultFolder.OTHER_FILES,
    }

    @classmethod
    def get_folder_for_category(
        cls, category: str, subcategory: str | None = None
    ) -> VaultFolder:
        """カテゴリに基づいてフォルダを取得（階層構造対応）"""
        # サブカテゴリが指定されている場合は優先
        if subcategory and subcategory in cls.SUBCATEGORY_FOLDER_MAPPING:
            return cls.SUBCATEGORY_FOLDER_MAPPING[subcategory]

        # メインカテゴリで検索
        return cls.CATEGORY_FOLDER_MAPPING.get(category, VaultFolder.INBOX)

    @classmethod
    def get_folder_for_file_type(cls, file_type: str) -> VaultFolder:
        """ファイル種別に基づいてフォルダを取得"""
        return cls.FILE_TYPE_FOLDER_MAPPING.get(file_type, VaultFolder.OTHER_FILES)

    @classmethod
    def get_all_finance_folders(cls) -> list[VaultFolder]:
        """すべての金融関連フォルダを取得"""
        return [
            VaultFolder.FINANCE,
            VaultFolder.FINANCE_EXPENSES,
            VaultFolder.FINANCE_INCOME,
            VaultFolder.FINANCE_SUBSCRIPTIONS,
            VaultFolder.FINANCE_BUDGETS,
            VaultFolder.FINANCE_REPORTS,
        ]

    @classmethod
    def get_all_task_folders(cls) -> list[VaultFolder]:
        """すべてのタスク関連フォルダを取得"""
        return [
            VaultFolder.TASKS,
            VaultFolder.TASKS_BACKLOG,
            VaultFolder.TASKS_ACTIVE,
            VaultFolder.TASKS_WAITING,
            VaultFolder.TASKS_COMPLETED,
            VaultFolder.TASKS_TEMPLATES,
        ]

    @classmethod
    def get_all_health_folders(cls) -> list[VaultFolder]:
        """すべての健康関連フォルダを取得"""
        return [
            VaultFolder.HEALTH,
            VaultFolder.HEALTH_ACTIVITIES,
            VaultFolder.HEALTH_SLEEP,
            VaultFolder.HEALTH_WELLNESS,
            VaultFolder.HEALTH_MEDICAL,
            VaultFolder.HEALTH_ANALYTICS,
        ]

    @classmethod
    def get_all_knowledge_folders(cls) -> list[VaultFolder]:
        """すべてのナレッジ関連フォルダを取得（ LEARNING → KNOWLEDGE に変更）"""
        return [
            VaultFolder.KNOWLEDGE,
            VaultFolder.KNOWLEDGE_TECHNICAL,
            VaultFolder.KNOWLEDGE_PROCESSES,
            VaultFolder.KNOWLEDGE_TOOLS,
            VaultFolder.KNOWLEDGE_LEARNINGS,
        ]


class NoteFilename:
    """ノートファイル名の生成と解析"""

    @staticmethod
    def generate_message_note_filename(
        timestamp: datetime,
        category: str | None = None,
        title: str | None = None,
        max_title_length: int = 50,
    ) -> str:
        """メッセージノートのファイル名を生成"""

        # タイムスタンプ部分 (YYYYMMDDHHMM)
        timestamp_str = timestamp.strftime("%Y%m%d%H%M")

        # カテゴリ部分
        category_str = ""
        if category:
            # カテゴリ名をクリーンアップ
            clean_category = re.sub(
                r"[^a-zA-Z0-9\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]", "", category
            )
            if clean_category:
                category_str = f"_{clean_category}"

        # タイトル部分
        title_str = ""
        if title:
            # タイトルをクリーンアップ
            clean_title = re.sub(r'[<>:"/\\|?*\n\r]', "", title)
            clean_title = clean_title.strip()

            if clean_title:
                # 長すぎる場合は切り詰め
                if len(clean_title) > max_title_length:
                    clean_title = clean_title[:max_title_length] + "..."
                title_str = f"_{clean_title}"

        # デフォルトタイトル
        if not title_str:
            title_str = "_memo"

        return f"{timestamp_str}{category_str}{title_str}.md"

    @staticmethod
    def generate_daily_note_filename(date: datetime) -> str:
        """日次ノートのファイル名を生成"""
        return date.strftime("%Y-%m-%d.md")

    @staticmethod
    def parse_message_note_filename(filename: str) -> dict[str, str | None]:
        """メッセージノートのファイル名を解析"""

        if not filename.endswith(".md"):
            return {"timestamp": None, "category": None, "title": None}

        basename = filename[:-3]  # .md を除去

        # パターンマッチング: YYYYMMDDHHMM_[category]_[title]
        pattern = r"^(\d{12})(?:_([^_]+))?(?:_(.+))?$"
        match = re.match(pattern, basename)

        if match:
            timestamp_str, category, title = match.groups()
            return {"timestamp": timestamp_str, "category": category, "title": title}

        return {"timestamp": None, "category": None, "title": None}


# ローカルデータ管理システム（ファイルベース）


class LocalDataIndex:
    """JSON ベースのローカルデータインデックス"""

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.index_file = vault_path / ".obsidian_local_index.json"
        self.metadata_file = vault_path / ".obsidian_metadata.json"
        self.search_cache_file = vault_path / ".obsidian_search_cache.json"

        # インデックスデータ
        self.notes_index: dict[str, dict] = {}
        self.tags_index: dict[str, set[str]] = {}
        self.links_index: dict[str, set[str]] = {}
        self.content_index: dict[str, list[str]] = {}

        self._load_indexes()

    def _load_indexes(self) -> None:
        """インデックスファイルを読み込み"""
        try:
            if self.index_file.exists():
                with open(self.index_file, encoding="utf-8") as f:
                    data = json.load(f)
                    self.notes_index = data.get("notes", {})
                    # Set 型は JSON でシリアライズできないので変換
                    self.tags_index = {
                        k: set(v) for k, v in data.get("tags", {}).items()
                    }
                    self.links_index = {
                        k: set(v) for k, v in data.get("links", {}).items()
                    }
                    self.content_index = data.get("content", {})
        except Exception:
            self.notes_index = {}
            self.tags_index = {}
            self.links_index = {}
            self.content_index = {}

    def save_indexes(self) -> bool:
        """インデックスファイルを保存"""
        try:
            data = {
                "notes": self.notes_index,
                # Set 型をリストに変換
                "tags": {k: list(v) for k, v in self.tags_index.items()},
                "links": {k: list(v) for k, v in self.links_index.items()},
                "content": self.content_index,
                "last_updated": datetime.now().isoformat(),
            }

            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True
        except Exception:
            return False

    def add_note(self, note: ObsidianNote) -> bool:
        """ノートをインデックスに追加"""
        try:
            file_key = str(note.file_path.relative_to(self.vault_path))

            # ノート基本情報
            self.notes_index[file_key] = {
                "title": note.title,
                "created_at": note.created_at.isoformat(),
                "modified_at": note.modified_at.isoformat(),
                "status": note.frontmatter.status.value,
                "category": note.frontmatter.ai_category,
                "file_size": len(note.content.encode()),
                "word_count": len(note.content.split()),
                "ai_processed": note.frontmatter.ai_processed,
                "ai_summary": note.frontmatter.ai_summary,
            }

            # タグインデックス
            all_tags = note.frontmatter.tags + note.frontmatter.ai_tags
            for tag in all_tags:
                clean_tag = tag.lstrip("#")
                if clean_tag not in self.tags_index:
                    self.tags_index[clean_tag] = set()
                self.tags_index[clean_tag].add(file_key)

            # コンテンツインデックス（検索用キーワード）
            words = note.content.lower().split()
            self.content_index[file_key] = list(set(words))

            return True
        except Exception:
            return False

    def remove_note(self, file_path: Path) -> bool:
        """ノートをインデックスから削除"""
        try:
            file_key = str(file_path.relative_to(self.vault_path))

            # ノート情報削除
            if file_key in self.notes_index:
                del self.notes_index[file_key]

            # タグインデックスから削除
            for tag_files in self.tags_index.values():
                tag_files.discard(file_key)

            # リンクインデックスから削除
            if file_key in self.links_index:
                del self.links_index[file_key]

            # コンテンツインデックスから削除
            if file_key in self.content_index:
                del self.content_index[file_key]

            return True
        except Exception:
            return False

    def search_notes(
        self,
        query: str | None = None,
        tags: list[str] | None = None,
        status: str | None = None,
        category: str | None = None,
        limit: int = 50,
    ) -> list[str]:
        """ノートを検索してファイルパスのリストを返す"""
        results = set(self.notes_index.keys())

        # クエリ検索
        if query:
            query_words = query.lower().split()
            matching_files = set()

            for file_key, words in self.content_index.items():
                if any(word in words for word in query_words):
                    matching_files.add(file_key)

            results &= matching_files

        # タグフィルター
        if tags:
            for tag in tags:
                clean_tag = tag.lstrip("#")
                if clean_tag in self.tags_index:
                    results &= self.tags_index[clean_tag]
                else:
                    results = set()  # タグが存在しない場合は空結果
                    break

        # ステータスフィルター
        if status:
            status_files = {
                k for k, v in self.notes_index.items() if v.get("status") == status
            }
            results &= status_files

        # カテゴリフィルター
        if category:
            category_files = {
                k for k, v in self.notes_index.items() if v.get("category") == category
            }
            results &= category_files

        # 結果を作成日時でソート
        sorted_results = sorted(
            results,
            key=lambda x: self.notes_index[x].get("created_at", ""),
            reverse=True,
        )

        return sorted_results[:limit]

    def get_stats(self) -> dict:
        """統計情報を取得"""
        total_notes = len(self.notes_index)
        total_tags = len(self.tags_index)

        # ステータス別統計
        status_counts: dict[str, int] = {}
        category_counts: dict[str, int] = {}
        total_words = 0

        for note_data in self.notes_index.values():
            status = note_data.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

            category = note_data.get("category")
            if category:
                category_counts[category] = category_counts.get(category, 0) + 1

            total_words += note_data.get("word_count", 0)

        # 人気タグ（上位 10 個）
        popular_tags = sorted(
            [(tag, len(files)) for tag, files in self.tags_index.items()],
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        return {
            "total_notes": total_notes,
            "total_tags": total_tags,
            "total_words": total_words,
            "status_distribution": status_counts,
            "category_distribution": category_counts,
            "popular_tags": dict(popular_tags),
            "last_updated": datetime.now().isoformat(),
        }
