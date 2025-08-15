# Discord-Obsidian Memo Bot

DiscordのメッセージをAIで整理し、Obsidianに自動保存する個人用ボット

## 概要

このボットは、Discordに投稿したメッセージや音声ファイルを自動的にAIで分析・整理し、Obsidianのノートとして保存する個人用ナレッジマネジメントツールです。日常のメモ取りからデイリーノート作成まで、効率的な知識管理をサポートします。

## 主な機能

- **テキストメモの自動保存**: 指定したDiscordチャンネルの投稿をObsidianに保存
- **AIによる自動整理**: Google Gemini APIを使った自動要約・タグ付け・分類
- **音声メモの文字起こし**: 音声ファイルを自動でテキスト化して保存（オプション）
- **家計管理**: 支出記録、定期購読管理、家計レポート自動生成
- **タスク管理**: タスクの作成・追跡、生産性レビュー、スケジュール統合
- **健康データ統合**: Garmin Connect連携による健康データ追跡（オプション）
- **デイリーノート連携**: 特定のチャンネルへの投稿を、Obsidianのデイリーノートに追記
- **柔軟なテンプレート**: 保存するメモのフォーマットを自由にカスタマイズ
- **Vault統計**: ノート検索やVault全体の統計情報を表示

## 必要なもの

- Python 3.10以上
- [uv](https://github.com/astral-sh/uv) (高速なPythonパッケージ管理ツール)
- Discord Botトークン ([Discord Developer Portal](https://discord.com/developers/applications)で取得)
- Google Gemini APIキー ([Google AI Studio](https://aistudio.google.com/)で取得)
- Obsidian Vault（保管先のフォルダ）
- （オプション）Google Cloud Speech-to-Text APIの認証情報

## セットアップ手順

### 1. リポジトリのダウンロード
```bash
git clone https://github.com/kenvexar/discord-obsidian-memo-bot.git
cd discord-obsidian-memo-bot
```

### 2. 必要なライブラリのインストール
```bash
# uvがインストールされていない場合
pip install uv

# 依存関係のインストール
uv sync
```

### 3. 設定ファイルの準備
```bash
cp .env.example .env
```

### 4. 設定ファイルの編集
`.env`ファイルを開き、以下の項目を設定してください：

```env
# 必須設定
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_GUILD_ID=your_guild_id
GEMINI_API_KEY=your_gemini_api_key
OBSIDIAN_VAULT_PATH=/path/to/your/obsidian/vault

# チャンネルID（使用する機能に応じて設定）
CHANNEL_INBOX=123456789              # メイン用途（テキストメモ）
CHANNEL_VOICE=123456789              # 音声メモ用
CHANNEL_FILES=123456789              # ファイル添付メモ用
CHANNEL_MONEY=123456789              # 家計管理用
CHANNEL_FINANCE_REPORTS=123456789    # 家計レポート用
CHANNEL_TASKS=123456789              # タスク管理用
CHANNEL_PRODUCTIVITY_REVIEWS=123456789 # 生産性レビュー用
CHANNEL_NOTIFICATIONS=123456789      # システム通知用
CHANNEL_COMMANDS=123456789           # ボットコマンド用
CHANNEL_ACTIVITY_LOG=123456789       # アクティビティログ用
CHANNEL_DAILY_TASKS=123456789        # デイリータスク用

# オプション設定（音声認識を使う場合）
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

### 5. ボットの起動
```bash
uv run python -m src.main
```

コンソールに「Bot is ready!」と表示されれば成功です。

## 使い方

### 基本的な使い方
設定したチャンネルにメッセージを投稿するだけで、自動的に処理されObsidianに保存されます。

- **テキストメモ**: `#inbox` チャンネルにテキストを投稿
- **音声メモ**: `#voice` チャンネルに音声ファイルをアップロード
- **アクティビティログ**: `#activity-log` チャンネルへの投稿が今日のデイリーノートに追記
- **デイリータスク**: `#daily-tasks` チャンネルへの投稿がタスクとして記録

### Discordコマンド一覧

#### 基本コマンド
- `/help` - ヘルプ情報の表示
- `/status` - ボットの動作状況を確認
- `/ping` - 接続テスト

#### Obsidian管理
- `/vault_search [キーワード]` - Obsidian内のノートを検索
- `/vault_stats` - Vault統計情報の表示
- `/daily_note [日付]` - 指定日のデイリーノートを作成・表示

#### テンプレート機能
- `/list_templates` - 利用可能なテンプレート一覧
- `/create_from_template [template] [content]` - テンプレートからノート作成

## Obsidian Vaultの構造

ボットによって以下のような構造でファイルが保存されます：

```
Obsidian Vault/
├── 00_Capture/              # 新しいメモの受信箱
├── 01_Process/              # 処理中のメモ
├── 02_Knowledge/            # 整理済みの知識
├── 03_Projects/             # プロジェクト関連
├── 04_Life/                 # 日常・ライフ関連
│   ├── Daily/               # デイリーノート
│   ├── Finance/             # 家計関連
│   ├── Health/              # 健康関連
│   ├── Schedule/            # スケジュール
│   └── Tasks/               # タスク管理
├── 05_Resources/            # リソース・参考資料
└── 99_Meta/                 # メタデータ・設定
    └── Templates/           # カスタムテンプレート
```

## よくある質問 (FAQ)

### Q: ボットが反応しません
**A:** 以下を確認してください：
- `.env`ファイルのDiscordボットトークンが正しいか
- ボットがDiscordサーバーに参加しているか
- チャンネルIDが正しく設定されているか
- ボットに該当チャンネルの読み取り権限があるか

### Q: 音声認識が機能しません
**A:** 音声認識はオプション機能です：
- Google Cloud Speech-to-Text APIの設定が必要
- `GOOGLE_APPLICATION_CREDENTIALS`の設定が正しいか確認
- 認証JSONファイルのパスが正しいか確認

### Q: Obsidianにファイルが保存されません
**A:** 以下を確認してください：
- `OBSIDIAN_VAULT_PATH`が正しい絶対パスで設定されているか
- 指定したパスにObsidian Vaultが存在するか
- ディレクトリに書き込み権限があるか

### Q: Gemini APIの制限に達しました
**A:** 無料枠の制限に達した可能性があります：
- 1日1500リクエスト、1分間15リクエストの制限があります
- しばらく時間を置いてから再度お試しください
- 必要に応じて有料プランへのアップグレードを検討してください

## 注意事項

- このボットは個人利用を想定して設計されています
- APIの無料枠を効率的に活用するため、使用量制限が設定されています
- 音声認識機能は月60分の制限があります（Google Cloud Speech-to-Text無料枠）
