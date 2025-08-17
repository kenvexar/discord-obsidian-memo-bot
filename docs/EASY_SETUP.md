# 簡単セットアップガイド

Discord-Obsidian Memo Botを**チャンネルIDの設定なし**で5分で動かす最短手順です。

## 🚀 クイックスタート

### 1. 必要なもの

- Discord Botトークン
- Google Gemini APIキー
- Obsidianフォルダのパス

### 2. チャンネル作成（3つだけ）

Discordサーバーに以下のテキストチャンネルを作成：

```
📝 inbox          ← メモ投稿用（必須）
🔔 notifications  ← ボット通知用（必須）
🤖 commands       ← ボットコマンド用（必須）
```

**これだけです！** チャンネルIDをコピーする必要はありません。

### 3. 設定ファイル

```bash
# 設定例をコピー
cp .env.names-only.example .env

# 設定を編集
vim .env
```

**`.env`ファイルの編集（3つだけ）:**

```env
DISCORD_BOT_TOKEN=あなたのBotトークン
DISCORD_GUILD_ID=あなたのDiscordサーバーID
GEMINI_API_KEY=あなたのGemini APIキー
OBSIDIAN_VAULT_PATH=/path/to/obsidian/vault

USE_CHANNEL_NAMES_ONLY=true
```

### 4. 起動

```bash
uv run python -m src.main
```

### 5. 完了！

- `#inbox`チャンネルにメッセージを投稿
- ボットが自動的に処理してObsidianに保存
- `#notifications`で処理状況を確認

## 🔧 追加チャンネル（オプション）

より多くの機能が欲しい場合は、以下のチャンネルを追加：

```
🎤 voice           ← 音声メモ
📎 files           ← ファイルアップロード
💰 money           ← 家計簿・支出管理
✅ tasks           ← タスク管理
```

**ボットを再起動すると自動的に検出されます。**

## 🏗️ Discord サーバー構成例

カテゴリで整理すると見やすくなります：

```
📝 MEMO SYSTEM
  ├── inbox
  ├── voice
  └── files

💼 PRODUCTIVITY
  ├── tasks
  └── projects

💰 FINANCE
  ├── money
  └── finance-reports

🔧 SYSTEM
  ├── notifications
  ├── commands
  └── logs
```

## ⚡ メリット

### 従来の方式
```env
# 😫 面倒...
CHANNEL_INBOX=123456789012345678
CHANNEL_VOICE=987654321098765432
CHANNEL_TASKS=456789123456789123
CHANNEL_NOTIFICATIONS=789123456789123456
# ... 10個以上のチャンネルID
```

### 新しい方式
```env
# 😊 簡単！
USE_CHANNEL_NAMES_ONLY=true
# チャンネルは名前で自動検出
```

## 🔍 トラブルシューティング

### ボットがチャンネルを見つけられない

**症状:** `Required channel not found` エラー

**解決方法:**
1. チャンネル名が正確か確認（`inbox`, `notifications`, `commands`）
2. ボットにチャンネル表示権限があるか確認
3. `DISCORD_GUILD_ID`が正しいか確認

### ボットがメッセージに反応しない

**症状:** メッセージを投稿しても何も起こらない

**解決方法:**
1. ボットがオンラインか確認
2. ボットにメッセージ読み取り権限があるか確認
3. `#notifications`チャンネルでエラーメッセージを確認

### セットアップ状況の確認

ボット起動時のログを確認：
```
INFO: Auto-discovered channel channel_name=inbox channel_id=123456789
INFO: Channel auto-discovery completed discovered_count=3 mode=name-only
```

または、Pythonで確認：
```python
from src.bot.channel_config import ChannelConfig
from src.config import get_settings

# セットアップ状況を確認
config = ChannelConfig()
status = config.get_channel_setup_status()
print(status)

# 不足チャンネルの確認
suggestions = config.suggest_channel_setup()
print(suggestions)
```

## 🔄 従来設定からの移行

既にチャンネルIDで設定済みの場合：

1. **そのまま使える**: 既存設定は動作し続けます
2. **段階的移行**: `USE_CHANNEL_NAMES_ONLY=true`を追加するだけ
3. **完全移行**: チャンネルIDの環境変数を削除可能

## 📚 より詳しく

- **完全なチャンネル管理ガイド**: [docs/CHANNEL_MANAGEMENT.md](CHANNEL_MANAGEMENT.md)
- **開発者向けドキュメント**: [CLAUDE.md](../CLAUDE.md)
- **プロジェクト概要**: [README.md](../README.md)
