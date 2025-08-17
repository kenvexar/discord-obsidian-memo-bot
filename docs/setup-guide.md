# Discord-Obsidian Memo Bot セットアップガイド

## 初回セットアップ手順

### 1. 前提条件の確認

#### 必要なソフトウェア
- Python 3.13 (必須)
- uv (Python パッケージマネージャー)
- Docker (デプロイ時)
- Google Cloud CLI (Cloud Run デプロイ時)

#### インストール

```bash
# uv のインストール
curl -LsSf https://astral.sh/uv/install.sh | sh

# Google Cloud CLI のインストール（デプロイ時のみ）
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
```

### 2. Discord Bot の作成

1. [Discord Developer Portal](https://discord.com/developers/applications) にアクセス
2. "New Application" をクリックして新しいアプリケーションを作成
3. "Bot" タブに移動し、"Add Bot" をクリック
4. Bot Token をコピー（後で使用）
5. "Privileged Gateway Intents" で以下を有効化：
   - Message Content Intent
   - Server Members Intent

### 3. Discord サーバーの準備

#### 必要なチャンネルの作成

以下のチャンネルを作成し、各チャンネルIDを記録してください：

**📝 CAPTURE カテゴリ（必須）:**
- `#inbox` - 汎用メモ入力
- `#voice` - 音声メモ
- `#files` - ファイル添付メモ
- `#quick-notes` - 簡単なメモ（オプション）

**💰 FINANCE カテゴリ（必須）:**
- `#money` - 支出記録
- `#finance-reports` - 家計レポート（自動生成）
- `#income` - 収入記録（オプション）
- `#subscriptions` - 定期購読管理（オプション）

**📋 PRODUCTIVITY カテゴリ（必須）:**
- `#tasks` - タスク管理
- `#productivity-reviews` - 生産性レビュー
- `#projects` - プロジェクト管理（オプション）
- `#weekly-reviews` - 週次レビュー（オプション）
- `#goal-tracking` - 目標トラッキング（オプション）

**🏥 HEALTH カテゴリ（オプション - Garmin統合用）:**
- `#health-activities` - 運動記録
- `#health-sleep` - 睡眠データ
- `#health-wellness` - ウェルネス記録
- `#health-analytics` - 健康データ分析

**⚙️ SYSTEM カテゴリ（必須）:**
- `#notifications` - ボット通知
- `#commands` - ボットコマンド
- `#logs` - システムログ（オプション）

**📊 LEGACY カテゴリ（オプション - 下位互換）:**
- `#activity-log` - 活動ログ
- `#daily-tasks` - 日次タスク

#### チャンネルIDの取得方法

1. Discord の開発者モードを有効化
2. チャンネルを右クリック → "IDをコピー"
3. 各チャンネルIDを記録

### 4. Google Cloud の設定

#### プロジェクトの作成

```bash
# プロジェクト作成
gcloud projects create your-project-id --name="Discord Obsidian Bot"

# プロジェクト設定
gcloud config set project your-project-id

# 請求アカウントの設定（必要に応じて）
gcloud billing projects link your-project-id --billing-account=YOUR-BILLING-ACCOUNT-ID
```

#### API キーの取得

1. **Gemini API Key**
   - [Google AI Studio](https://makersuite.google.com/app/apikey) でAPIキーを作成

2. **Google Cloud Speech API Key**（オプション）
   - Google Cloud Console で Speech-to-Text API を有効化
   - APIキーまたはサービスアカウントキーを作成

### 5. プロジェクトのセットアップ

```bash
# プロジェクトのクローン
git clone <repository-url>
cd discord-obsidian-memo-bot

# 依存関係のインストール
uv sync
```

### 6. 環境変数の設定

`.env.example` ファイルをコピーして `.env.development` を作成：

```bash
cp .env.example .env.development
```

以下の項目を実際の値に更新してください：

```bash
# Discord 設定
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_GUILD_ID=your_discord_guild_id_here

# Google API 設定
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json
GOOGLE_CLOUD_SPEECH_API_KEY=your_speech_api_key_here

# Obsidian 設定
OBSIDIAN_VAULT_PATH=/path/to/your/obsidian/vault

# 必須チャンネルID設定
CHANNEL_INBOX=your_inbox_channel_id
CHANNEL_VOICE=your_voice_channel_id
CHANNEL_FILES=your_files_channel_id
CHANNEL_MONEY=your_money_channel_id
CHANNEL_FINANCE_REPORTS=your_finance_reports_channel_id
CHANNEL_TASKS=your_tasks_channel_id
CHANNEL_PRODUCTIVITY_REVIEWS=your_productivity_reviews_channel_id
CHANNEL_NOTIFICATIONS=your_notifications_channel_id
CHANNEL_COMMANDS=your_commands_channel_id

# レガシーチャンネル（オプション）
CHANNEL_ACTIVITY_LOG=your_activity_log_channel_id
CHANNEL_DAILY_TASKS=your_daily_tasks_channel_id

# 拡張チャンネル（オプション）
# Capture channels
CHANNEL_QUICK_NOTES=your_quick_notes_channel_id

# Finance channels
CHANNEL_INCOME=your_income_channel_id
CHANNEL_SUBSCRIPTIONS=your_subscriptions_channel_id

# Productivity channels
CHANNEL_PROJECTS=your_projects_channel_id
CHANNEL_WEEKLY_REVIEWS=your_weekly_reviews_channel_id
CHANNEL_GOAL_TRACKING=your_goal_tracking_channel_id

# Health channels（Garmin統合時）
CHANNEL_HEALTH_ACTIVITIES=your_health_activities_channel_id
CHANNEL_HEALTH_SLEEP=your_health_sleep_channel_id
CHANNEL_HEALTH_WELLNESS=your_health_wellness_channel_id
CHANNEL_HEALTH_ANALYTICS=your_health_analytics_channel_id

# System channels
CHANNEL_LOGS=your_logs_channel_id

# Garmin Connect 統合（オプション）
GARMIN_EMAIL=your_garmin_email@example.com
GARMIN_USERNAME=your_garmin_username
GARMIN_PASSWORD=your_garmin_password
GARMIN_CACHE_DIR=/path/to/garmin/cache
GARMIN_CACHE_HOURS=24.0

# API制限設定
GEMINI_API_DAILY_LIMIT=1500
GEMINI_API_MINUTE_LIMIT=15
SPEECH_API_MONTHLY_LIMIT_MINUTES=60

# ログ設定
LOG_LEVEL=INFO
LOG_FORMAT=json

# 環境設定
ENVIRONMENT=development

# セキュリティ設定（オプション）
GOOGLE_CLOUD_PROJECT=your_gcp_project_id
USE_SECRET_MANAGER=false
ENABLE_ACCESS_LOGGING=true
SECURITY_LOG_PATH=/path/to/security/logs

# Mock Mode 設定（開発・テスト用）
ENABLE_MOCK_MODE=false
MOCK_DISCORD_ENABLED=false
MOCK_GEMINI_ENABLED=false
MOCK_GARMIN_ENABLED=false
MOCK_SPEECH_ENABLED=false
```

### 7. Obsidian Vault の準備

```bash
# Obsidian Vault ディレクトリの作成
mkdir -p obsidian_vault

# 基本フォルダ構造の作成
mkdir -p obsidian_vault/{00_Inbox,01_Projects,02_DailyNotes,03_Ideas,04_Archive,05_Resources,06_Finance,07_Tasks,08_Health,99_Meta}

# テンプレートファイルの作成
mkdir -p obsidian_vault/99_Meta/templates
```

#### テンプレートファイルの作成

`obsidian_vault/99_Meta/templates/daily_note.md`:
```markdown
# {{date}}

## 📝 Daily Summary
{{summary}}

## 🎯 Key Activities
{{activities}}

## 💭 Ideas & Insights
{{ideas}}

## ✅ Tasks Completed
{{completed_tasks}}

## 📊 Metrics
- Messages processed: {{message_count}}
- AI requests: {{ai_requests}}
- Files created: {{files_created}}

## 🔄 Next Actions
{{next_actions}}
```

### 8. 動作確認

#### 基本テストの実行

```bash
# 全テストの実行
uv run pytest

# カバレッジ付きテスト
uv run pytest --cov=src

# 統合テストの実行
uv run pytest tests/integration/

# テストスクリプトを使った実行
python run_tests.py
```

#### ボットの起動テスト

```bash
# 開発モードでボット起動
uv run python -m src.main

# デバッグモードでの起動
uv run python -m src.main --debug
```

#### Discord での動作確認

1. ボットをDiscordサーバーに招待
2. `#bot-commands` チャンネルで `/help` コマンドを実行
3. `#inbox` チャンネルでメッセージを送信してみる

### 9. コード品質チェック

```bash
# フォーマットとリント（コミット前に実行）
uv run ruff check src/ --fix && uv run ruff format src/

# 型チェック
uv run mypy src/

# 全ての品質チェック
uv run ruff check src/ --fix && uv run ruff format src/ && uv run mypy src/

# pre-commitフックのセットアップ（オプション）
uv run pre-commit install
uv run pre-commit run --all-files
```

### 10. トラブルシューティング

#### よくある問題

**1. ボットが起動しない**
```bash
# ログレベルをDEBUGに変更して詳細を確認
LOG_LEVEL=DEBUG uv run python -m src.main

# 環境変数の確認
cat .env.development
```

**2. チャンネルが見つからない**
- チャンネルIDが正しいか確認（開発者モードでIDをコピー）
- ボットがサーバーに正しく追加されているか確認
- ボットの権限を確認（メッセージ送信、添付ファイル）

**3. APIエラー**
```bash
# APIキーの確認
echo $GEMINI_API_KEY
echo $DISCORD_BOT_TOKEN

# API制限の確認
# Gemini: 1500リクエスト/日, 15リクエスト/分
# Speech-to-Text: 60分/月（無料版）
```

**4. Obsidianファイルが作成されない**
```bash
# Obsidianパスの確認
ls -la obsidian_vault/
chmod -R 755 obsidian_vault/

# フォルダ構造の確認
tree obsidian_vault/
```

**5. Python依存関係の問題**
```bash
# 依存関係の再インストール
uv sync

# 開発依存関係も含めて
uv sync --dev
```

**6. Mock Mode での動作確認**
```bash
# Mock Mode を有効にしてテスト
ENABLE_MOCK_MODE=true uv run python -m src.main
```

### 11. 次のステップ

#### 本番環境へのデプロイ

```bash
# 本番環境用の設定
cp .env.development .env.production
# .env.production を本番環境用に編集（SECRET_MANAGER使用推奨）

# Cloud Run へのデプロイ
PROJECT_ID=your-project-id ./deploy.sh
```

#### カスタマイズ

1. **設定のカスタマイズ**
   - `src/config/settings.py` で基本設定
   - `.env.development` で環境固有設定

2. **テンプレートのカスタマイズ**
   - `obsidian_vault/99_Meta/templates/` でノートテンプレート
   - `src/obsidian/template_system.py` でテンプレート処理

3. **チャンネル設定のカスタマイズ**
   - `src/bot/channel_config.py` でチャンネルカテゴリ
   - 新しいチャンネルを追加する場合は設定ファイルも更新

4. **AI処理のカスタマイズ**
   - `src/ai/processor.py` でAI分析ロジック
   - プロンプトとカテゴリ分類の調整

#### 監視とヘルスチェック

```bash
# システム状態の確認
curl http://localhost:8080/health
curl http://localhost:8080/metrics

# ログの確認
tail -f logs/discord_bot.log
```

#### 高度な機能の有効化

1. **Garmin Connect統合**
   - Garmin認証情報を設定
   - ヘルスチャンネルを作成
   - `test_garmin_integration.py` でテスト

2. **高度なAI機能**
   - ベクトル検索の有効化
   - `test_advanced_ai.py` でテスト

3. **ヘルスデータ分析**
   - `test_health_analysis.py` でテスト

## サポート

- 技術的な質問: GitHubのIssueを作成
- ドキュメント: `docs/` ディレクトリを参照
- デプロイメント: `docs/deployment-guide.md` を参照

このガイドに従ってセットアップを完了すれば、Discord-Obsidian Memo Botが正常に動作するはずです。
