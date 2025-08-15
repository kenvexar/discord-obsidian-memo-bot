# Discord-Obsidian Memo Bot セットアップガイド

## 初回セットアップ手順

### 1. 前提条件の確認

#### 必要なソフトウェア
- Python 3.10以上
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

**📝 INBOX/CAPTURE カテゴリ:**
- `#inbox` - 汎用メモ入力
- `#voice` - 音声メモ
- `#files` - ファイル添付メモ

**💡 IDEAS/INSIGHTS カテゴリ:**
- `#ideas` - アイデア・洞察

**✅ TASKS/LOGS カテゴリ:**
- `#activity-log` - 活動ログ
- `#daily-tasks` - 日次タスク

**💰 FINANCE カテゴリ:**
- `#money` - 家計管理（支出記録、定期購読管理）
- `#finance-reports` - 家計レポート（自動レポート出力）

**📋 TASKS カテゴリ:**
- `#tasks` - タスク管理（作成・追跡・完了）
- `#productivity-reviews` - 生産性レビュー（週次・月次レビュー）

**⚙️ システム管理:**
- `#bot-notifications` - ボット通知
- `#bot-commands` - ボットコマンド

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

`.env.development` ファイルを作成：

```bash
# コア設定
ENVIRONMENT=development
ENABLE_MOCK_MODE=false

# Discord 設定
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_GUILD_ID=your_guild_id_here

# API設定
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_CLOUD_SPEECH_API_KEY=your_speech_api_key_here

# Obsidian設定
OBSIDIAN_VAULT_PATH=./obsidian_vault

# チャンネルID設定
CHANNEL_INBOX=123456789012345678
CHANNEL_VOICE=123456789012345679
CHANNEL_FILES=123456789012345680
CHANNEL_MONEY=123456789012345681
CHANNEL_FINANCE_REPORTS=123456789012345682
CHANNEL_TASKS=123456789012345683
CHANNEL_PRODUCTIVITY_REVIEWS=123456789012345684
CHANNEL_NOTIFICATIONS=123456789012345685
CHANNEL_COMMANDS=123456789012345686
CHANNEL_ACTIVITY_LOG=123456789012345687
CHANNEL_DAILY_TASKS=123456789012345688

# Garmin Connect 統合（オプション）
GARMIN_EMAIL=your_garmin_email@example.com
GARMIN_PASSWORD=your_garmin_password
GARMIN_CACHE_DIR=./garmin_cache
GARMIN_CACHE_HOURS=24.0

# セキュリティ設定（本番環境）
GOOGLE_CLOUD_PROJECT=your-project-id
USE_SECRET_MANAGER=false
ENABLE_ACCESS_LOGGING=true

# Mock Mode 設定（開発・テスト用）
ENABLE_MOCK_MODE=false
MOCK_DISCORD_ENABLED=false
MOCK_GEMINI_ENABLED=false
MOCK_GARMIN_ENABLED=false
MOCK_SPEECH_ENABLED=false

# API制限設定
GEMINI_API_DAILY_LIMIT=1500
SPEECH_API_MONTHLY_LIMIT_MINUTES=60

# ログ設定
LOG_LEVEL=INFO
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
# 基本動作テスト
python run_tests.py
```

#### ボットの起動テスト

```bash
# 開発モードでボット起動
uv run python src/main.py
```

#### Discord での動作確認

1. ボットをDiscordサーバーに招待
2. `#bot-commands` チャンネルで `/help` コマンドを実行
3. `#inbox` チャンネルでメッセージを送信してみる

### 9. トラブルシューティング

#### よくある問題

**1. ボットが起動しない**
```bash
# ログレベルをDEBUGに変更して詳細を確認
LOG_LEVEL=DEBUG uv run python src/main.py
```

**2. チャンネルが見つからない**
- チャンネルIDが正しいか確認
- ボットがサーバーに正しく追加されているか確認
- ボットの権限を確認

**3. APIエラー**
```bash
# APIキーの確認
echo $GEMINI_API_KEY
echo $DISCORD_BOT_TOKEN
```

**4. Obsidianファイルが作成されない**
```bash
# Obsidianパスの確認
ls -la obsidian_vault/
chmod -R 755 obsidian_vault/
```

### 10. 次のステップ

#### 本番環境へのデプロイ

```bash
# 本番環境用の設定
cp .env.development .env.production
# .env.production を本番環境用に編集

# Cloud Run へのデプロイ
PROJECT_ID=your-project-id ./deploy.sh
```

#### カスタマイズ

1. `src/config/settings.py` で設定をカスタマイズ
2. `obsidian_vault/99_Meta/templates/` でテンプレートをカスタマイズ
3. `src/bot/channel_config.py` でチャンネル設定をカスタマイズ

#### 監視の設定

```bash
# システム状態の確認
curl http://localhost:8080/health
curl http://localhost:8080/metrics
```

## サポート

- 技術的な質問: GitHubのIssueを作成
- ドキュメント: `docs/` ディレクトリを参照
- デプロイメント: `docs/deployment-guide.md` を参照

このガイドに従ってセットアップを完了すれば、Discord-Obsidian Memo Botが正常に動作するはずです。
