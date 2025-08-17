# Discord-Obsidian Memo Bot - 包括的ドキュメント

## 目次

1. [プロジェクト概要](#プロジェクト概要)
2. [アーキテクチャ](#アーキテクチャ)
3. [セットアップとインストール](#セットアップとインストール)
4. [API仕様書](#API仕様書)
5. [設定オプション](#設定オプション)
6. [使用例とユースケース](#使用例とユースケース)
7. [開発者ガイド](#開発者ガイド)
8. [トラブルシューティング](#トラブルシューティング)

---

## プロジェクト概要

Discord-Obsidian Memo Botは、Discordを統合インターフェースとして使用し、AI分析による自動メモ処理とObsidianナレッジベースへの保存を提供する包括的な個人ナレッジマネジメントシステムです。

### 主要機能

#### 🤖 AI駆動メモ処理
- **自動メッセージ分析**: Google Gemini AIによるDiscordメッセージの自動分析・分類
- **インテリジェントタグ付け**: 内容に基づく自動タグ生成とカテゴリ分類
- **要約生成**: 長文メッセージの自動要約とキーポイント抽出
- **URLコンテンツ解析**: 共有されたリンクの自動要約とメタデータ抽出

#### 🎤 音声処理機能
- **音声文字起こし**: Google Cloud Speech-to-Text APIによる高精度な音声認識
- **音声メモ処理**: ボイスチャンネルでの音声メモの自動文字起こしとObsidian保存
- **音声ファイル処理**: アップロードされた音声ファイルの自動処理

#### 📝 Obsidian統合
- **構造化ノート生成**: AIが分析した内容を構造化されたMarkdownノートとして保存
- **自動フォルダ分類**: 内容に基づいたObsidianボルト内の適切なフォルダへの自動分類
- **テンプレートシステム**: 柔軟なMarkdownテンプレートシステムによるノート生成
- **デイリーノート統合**: 日次ノートとの統合、Activity LogとDaily Tasksの自動更新

#### 💰 ファイナンス管理
- **支出トラッキング**: 金融関連メッセージの自動検出と支出記録
- **定期購入管理**: サブスクリプションサービスの管理と期限提醒
- **予算管理**: 月次・年次予算の設定と支出監視
- **ファイナンスレポート**: 定期的な支出レポートの自動生成

#### ✅ タスク・プロジェクト管理
- **タスク抽出**: メッセージからのタスク自動抽出と作成
- **プロジェクト追跡**: プロジェクトの進捗管理と期限監視
- **生産性レビュー**: 週次・月次生産性レポートの自動生成
- **リマインダーシステム**: 重要タスクの自動通知

#### 🏃‍♂️ 健康データ統合
- **Garmin Connect統合**: Garmin健康デバイスとの自動データ同期
- **活動分析**: 運動データの分析とインサイト生成
- **睡眠分析**: 睡眠パターンの追跡と改善提案
- **健康レポート**: 定期的な健康データサマリーの生成

### システム特徴

- **非同期処理**: 高パフォーマンスな非同期I/O操作
- **型安全性**: 完全なPython型ヒントによる安全性確保
- **セキュリティ**: Google Cloud Secret Managerとセキュリティログによる安全な秘密情報管理
- **スケーラビリティ**: Google Cloud Runでの24時間365日稼働対応
- **包括的テスト**: 単体テスト・統合テストによる品質保証

---

## アーキテクチャ

### システム全体構成

Discord-Obsidian Memo Botは以下のレイヤード・アーキテクチャを採用しています：

```
┌─────────────────────────────────────────────────────────────┐
│                    Interface Layer                          │
│  ┌─────────────────┐  ┌──────────────────────────────────┐  │
│  │   Discord Bot   │  │      REST API (Future)          │  │
│  │   (Primary UI)  │  │   (Web Dashboard)                │  │
│  └─────────────────┘  └──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  Business Logic Layer                      │
│  ┌──────────────┐ ┌───────────────┐ ┌──────────────────┐   │
│  │ Message      │ │ AI Processing │ │ Finance Manager  │   │
│  │ Processing   │ │ & Analysis    │ │ & Task Manager   │   │
│  └──────────────┘ └───────────────┘ └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   Integration Layer                        │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────────────┐  │
│  │ Gemini AI   │ │ Google Cloud │ │ Garmin Connect       │  │
│  │ API         │ │ Speech API   │ │ API                  │  │
│  └─────────────┘ └──────────────┘ └──────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   Storage Layer                            │
│  ┌─────────────────────────┐  ┌─────────────────────────┐   │
│  │     Obsidian Vault      │  │   Security & Logs       │   │
│  │   (Structured Notes)    │  │ (Cloud Secret Manager)  │   │
│  └─────────────────────────┘  └─────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### モジュール構成

```
src/
├── bot/                    # Discord Bot レイヤー
│   ├── client.py          # メインDiscordクライアント
│   ├── handlers.py        # イベントハンドラー
│   ├── commands.py        # スラッシュコマンド
│   ├── message_processor.py # メッセージ処理ロジック
│   └── models.py          # Discordデータモデル
│
├── ai/                     # AI処理レイヤー
│   ├── processor.py       # メインAIプロセッサー
│   ├── gemini_client.py   # Gemini APIクライアント
│   ├── note_analyzer.py   # ノート分析エンジン
│   ├── url_processor.py   # URL内容処理
│   └── vector_store.py    # ベクトル検索
│
├── obsidian/              # Obsidian統合レイヤー
│   ├── file_manager.py    # ファイル操作管理
│   ├── template_system.py # テンプレートエンジン
│   ├── daily_integration.py # デイリーノート統合
│   └── organizer.py       # ボルト組織化
│
├── finance/               # ファイナンス管理
│   ├── expense_manager.py # 支出管理
│   ├── subscription_manager.py # サブスク管理
│   └── report_generator.py # レポート生成
│
├── tasks/                 # タスク管理
│   ├── task_manager.py    # タスク管理
│   ├── schedule_manager.py # スケジュール管理
│   └── reminder_system.py # リマインダー
│
├── health_analysis/       # 健康データ分析
│   ├── analyzer.py        # データ分析
│   ├── integrator.py      # データ統合
│   └── scheduler.py       # 定期処理
│
├── garmin/                # Garmin Connect統合
│   ├── client.py          # Garmin APIクライアント
│   ├── cache.py           # データキャッシュ
│   └── formatter.py       # データフォーマット
│
├── audio/                 # 音声処理
│   └── speech_processor.py # 音声文字起こし
│
├── security/              # セキュリティ
│   ├── secret_manager.py  # 秘密情報管理
│   └── access_logger.py   # アクセスログ
│
└── monitoring/            # 監視・ヘルスチェック
    └── health_server.py   # ヘルスチェックサーバー
```

### データフロー

1. **入力処理**: Discordメッセージ → Message Handler → AI Processor
2. **AI分析**: Gemini API → Content Analysis → Category Detection
3. **構造化**: Template System → Markdown Generation → Metadata Extraction
4. **保存**: Obsidian File Manager → Vault Organization → File Operations
5. **統合**: Daily Note Integration → Cross-referencing → Search Indexing

### 設計パターン

- **レイヤードアーキテクチャ**: 明確な責任分離と保守性
- **依存性注入**: 疎結合とテスト容易性
- **ファクトリーパターン**: 設定ベースのクライアント生成
- **ストラテジーパターン**: プラガブルな処理方法
- **オブザーバーパターン**: イベント駆動アーキテクチャ

---

## セットアップとインストール

### 前提条件

- **Python**: 3.13以上
- **uv**: 高速Pythonパッケージマネージャー
- **Obsidian**: ローカルボルトまたはクラウド同期ボルト
- **Discordボット**: Discord Developer Portalでの設定済みボット

### 必要なAPIキー

1. **Discord Bot Token**: [Discord Developer Portal](https://discord.com/developers/applications)
2. **Google Gemini API Key**: [Google AI Studio](https://makersuite.google.com/)
3. **Google Cloud Project** (音声認識用、オプション)
4. **Garmin Connect Account** (健康データ統合用、オプション)

### インストール手順

#### 1. リポジトリのクローン

```bash
git clone https://github.com/kenvexar/discord-obsidian-memo-bot.git
cd discord-obsidian-memo-bot
```

#### 2. Python環境のセットアップ

```bash
# uvのインストール (未インストールの場合)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 依存関係のインストール
uv sync

# 開発依存関係も含める場合
uv sync --dev
```

#### 3. 環境変数の設定

```bash
# .env.exampleをコピー
cp .env.example .env

# .envファイルを編集
nano .env
```

#### 4. 必須環境変数の設定

```env
# Core Discord & AI
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_GUILD_ID=your_guild_id
GEMINI_API_KEY=your_gemini_api_key
OBSIDIAN_VAULT_PATH=/path/to/your/obsidian/vault

# Channel Configuration (Discordサーバーに応じて設定)
CHANNEL_INBOX=123456789              # メインテキストメモ
CHANNEL_VOICE=123456789              # ボイスメモ
CHANNEL_FILES=123456789              # ファイル共有
CHANNEL_MONEY=123456789              # 金融関連
CHANNEL_FINANCE_REPORTS=123456789    # 財務レポート
CHANNEL_TASKS=123456789              # タスク管理
CHANNEL_PRODUCTIVITY_REVIEWS=123456789 # 生産性レビュー
CHANNEL_NOTIFICATIONS=123456789      # 通知
CHANNEL_COMMANDS=123456789           # コマンド実行
```

#### 5. オプション機能の設定

```env
# 音声認識 (オプション)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Garmin Connect統合 (オプション)
GARMIN_EMAIL=your_garmin_email
GARMIN_PASSWORD=your_garmin_password

# 追加チャンネル (オプション)
CHANNEL_HEALTH_ACTIVITIES=123456789
CHANNEL_HEALTH_SLEEP=123456789
CHANNEL_PROJECTS=123456789
CHANNEL_WEEKLY_REVIEWS=123456789
```

#### 6. Obsidianボルトの初期化

```bash
# ボルト構造の自動作成
uv run python -c "
from src.obsidian.file_manager import ObsidianFileManager
from src.config import get_settings
manager = ObsidianFileManager(get_settings().obsidian_vault_path)
import asyncio
asyncio.run(manager.initialize_vault())
"
```

#### 7. 動作確認

```bash
# 設定テスト
uv run python -c "from src.config import get_settings; print('設定OK:', get_settings().environment)"

# ボット起動テスト
uv run python -m src.main
```

### Docker環境での実行

#### 1. Dockerイメージのビルド

```bash
docker build -t discord-obsidian-memo-bot .
```

#### 2. Docker Composeでの実行

```yaml
# docker-compose.yml
version: '3.8'
services:
  bot:
    build: .
    env_file:
      - .env
    volumes:
      - ./obsidian_vault:/app/obsidian_vault:rw
      - ./logs:/app/logs:rw
    restart: unless-stopped
```

```bash
docker-compose up -d
```

### Google Cloud Runでのデプロイ

#### 1. Cloud Run設定

```bash
# Google Cloud CLIの設定
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# シークレットの設定
gcloud secrets create discord-bot-token --data-file=<(echo -n "YOUR_TOKEN")
gcloud secrets create gemini-api-key --data-file=<(echo -n "YOUR_KEY")

# デプロイ
gcloud run deploy discord-obsidian-memo-bot \
  --source . \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --set-env-vars ENVIRONMENT=production
```

---

## API仕様書

### Discord コマンド API

Discord-Obsidian Memo Botは豊富なスラッシュコマンドを提供しています。

#### 基本コマンド

##### `/ping`
- **説明**: ボットの応答性テスト
- **パラメーター**: なし
- **戻り値**: レスポンス時間とシステム状態
- **例**: `/ping`

##### `/status`
- **説明**: システム全体の状態確認
- **パラメーター**: なし
- **戻り値**:
  - Bot稼働時間
  - API使用状況
  - システムメトリクス
  - 各サービス接続状態

##### `/help`
- **説明**: 利用可能なコマンドの一覧表示
- **パラメーター**:
  - `category` (オプション): コマンドカテゴリ
- **戻り値**: コマンドリストと使用方法

#### AI処理コマンド

##### `/process`
- **説明**: テキストの手動AI処理
- **パラメーター**:
  - `text` (必須): 処理したいテキスト
  - `save_to_obsidian` (オプション): Obsidianに保存するか
- **戻り値**: AI分析結果とメタデータ

##### `/summarize`
- **説明**: 長文テキストの要約生成
- **パラメーター**:
  - `text` (必須): 要約したいテキスト
  - `max_length` (オプション): 最大要約長
- **戻り値**: 要約文とキーポイント

##### `/analyze_url`
- **説明**: URL内容の分析と要約
- **パラメーター**:
  - `url` (必須): 分析したいURL
  - `save_summary` (オプション): 要約をObsidianに保存
- **戻り値**: URLコンテンツの要約とメタデータ

#### Obsidianコマンド

##### `/search_notes`
- **説明**: Obsidianボルト内のノート検索
- **パラメーター**:
  - `query` (必須): 検索クエリ
  - `folder` (オプション): 検索対象フォルダ
  - `limit` (オプション): 結果上限数
- **戻り値**: マッチしたノートのリストと内容スニペット

##### `/create_note`
- **説明**: 新しいObsidianノートの作成
- **パラメーター**:
  - `title` (必須): ノートタイトル
  - `content` (必須): ノート内容
  - `folder` (オプション): 保存先フォルダ
  - `template` (オプション): 使用するテンプレート
- **戻り値**: 作成されたノートの情報

##### `/vault_stats`
- **説明**: Obsidianボルトの統計情報
- **パラメーター**: なし
- **戻り値**:
  - 総ノート数
  - フォルダ別ノート数
  - 最近の更新状況
  - ストレージ使用量

#### デイリーノートコマンド

##### `/daily_note`
- **説明**: 今日のデイリーノート操作
- **パラメーター**:
  - `action` (必須): `show`, `create`, `update`
  - `content` (オプション): 追加する内容
- **戻り値**: デイリーノートの内容または更新結果

##### `/weekly_review`
- **説明**: 週次レビューの生成
- **パラメーター**:
  - `week_offset` (オプション): 何週間前のレビュー (デフォルト: 0)
- **戻り値**: 1週間のアクティビティサマリー

#### ファイナンス管理コマンド

##### `/add_expense`
- **説明**: 支出の記録
- **パラメーター**:
  - `amount` (必須): 金額
  - `description` (必須): 支出説明
  - `category` (オプション): カテゴリ
  - `date` (オプション): 日付 (デフォルト: 今日)
- **戻り値**: 記録された支出の詳細

##### `/expense_report`
- **説明**: 支出レポートの生成
- **パラメーター**:
  - `period` (必須): `daily`, `weekly`, `monthly`, `yearly`
  - `category` (オプション): 特定カテゴリのみ
- **戻り値**: 期間別支出サマリー

##### `/add_subscription`
- **説明**: 定期購入サービスの登録
- **パラメーター**:
  - `name` (必須): サービス名
  - `amount` (必須): 月額料金
  - `billing_date` (必須): 請求日
  - `category` (オプション): カテゴリ
- **戻り値**: 登録されたサブスクリプション詳細

##### `/subscription_overview`
- **説明**: 定期購入の概要表示
- **パラメーター**: なし
- **戻り値**:
  - 月額合計
  - 次回請求予定
  - 期限が近いサービス

#### タスク管理コマンド

##### `/add_task`
- **説明**: 新しいタスクの作成
- **パラメーター**:
  - `title` (必須): タスクタイトル
  - `description` (オプション): タスク詳細
  - `due_date` (オプション): 期限
  - `priority` (オプション): 優先度 (`low`, `medium`, `high`, `urgent`)
  - `project` (オプション): プロジェクト名
- **戻り値**: 作成されたタスクの詳細

##### `/list_tasks`
- **説明**: タスクリストの表示
- **パラメーター**:
  - `status` (オプション): `pending`, `in_progress`, `completed`
  - `project` (オプション): 特定プロジェクトのみ
  - `priority` (オプション): 特定優先度のみ
- **戻り値**: フィルタされたタスクリスト

##### `/complete_task`
- **説明**: タスクの完了
- **パラメーター**:
  - `task_id` (必須): タスクID
  - `notes` (オプション): 完了メモ
- **戻り値**: 完了したタスクの詳細

##### `/productivity_report`
- **説明**: 生産性レポートの生成
- **パラメーター**:
  - `period` (必須): `daily`, `weekly`, `monthly`
- **戻り値**:
  - 完了タスク数
  - 平均完了時間
  - プロジェクト別進捗

#### システム管理コマンド

##### `/backup_vault`
- **説明**: Obsidianボルトのバックアップ
- **パラメーター**: なし
- **戻り値**: バックアップファイルの場所と詳細

##### `/system_metrics`
- **説明**: 詳細なシステムメトリクス
- **パラメーター**: なし
- **戻り値**:
  - CPU/メモリ使用率
  - API使用統計
  - エラー統計
  - パフォーマンスメトリクス

##### `/cache_info`
- **説明**: AIキャッシュの状態確認
- **パラメーター**: なし
- **戻り値**: キャッシュヒット率と使用状況

##### `/clear_cache`
- **説明**: AIキャッシュのクリア
- **パラメーター**: なし
- **戻り値**: クリアされたキャッシュ数

#### テンプレート管理コマンド

##### `/list_templates`
- **説明**: 利用可能なテンプレート一覧
- **パラメーター**: なし
- **戻り値**: テンプレート名とその説明

##### `/create_from_template`
- **説明**: テンプレートからノート作成
- **パラメーター**:
  - `template_name` (必須): テンプレート名
  - `title` (必須): ノートタイトル
  - `variables` (オプション): テンプレート変数
- **戻り値**: 作成されたノートの詳細

### Python API

#### AIProcessor クラス

```python
from src.ai.processor import AIProcessor

class AIProcessor:
    async def process_text(
        self,
        text: str,
        context: Optional[str] = None,
        enable_cache: bool = True
    ) -> ProcessingResult:
        """テキストのAI処理"""

    async def process_batch(
        self,
        texts: List[str],
        max_concurrent: int = 3
    ) -> List[ProcessingResult]:
        """バッチテキスト処理"""

    async def generate_embeddings(
        self,
        text: str
    ) -> List[float]:
        """テキストの埋め込みベクトル生成"""

    async def summarize_url_content(
        self,
        url: str
    ) -> UrlSummary:
        """URL内容の要約生成"""
```

#### ObsidianFileManager クラス

```python
from src.obsidian.file_manager import ObsidianFileManager

class ObsidianFileManager:
    async def save_note(
        self,
        content: str,
        metadata: NoteMetadata,
        folder_hint: Optional[str] = None
    ) -> SaveResult:
        """ノートの保存"""

    async def search_notes(
        self,
        query: str,
        folder: Optional[str] = None,
        limit: int = 10
    ) -> List[SearchResult]:
        """ノート検索"""

    async def get_vault_stats(self) -> VaultStats:
        """ボルト統計の取得"""

    async def backup_vault(self) -> BackupResult:
        """ボルトのバックアップ"""
```

---

## 設定オプション

### 環境変数設定

#### コア設定 (必須)

| 変数名 | 説明 | 例 |
|--------|------|-----|
| `DISCORD_BOT_TOKEN` | DiscordボットトークN | `MTIzNDU2Nzg5MDEyMzQ1Njc4OTA...` |
| `DISCORD_GUILD_ID` | DiscordサーバーID | `123456789012345678` |
| `GEMINI_API_KEY` | Google Gemini APIキー | `AIzaSyDaGmWKa4JsXMeMbZdTkxKc...` |
| `OBSIDIAN_VAULT_PATH` | Obsidianボルトパス | `/Users/username/ObsidianVault` |

#### チャンネル設定 (必須)

| 変数名 | 説明 | 用途 |
|--------|------|------|
| `CHANNEL_INBOX` | メインテキストメモ | 一般的なメモとアイデア |
| `CHANNEL_VOICE` | ボイスメモ | 音声メッセージの処理 |
| `CHANNEL_FILES` | ファイル共有 | 文書・画像ファイルの処理 |
| `CHANNEL_MONEY` | 金融関連 | 支出・収入の記録 |
| `CHANNEL_FINANCE_REPORTS` | 財務レポート | 自動生成された財務報告 |
| `CHANNEL_TASKS` | タスク管理 | タスクとプロジェクト管理 |
| `CHANNEL_PRODUCTIVITY_REVIEWS` | 生産性レビュー | 週次・月次レビューの配信 |
| `CHANNEL_NOTIFICATIONS` | 通知 | システム通知とアラート |
| `CHANNEL_COMMANDS` | コマンド実行 | スラッシュコマンドの実行 |

#### 拡張チャンネル設定 (オプション)

| 変数名 | 説明 | 用途 |
|--------|------|------|
| `CHANNEL_QUICK_NOTES` | クイックメモ | 短いメモの迅速な記録 |
| `CHANNEL_INCOME` | 収入記録 | 収入の追跡と管理 |
| `CHANNEL_SUBSCRIPTIONS` | サブスクリプション | 定期購入サービス管理 |
| `CHANNEL_PROJECTS` | プロジェクト | 大規模プロジェクトの管理 |
| `CHANNEL_WEEKLY_REVIEWS` | 週次レビュー | 週次生産性レビュー |
| `CHANNEL_GOAL_TRACKING` | 目標追跡 | 長期目標の進捗管理 |

#### 健康データ設定 (オプション)

| 変数名 | 説明 | 用途 |
|--------|------|------|
| `CHANNEL_HEALTH_ACTIVITIES` | 健康活動 | 運動・活動データ |
| `CHANNEL_HEALTH_SLEEP` | 睡眠データ | 睡眠パターン分析 |
| `CHANNEL_HEALTH_WELLNESS` | ウェルネス | 全般的な健康指標 |
| `CHANNEL_HEALTH_ANALYTICS` | 健康分析 | AI分析による健康インサイト |

#### API制限設定

| 変数名 | デフォルト | 説明 |
|--------|-----------|------|
| `GEMINI_API_DAILY_LIMIT` | `1500` | Gemini API 1日あたり制限 |
| `GEMINI_API_MINUTE_LIMIT` | `15` | Gemini API 1分あたり制限 |
| `SPEECH_API_MONTHLY_LIMIT_MINUTES` | `60` | 音声認識API月間制限（分） |

#### セキュリティ設定

| 変数名 | デフォルト | 説明 |
|--------|-----------|------|
| `USE_SECRET_MANAGER` | `false` | Google Cloud Secret Manager使用 |
| `GOOGLE_CLOUD_PROJECT` | `None` | Google Cloudプロジェクト名 |
| `ENABLE_ACCESS_LOGGING` | `true` | アクセスログ記録の有効化 |
| `SECURITY_LOG_PATH` | `None` | セキュリティログファイルパス |

#### 開発・テスト設定

| 変数名 | デフォルト | 説明 |
|--------|-----------|------|
| `ENVIRONMENT` | `development` | 実行環境 (`development`, `production`, `testing`) |
| `ENABLE_MOCK_MODE` | `false` | モックモードの有効化 |
| `MOCK_DISCORD_ENABLED` | `false` | Discord API モック |
| `MOCK_GEMINI_ENABLED` | `false` | Gemini API モック |
| `MOCK_GARMIN_ENABLED` | `false` | Garmin API モック |

### Obsidianボルト構造

自動作成されるフォルダ構造：

```
ObsidianVault/
├── 00_Inbox/                  # 受信トレイ（未分類メモ）
├── 01_Projects/               # プロジェクト
├── 02_DailyNotes/            # デイリーノート
│   ├── 2024/
│   │   ├── 01-January/
│   │   ├── 02-February/
│   │   └── ...
├── 03_Ideas/                  # アイデア・インスピレーション
├── 04_Archive/                # アーカイブ
├── 05_Resources/              # リソース・参考資料
├── 06_Finance/                # 財務・家計
├── 07_Tasks/                  # タスク・TODO
├── 08_Health/                 # 健康・ウェルネス
├── 10_Attachments/            # 添付ファイル
│   ├── Images/
│   ├── Documents/
│   ├── Audio/
│   └── Other/
└── 99_Meta/                   # メタデータ・設定
    └── Templates/             # テンプレート
        ├── daily_note.md
        ├── meeting_note.md
        ├── task_note.md
        └── idea_note.md
```

### テンプレート設定

#### デイリーノートテンプレート

```markdown
# {{date}} - Daily Note

## Today's Focus
-

## Activities
<!-- Auto-populated by Discord messages -->

## Tasks
<!-- Extracted from messages and manual entries -->

## Finance
<!-- Tracked expenses and income -->

## Health & Wellness
<!-- Garmin data and wellness notes -->

## Reflections
-

## Tomorrow's Plan
-

---
Created: {{timestamp}}
Tags: #daily-note
```

#### タスクノートテンプレート

```markdown
# {{title}}

## Description
{{description}}

## Details
- **Priority**: {{priority}}
- **Project**: {{project}}
- **Due Date**: {{due_date}}
- **Status**: {{status}}

## Progress
{{progress_notes}}

## Related Notes
{{related_links}}

---
Created: {{created_date}}
Tags: #task {{project_tag}}
```

---

## 使用例とユースケース

### 日常的な使用シナリオ

#### 1. 朝のセットアップ

```discord
# デイリーノートの確認
/daily_note action:show

# 今日のタスク確認
/list_tasks status:pending

# 健康データの同期（Garmin連携）
# 自動実行：朝8時に前日の活動データを取得
```

#### 2. アイデアキャプチャ

```discord
# Inboxチャンネルでの投稿
新しいプロジェクトアイデア：AIを使った家計簿アプリ。
音声で支出を記録して、自動カテゴリ分類。
Obsidianと連携して月次レポート生成。

# 自動処理結果
# → 03_Ideas/ai-household-app.md として保存
# → タグ: #idea #ai #finance #app
# → 関連ノートとのリンク自動生成
```

#### 3. 会議メモ

```discord
# Voiceチャンネルでの音声メモ
"今日のチームミーティングで、新機能のリリース予定が来月に決定。
UIデザインの修正と、バックエンドAPIの最適化が必要。
担当者はAliceがフロントエンド、BobがAPIを担当する。"

# 自動処理結果
# → 音声文字起こし → AI分析 → 構造化ノート生成
# → 01_Projects/team-meeting-20240117.md
# → タスク自動抽出：UIデザイン修正、API最適化
```

#### 4. 支出管理

```discord
# Moneyチャンネルでの投稿
今日のランチ：1200円、コンビニで買い物：800円

# または直接コマンド
/add_expense amount:1200 description:"ランチ" category:"食費"
/add_expense amount:800 description:"コンビニ買い物" category:"日用品"

# 月末の支出レポート生成
/expense_report period:monthly
```

#### 5. プロジェクト管理

```discord
# 新プロジェクトの作成
/add_task title:"ブログリニューアル" description:"WordPressからGatsbyに移行" priority:high due_date:"2024-02-15" project:"ブログ"

# 進捗更新
プロジェクト「ブログリニューアル」の進捗：
デザインモックアップ完成。コンテンツ移行を開始。
予定より1日遅れているが、来週には完了予定。

# タスク完了
/complete_task task_id:123 notes:"デザイン完了、レビュー済み"
```

### 高度な使用例

#### 1. 自動化されたワークフロー

```python
# カスタムワークフロー例
# 毎朝自動実行される健康データ分析

async def morning_health_routine():
    # Garminデータの取得
    garmin_data = await garmin_client.get_yesterday_data()

    # AI分析
    health_insights = await ai_processor.analyze_health_data(garmin_data)

    # Obsidianノート生成
    await obsidian_manager.save_health_summary(health_insights)

    # Discord通知
    await bot.send_notification(
        channel="health_analytics",
        content=f"昨日の健康サマリーを生成しました：\n{health_insights.summary}"
    )
```

#### 2. 複合的な情報統合

```discord
# URL共有による自動記事分析
https://example.com/interesting-ai-article

# 自動処理フロー：
# 1. URL内容の取得・分析
# 2. 要約生成
# 3. 関連する既存ノートの検索
# 4. 内部リンクの生成
# 5. 適切なフォルダに保存
# 6. タグの自動付与

# 結果例：
# → 05_Resources/ai-trends-2024.md
# → 関連ノート: [[Machine Learning Basics]], [[Future of AI]]
# → タグ: #ai #trends #article #resource
```

#### 3. 週次レビューワークフロー

```discord
# 金曜日の週次レビュー
/weekly_review

# 自動生成内容：
# - 今週完了したタスク
# - 今週の支出サマリー
# - 健康活動データ
# - AIが検出した重要なメモ
# - 来週の推奨アクション
```

### 特殊なユースケース

#### 1. 研究・学習ワークフロー

```discord
# 研究テーマに関する情報収集
研究テーマ：「機械学習における説明可能性」

# 関連記事の共有
https://research.example.com/explainable-ai-paper
https://blog.example.com/ml-interpretability

# 自動処理：
# → 論文要約生成
# → 既存の研究ノートとの関連付け
# → 概念マップの更新
# → 追加調査項目の提案
```

#### 2. 創作・ライティング支援

```discord
# ブログ記事のアイデア投稿
ブログネタ：「リモートワークでの生産性向上テクニック」
書きたい内容：
- 時間管理のコツ
- 集中力維持の方法
- ツール活用法

# AI支援機能：
# → 記事構成案の自動生成
# → 関連する既存メモの検索
# → 参考資料の提案
# → 執筆テンプレートの提供
```

#### 3. 健康とウェルネス追跡

```discord
# 健康目標の設定
/add_task title:"1日1万歩達成" priority:medium project:"健康管理"

# Garmin自動同期データ：
# → 毎日の歩数、心拍数、睡眠データ
# → 週次・月次トレンド分析
# → 目標達成度の自動評価
# → 改善提案の生成

# 健康レポート例：
# → 平均睡眠時間：7時間15分（目標：8時間）
# → 週間運動時間：3.5時間（目標：5時間）
# → ストレスレベル：中程度
# → 推奨アクション：就寝時間を30分早める
```

---

## 開発者ガイド

### 開発環境のセットアップ

#### 1. 必要なツール

```bash
# Python 3.13以上
python --version

# uvパッケージマネージャー
curl -LsSf https://astral.sh/uv/install.sh | sh

# Git
git --version
```

#### 2. 開発依存関係のインストール

```bash
# プロジェクトクローン
git clone https://github.com/kenvexar/discord-obsidian-memo-bot.git
cd discord-obsidian-memo-bot

# 開発環境構築
uv sync --dev

# pre-commitフックの設定
uv run pre-commit install
```

#### 3. 開発用設定

```bash
# 開発用環境変数
cp .env.example .env.development

# テスト環境の設定
export ENVIRONMENT=development
export ENABLE_MOCK_MODE=true
```

### コード品質ガイドライン

#### 1. コードフォーマットとリンティング

```bash
# コードフォーマット（Ruff）
uv run ruff format src/

# リンティングチェック
uv run ruff check src/

# 自動修正
uv run ruff check src/ --fix

# 型チェック（mypy）
uv run mypy src/
```

#### 2. テスト実行

```bash
# 全テスト実行
uv run pytest

# カバレッジ付きテスト
uv run pytest --cov=src

# 特定テストファイル
uv run pytest tests/unit/test_ai_processing.py

# 統合テスト
uv run pytest tests/integration/

# 非同期テスト（詳細出力）
uv run pytest tests/unit/test_ai_processing.py -v
```

#### 3. コード品質チェック

```bash
# 全品質チェック実行
uv run ruff check src/ --fix && uv run ruff format src/ && uv run mypy src/

# pre-commitフック実行
uv run pre-commit run --all-files
```

### プロジェクト構造

#### 1. モジュール設計原則

- **単一責任の原則**: 各モジュールは一つの明確な責任を持つ
- **依存性注入**: コンストラクタでの依存関係注入
- **型安全性**: 完全な型ヒント
- **非同期ファーストー**: 全I/O操作を非同期で実装

#### 2. レイヤードアーキテクチャ

```python
# 各レイヤーの責任範囲

# Interface Layer (bot/)
# - Discord API との直接やり取り
# - ユーザー入力の検証
# - レスポンスフォーマット

# Business Logic Layer (ai/, finance/, tasks/)
# - ドメインロジックの実装
# - ビジネスルールの適用
# - データ変換・処理

# Integration Layer (obsidian/, garmin/, audio/)
# - 外部サービスとの統合
# - データ形式の変換
# - API呼び出し管理

# Infrastructure Layer (config/, security/, utils/)
# - 横断的関心事
# - 設定管理
# - ログ・監視
```

#### 3. 新機能開発フロー

```python
# 1. データモデル定義 (models.py)
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NewFeatureRequest(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    created_at: datetime = Field(default_factory=datetime.now)

# 2. ビジネスロジック実装
class NewFeatureManager:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def process_request(self, request: NewFeatureRequest) -> ProcessingResult:
        # ビジネスロジック実装
        pass

# 3. Discord コマンド追加
class NewFeatureCommands:
    def __init__(self, feature_manager: NewFeatureManager):
        self.feature_manager = feature_manager

    @app_commands.command()
    async def new_feature_command(self, interaction: discord.Interaction, title: str):
        # コマンド実装
        pass

# 4. テスト作成
class TestNewFeature:
    @pytest.mark.asyncio
    async def test_process_request(self):
        # テスト実装
        pass
```

### APIの拡張

#### 1. 新しいAI処理機能の追加

```python
# src/ai/processor.py への機能追加例

class AIProcessor:
    async def new_analysis_feature(
        self,
        input_data: str,
        analysis_type: str = "standard"
    ) -> AnalysisResult:
        """新しい分析機能の実装"""

        # キャッシュチェック
        cache_key = self._generate_content_hash(f"{input_data}:{analysis_type}")
        cached_result = await self._get_from_cache(cache_key)
        if cached_result:
            return cached_result

        # Gemini API呼び出し
        prompt = self._build_analysis_prompt(input_data, analysis_type)

        try:
            response = await self.gemini_client.generate_content_async(prompt)
            result = self._parse_analysis_response(response)

            # キャッシュ保存
            await self._save_to_cache(cache_key, result)

            return result

        except Exception as e:
            logger.error("Analysis failed", error=str(e))
            raise ProcessingError(f"Analysis failed: {e}")
```

#### 2. 新しいObsidian統合機能

```python
# src/obsidian/file_manager.py への機能追加例

class ObsidianFileManager:
    async def create_specialized_note(
        self,
        note_type: str,
        content: Dict[str, Any],
        template_override: Optional[str] = None
    ) -> SaveResult:
        """特殊なノートタイプの作成"""

        # テンプレート選択
        template = template_override or f"{note_type}_template.md"

        # コンテンツの構造化
        structured_content = await self._structure_content(content, note_type)

        # テンプレート適用
        final_content = await self.template_system.apply_template(
            template, structured_content
        )

        # 保存先決定
        folder = self._determine_folder_for_type(note_type)

        # ファイル保存
        return await self.save_note(final_content, metadata, folder)
```

### テスト戦略

#### 1. 単体テスト

```python
# tests/unit/test_new_feature.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.new_feature.manager import NewFeatureManager

class TestNewFeatureManager:
    @pytest.fixture
    def manager(self, mock_settings):
        return NewFeatureManager(mock_settings)

    @pytest.mark.asyncio
    async def test_process_request_success(self, manager):
        # テストデータ準備
        request = NewFeatureRequest(title="Test", description="Test description")

        # モック設定
        manager.external_service = AsyncMock()
        manager.external_service.process.return_value = {"status": "success"}

        # テスト実行
        result = await manager.process_request(request)

        # アサーション
        assert result.success is True
        assert result.data["status"] == "success"
        manager.external_service.process.assert_called_once()
```

#### 2. 統合テスト

```python
# tests/integration/test_new_feature_integration.py

import pytest
from src.bot.client import DiscordBot
from src.new_feature.manager import NewFeatureManager

class TestNewFeatureIntegration:
    @pytest.mark.asyncio
    async def test_discord_to_obsidian_flow(self, test_bot, test_vault):
        # エンドツーエンドのワークフローテスト

        # Discord メッセージシミュレーション
        mock_message = create_mock_message("Test new feature")

        # 処理実行
        result = await test_bot.process_message(mock_message)

        # Obsidian保存確認
        saved_files = test_vault.list_recent_files()
        assert len(saved_files) == 1
        assert "new-feature" in saved_files[0].name
```

#### 3. パフォーマンステスト

```python
# tests/performance/test_ai_performance.py

import pytest
import time
from src.ai.processor import AIProcessor

class TestAIPerformance:
    @pytest.mark.asyncio
    async def test_batch_processing_performance(self, ai_processor):
        # 大量データでのパフォーマンステスト

        texts = ["Test text " + str(i) for i in range(100)]

        start_time = time.time()
        results = await ai_processor.process_batch(texts, max_concurrent=5)
        end_time = time.time()

        # パフォーマンス要件確認
        processing_time = end_time - start_time
        assert processing_time < 30.0  # 30秒以内
        assert len(results) == 100
        assert all(r.success for r in results)
```

### デプロイメント

#### 1. 本番環境設定

```yaml
# service.yaml (Google Cloud Run)
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: discord-obsidian-memo-bot
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/execution-environment: gen2
        run.googleapis.com/cpu-throttling: "false"
    spec:
      containerConcurrency: 1
      timeoutSeconds: 3600
      containers:
      - image: gcr.io/PROJECT_ID/discord-obsidian-memo-bot
        ports:
        - containerPort: 8080
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: USE_SECRET_MANAGER
          value: "true"
        - name: GOOGLE_CLOUD_PROJECT
          value: "PROJECT_ID"
        resources:
          limits:
            cpu: "2"
            memory: "2Gi"
          requests:
            cpu: "1"
            memory: "1Gi"
```

#### 2. CI/CDパイプライン

```yaml
# .github/workflows/deploy.yml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: astral-sh/setup-uv@v1
    - name: Install dependencies
      run: uv sync --dev
    - name: Run tests
      run: uv run pytest --cov=src
    - name: Type check
      run: uv run mypy src/
    - name: Lint
      run: uv run ruff check src/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: google-github-actions/setup-gcloud@v1
    - name: Deploy to Cloud Run
      run: |
        gcloud run deploy discord-obsidian-memo-bot \
          --source . \
          --platform managed \
          --region asia-northeast1 \
          --allow-unauthenticated
```

---

## トラブルシューティング

### よくある問題と解決方法

#### 1. インストール・セットアップ関連

##### Q: `uv sync` でパッケージインストールが失敗する

**原因**: Python 3.13未満のバージョンを使用している

**解決方法**:
```bash
# Pythonバージョン確認
python --version

# Python 3.13以上をインストール
# macOS (Homebrew)
brew install python@3.13

# Ubuntu
sudo apt update
sudo apt install python3.13

# uvでPythonバージョン指定
uv python install 3.13
uv sync
```

##### Q: Discord Bot Tokenが無効というエラー

**原因**: トークンの設定ミスまたは権限不足

**解決方法**:
```bash
# トークン確認
echo $DISCORD_BOT_TOKEN

# Discord Developer Portalで確認:
# 1. Bot permissions: Send Messages, Read Message History, Use Slash Commands
# 2. OAuth2 URL Generator: bot + applications.commands スコープ
# 3. サーバーに適切に招待されているか確認
```

##### Q: Obsidianボルトパスでエラーが発生

**原因**: パスが存在しないか、権限がない

**解決方法**:
```bash
# ディレクトリ作成
mkdir -p /path/to/obsidian/vault

# 権限確認
ls -la /path/to/obsidian/

# パス設定確認
echo $OBSIDIAN_VAULT_PATH
```

#### 2. 実行時エラー

##### Q: Gemini API でレート制限エラー

**エラーメッセージ**: `429 Too Many Requests`

**解決方法**:
```python
# レート制限設定の調整 (.env)
GEMINI_API_DAILY_LIMIT=1500
GEMINI_API_MINUTE_LIMIT=15

# キャッシュの有効活用
# AIProcessorは自動的にキャッシュを使用してAPI呼び出しを最小化
```

##### Q: 音声認識でエラーが発生

**エラーメッセージ**: `Google Cloud Speech API authentication failed`

**解決方法**:
```bash
# サービスアカウントキー設定
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"

# または、音声機能を無効化
export MOCK_SPEECH_ENABLED=true
```

##### Q: Discordでスラッシュコマンドが表示されない

**原因**: コマンド同期の問題

**解決方法**:
```python
# 開発中は手動でコマンド同期
# Botコードに一時的に追加:
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
```

#### 3. パフォーマンス問題

##### Q: AI処理が遅い

**原因**: バッチ処理の非効率またはキャッシュ未使用

**解決方法**:
```python
# バッチサイズの調整
await ai_processor.process_batch(texts, max_concurrent=3)

# キャッシュ状態確認
cache_info = ai_processor.get_cache_info()
print(f"Cache hit rate: {cache_info['hit_rate']}")

# 大量処理時のキューイング使用
for text in large_text_list:
    ai_processor.add_to_queue(text)
await ai_processor.process_queue()
```

##### Q: Obsidianファイル保存が遅い

**原因**: ディスクI/Oボトルネックまたはファイル数過多

**解決方法**:
```python
# 定期的なクリーンアップ
await obsidian_manager.clear_operation_history()

# バックアップの最適化
await obsidian_manager.backup_vault()  # 月1回程度

# ファイル統計確認
stats = await obsidian_manager.get_vault_stats()
print(f"Total files: {stats.total_files}")
```

#### 4. メモリ・リソース問題

##### Q: メモリ使用量が多い

**原因**: キャッシュの肥大化またはメモリリーク

**解決方法**:
```python
# キャッシュサイズ確認とクリア
cache_info = ai_processor.get_cache_info()
if cache_info['size_mb'] > 100:  # 100MB超過
    ai_processor.clear_cache()

# システムメトリクス監視
/system_metrics  # Discordコマンドで確認
```

##### Q: Cloud Runでタイムアウトが発生

**原因**: 長時間処理によるタイムアウト

**解決方法**:
```yaml
# service.yaml の調整
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/execution-environment: gen2
        run.googleapis.com/cpu-throttling: "false"
    spec:
      timeoutSeconds: 3600  # 1時間に延長
      containers:
      - resources:
          limits:
            cpu: "2"      # CPU増強
            memory: "2Gi" # メモリ増強
```

#### 5. データ整合性問題

##### Q: Obsidianノートが重複保存される

**原因**: 重複検出ロジックの問題

**解決方法**:
```python
# 重複チェックの強化
# ObsidianFileManager の設定確認

# 手動での重複削除
duplicates = await obsidian_manager.find_duplicates()
for dup in duplicates:
    await obsidian_manager.delete_note(dup.path)
```

##### Q: タスクやファイナンスデータが消失

**原因**: ファイル書き込みエラーまたは権限問題

**解決方法**:
```python
# バックアップからの復元
backup_files = await obsidian_manager.list_backups()
latest_backup = backup_files[0]
await obsidian_manager.restore_from_backup(latest_backup)

# 自動バックアップの有効化
# デイリーバックアップ設定
```

### ログとデバッグ

#### 1. ログレベルの調整

```bash
# 詳細ログ出力
export LOG_LEVEL=DEBUG

# JSON形式ログ
export LOG_FORMAT=json

# ログファイル指定
export LOG_FILE=/app/logs/bot.log
```

#### 2. デバッグ情報の取得

```discord
# システム状態確認
/status

# 詳細メトリクス
/system_metrics

# AI処理状況
/cache_info

# Obsidianボルト状況
/vault_stats
```

#### 3. エラー追跡

```python
# カスタムロガー使用例
from src.utils.logger import get_logger

logger = get_logger("debug_session")

try:
    result = await some_operation()
    logger.info("Operation completed", result=result)
except Exception as e:
    logger.error(
        "Operation failed",
        error=str(e),
        operation="some_operation",
        exc_info=True
    )
```

### サポートとコミュニティ

#### 問題報告

1. **GitHubイシュー**: バグ報告・機能要求
2. **ログファイル**: エラー詳細の提供
3. **設定情報**: 環境変数と設定ファイル (機密情報除く)
4. **再現手順**: 問題の再現可能な手順

#### 貢献ガイドライン

1. **フォーク**: リポジトリのフォーク
2. **ブランチ**: `feature/your-feature-name` で開発
3. **テスト**: 新機能には必ずテストを追加
4. **プルリクエスト**: 詳細な説明と変更理由

---

**プロジェクト情報**
- **バージョン**: 0.1.0
- **Python要求バージョン**: 3.13以上
- **ライセンス**: MIT
- **メンテナー**: Kent
- **最終更新**: 2025年8月17日

このドキュメントは継続的に更新されます。最新情報は[GitHubリポジトリ](https://github.com/kenvexar/discord-obsidian-memo-bot)をご確認ください。
