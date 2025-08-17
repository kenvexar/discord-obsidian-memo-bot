# 📦 詳細インストール手順

Discord-Obsidian Memo Botの完全なインストールと設定方法を説明します。全機能を活用したい場合はこちらのガイドに従ってください。

## 📋 目次

1. [システム要件](#システム要件)
2. [事前準備](#事前準備)
3. [本体インストール](#本体インストール)
4. [Discord設定](#discord設定)
5. [API設定](#api設定)
6. [チャンネル設定](#チャンネル設定)
7. [Obsidian設定](#obsidian設定)
8. [オプション機能](#オプション機能)
9. [動作確認](#動作確認)
10. [トラブルシューティング](#トラブルシューティング)

## 💻 システム要件

### 必須要件
- **OS**: macOS 10.15+, Ubuntu 20.04+, Windows 10+ (WSL2推奨)
- **Python**: 3.13以上
- **メモリ**: 最小512MB、推奨1GB以上
- **ディスク**: 最小1GB、推奨5GB以上（Obsidianボルト含む）
- **ネットワーク**: インターネット接続必須

### 推奨環境
- **CPU**: 2コア以上
- **メモリ**: 2GB以上
- **SSD**: 推奨（高速なファイルI/O）

## 🔧 事前準備

### 1. Python 3.13のインストール

**macOS (Homebrew)**
```bash
brew install python@3.13
python3.13 --version
```

**Ubuntu/Debian**
```bash
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.13 python3.13-venv python3.13-pip
```

**Windows (WSL2推奨)**
```bash
# WSL2 Ubuntu環境で上記Ubuntu手順を実行
```

### 2. uvパッケージマネージャーのインストール

```bash
# Unix系OS (macOS/Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 手動インストール
pip install uv

# インストール確認
uv --version
```

### 3. Gitのインストール

```bash
# macOS
brew install git

# Ubuntu
sudo apt install git

# Windows
# Git for Windows をダウンロード・インストール
```

## 📥 本体インストール

### 1. リポジトリの取得

```bash
# GitHubからクローン
git clone https://github.com/kenvexar/discord-obsidian-memo-bot.git
cd discord-obsidian-memo-bot

# プロジェクト構造確認
ls -la
```

### 2. 依存関係のインストール

```bash
# 本番用依存関係のインストール
uv sync

# 開発用依存関係も含める場合
uv sync --dev

# インストール済みパッケージ確認
uv pip list
```

### 3. 環境設定ファイルの準備

```bash
# サンプル設定をコピー
cp .env.example .env

# 設定ファイル確認
cat .env.example
```

## 🤖 Discord設定

### 1. Discord Botの作成

1. [Discord Developer Portal](https://discord.com/developers/applications)にアクセス
2. "New Application"をクリック
3. アプリケーション名を入力（例: "My Knowledge Bot"）
4. 作成後、アプリケーションIDをメモ

### 2. Botの設定

1. 左メニューから"Bot"を選択
2. "Add Bot"をクリック
3. Bot設定を行う：
   - **Public Bot**: オフ（個人利用のため）
   - **Requires OAuth2 Code Grant**: オフ
   - **Message Content Intent**: オン（必須）
   - **Server Members Intent**: オン（推奨）
   - **Presence Intent**: オフ

### 3. Botトークンの取得

1. "Token"セクションで"Copy"をクリック
2. トークンを安全な場所に保存
3. `.env`ファイルの`DISCORD_BOT_TOKEN`に設定

### 4. Bot権限の設定

1. 左メニューから"OAuth2" → "URL Generator"を選択
2. **Scopes**を選択：
   - `bot`
   - `applications.commands`

3. **Bot Permissions**を選択：
   - **Text Permissions**:
     - Send Messages
     - Send Messages in Threads
     - Embed Links
     - Attach Files
     - Read Message History
     - Add Reactions
   - **Voice Permissions**:
     - Connect
     - Speak
   - **General Permissions**:
     - Use Slash Commands

### 5. Botをサーバーに招待

1. 生成されたURLをコピー
2. URLにアクセスしてBotを招待
3. 適切なサーバーを選択
4. 権限を確認して認証

## 🔑 API設定

### 1. Google Gemini API

**APIキーの取得:**
1. [Google AI Studio](https://aistudio.google.com/)にアクセス
2. Googleアカウントでログイン
3. "Get API key"をクリック
4. "Create API key in new project"を選択
5. APIキーをコピーして`.env`の`GEMINI_API_KEY`に設定

**使用量制限の確認:**
- 無料版: 1日1500リクエスト、1分15リクエスト
- 有料版が必要な場合は[Google Cloud Console](https://console.cloud.google.com/)で設定

### 2. Google Cloud Speech-to-Text API（オプション）

**サービスアカウントの作成:**
1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. プロジェクトを作成または選択
3. "APIs & Services" → "Credentials"
4. "Create Credentials" → "Service Account"
5. サービスアカウント名を入力
6. 役割を選択: "Cloud Speech Client"
7. JSONキーをダウンロード

**設定:**
```bash
# サービスアカウントキーの配置
mkdir -p ~/.config/gcloud/
cp ~/Downloads/service-account-key.json ~/.config/gcloud/speech-key.json

# 環境変数設定
echo "GOOGLE_APPLICATION_CREDENTIALS=$HOME/.config/gcloud/speech-key.json" >> .env
```

### 3. Garmin Connect（オプション）

```env
# Garmin Connect認証情報
GARMIN_EMAIL=your_email@example.com
GARMIN_USERNAME=your_username
GARMIN_PASSWORD=your_password
```

## 📺 チャンネル設定

### 1. 必要なチャンネルの作成

Discordサーバーで以下のチャンネルを作成します：

**📝 CAPTURE カテゴリ（必須）:**
```
#inbox      - 汎用メモ入力
#voice      - 音声メモ
#files      - ファイル添付メモ
```

**💰 FINANCE カテゴリ（推奨）:**
```
#money              - 支出記録
#finance-reports    - 家計レポート自動生成
```

**📋 PRODUCTIVITY カテゴリ（推奨）:**
```
#tasks                   - タスク管理
#productivity-reviews    - 生産性レビュー
```

**⚙️ SYSTEM カテゴリ（必須）:**
```
#notifications    - ボット通知
#commands         - ボットコマンド
```

### 2. チャンネルIDの取得

1. Discordで開発者モードを有効化：
   - 設定 → 詳細設定 → 開発者モード をオン
2. 各チャンネルを右クリック → "IDをコピー"
3. `.env`ファイルに設定：

```env
# 基本チャンネル（必須）
CHANNEL_INBOX=123456789012345678
CHANNEL_VOICE=123456789012345679
CHANNEL_FILES=123456789012345680
CHANNEL_NOTIFICATIONS=123456789012345681
CHANNEL_COMMANDS=123456789012345682

# 金融管理（推奨）
CHANNEL_MONEY=123456789012345683
CHANNEL_FINANCE_REPORTS=123456789012345684

# タスク管理（推奨）
CHANNEL_TASKS=123456789012345685
CHANNEL_PRODUCTIVITY_REVIEWS=123456789012345686
```

### 3. サーバーIDの取得

1. Discordサーバー名を右クリック
2. "IDをコピー"をクリック
3. `.env`の`DISCORD_GUILD_ID`に設定

## 📚 Obsidian設定

### 1. Obsidianボルトの準備

**新規ボルトの作成:**
```bash
# ボルトディレクトリ作成
mkdir -p ~/Documents/ObsidianVault
cd ~/Documents/ObsidianVault

# 基本フォルダ構造作成
mkdir -p {00_Inbox,01_Projects,02_DailyNotes,03_Ideas,04_Archive,05_Resources,06_Finance,07_Tasks,08_Health,10_Attachments,99_Meta}

# テンプレートフォルダ作成
mkdir -p 99_Meta/Templates
```

**既存ボルトを使用する場合:**
```bash
# 既存ボルトパスを確認
ls -la /path/to/your/existing/vault

# .envファイルにパス設定
echo "OBSIDIAN_VAULT_PATH=/path/to/your/existing/vault" >> .env
```

### 2. テンプレートファイルの作成

**基本テンプレート:**
```bash
# デイリーノートテンプレート
cat > ~/Documents/ObsidianVault/99_Meta/Templates/daily_note.md << 'EOF'
# {{date}}

## 📝 Today's Summary
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

---
Created: {{timestamp}}
Tags: #daily-note
EOF
```

### 3. Obsidian設定

**プラグイン推奨設定:**
1. Obsidianでボルトを開く
2. 設定 → コミュニティプラグイン → セーフモードをオフ
3. 推奨プラグインをインストール：
   - Calendar
   - Templater
   - Dataview（高度な機能用）

## 🔧 オプション機能

### 1. 音声処理の有効化

```env
# Speech-to-Text設定
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
SPEECH_API_MONTHLY_LIMIT_MINUTES=60
```

### 2. 健康データ統合

```env
# Garmin Connect設定
GARMIN_EMAIL=your_email@example.com
GARMIN_USERNAME=your_username
GARMIN_PASSWORD=your_password
GARMIN_CACHE_HOURS=24.0

# 健康関連チャンネル
CHANNEL_HEALTH_ACTIVITIES=123456789012345687
CHANNEL_HEALTH_SLEEP=123456789012345688
```

### 3. 高度なAI機能

```env
# ベクトル検索の有効化
ENABLE_VECTOR_SEARCH=true

# キャッシュ設定
AI_CACHE_SIZE_MB=100
AI_CACHE_HOURS=24
```

### 4. セキュリティ設定

```env
# Google Cloud Secret Manager使用
USE_SECRET_MANAGER=false  # ローカル環境では通常false
GOOGLE_CLOUD_PROJECT=your-project-id

# アクセスログ
ENABLE_ACCESS_LOGGING=true
SECURITY_LOG_PATH=/path/to/security/logs
```

## ✅ 動作確認

### 1. 設定の検証

```bash
# 環境変数の確認
cat .env | grep -E "(DISCORD_|GEMINI_|OBSIDIAN_)"

# Python環境の確認
uv run python --version
uv run python -c "import discord; print('discord.py version:', discord.__version__)"
```

### 2. テスト実行

```bash
# 全テストの実行
uv run pytest

# 基本機能テスト
uv run pytest tests/unit/test_config.py -v

# 統合テスト
uv run pytest tests/integration/ -v
```

### 3. Bot起動とテスト

```bash
# Botを起動
uv run python -m src.main

# 別ターミナルで動作確認
# Discordで以下のコマンドを実行:
# /ping
# /status
# /help
```

### 4. 機能別テスト

**基本メモ機能:**
1. `#inbox`チャンネルにメッセージ投稿
2. Obsidianボルトに新しいファイルが作成されることを確認

**音声メモ機能:**
1. `#voice`チャンネルに音声ファイルをアップロード
2. 文字起こし結果がObsidianに保存されることを確認

**コマンド機能:**
1. `/vault_stats`で統計情報を確認
2. `/search_notes keyword`で検索機能を確認

## 🔧 トラブルシューティング

### よくある問題

**1. Botが起動しない**
```bash
# Python バージョン確認
python --version  # 3.13以上必要

# 依存関係の再インストール
uv sync --reinstall

# ログの確認
tail -f logs/bot.log
```

**2. Discord認証エラー**
```bash
# トークンの確認
echo $DISCORD_BOT_TOKEN

# Bot権限の確認
# Discord Developer Portalで権限設定を再確認
```

**3. Obsidianファイル作成エラー**
```bash
# パスと権限の確認
ls -la $OBSIDIAN_VAULT_PATH
chmod 755 $OBSIDIAN_VAULT_PATH

# フォルダ構造の確認
tree $OBSIDIAN_VAULT_PATH
```

**4. API制限エラー**
```bash
# Gemini API使用量確認
# Discordで `/ai_stats` コマンド実行

# Speech API確認
# Google Cloud Consoleで使用量確認
```

### デバッグモード

```bash
# 詳細ログでの起動
LOG_LEVEL=DEBUG uv run python -m src.main

# 特定モジュールのデバッグ
PYTHONPATH=src python -c "from src.config.settings import get_settings; print(get_settings())"
```

### サポート

問題が解決しない場合：
1. [トラブルシューティングガイド](../operations/troubleshooting.md)を確認
2. [GitHub Issues](https://github.com/kenvexar/discord-obsidian-memo-bot/issues)で問題を報告
3. ログファイルとエラーメッセージを添付

## 📚 次のステップ

インストールが完了したら：
1. **[基本的な使い方](basic-usage.md)** - 日常的な使用方法を学ぶ
2. **[コマンドリファレンス](commands-reference.md)** - 利用可能なコマンドを確認
3. **[高度な機能](advanced-features.md)** - より高度な機能を活用
4. **[設定オプション](../operations/configuration.md)** - 詳細な設定をカスタマイズ

---

このインストールガイドで全機能が利用可能になります。問題があれば遠慮なくサポートチャンネルで質問してください。
