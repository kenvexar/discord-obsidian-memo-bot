# チャンネル管理ガイド

Discord-Obsidian Memo Botは、Discordチャンネルを名前で自動検出します。面倒なチャンネルIDの設定は一切不要で、標準的なチャンネル名を作成するだけで動作します。

## 概要

ボットは起動時に、事前定義された標準チャンネル名を自動的に検索し、見つかったチャンネルを自動設定します。チャンネルIDをコピペしたり、環境変数に設定する必要はありません。

## サポートされるチャンネル

### コアチャンネル（必須）

| 設定名 | Discord チャンネル名 | 用途 |
|--------|-------------------|------|
| `CHANNEL_INBOX` | `inbox` | メインのメモ投稿チャンネル |
| `CHANNEL_VOICE` | `voice` | 音声メモのアップロード |
| `CHANNEL_FILES` | `files` | ファイルアップロード |
| `CHANNEL_MONEY` | `money` | 支出・収入の記録 |
| `CHANNEL_FINANCE_REPORTS` | `finance-reports` | 財務レポートと分析 |
| `CHANNEL_TASKS` | `tasks` | タスク管理 |
| `CHANNEL_PRODUCTIVITY_REVIEWS` | `productivity-reviews` | 日次生産性レビュー |
| `CHANNEL_NOTIFICATIONS` | `notifications` | システム通知 |
| `CHANNEL_COMMANDS` | `commands` | ボットコマンド実行 |

### オプションチャンネル

| 設定名 | Discord チャンネル名 | 用途 |
|--------|-------------------|------|
| `CHANNEL_QUICK_NOTES` | `quick-notes` | AI処理なしのクイックメモ |
| `CHANNEL_INCOME` | `income` | 収入専用記録 |
| `CHANNEL_SUBSCRIPTIONS` | `subscriptions` | サブスクリプション管理 |
| `CHANNEL_PROJECTS` | `projects` | プロジェクト管理 |
| `CHANNEL_WEEKLY_REVIEWS` | `weekly-reviews` | 週次レビュー |
| `CHANNEL_GOAL_TRACKING` | `goal-tracking` | 目標追跡 |

### ヘルスチャンネル

| 設定名 | Discord チャンネル名 | 用途 |
|--------|-------------------|------|
| `CHANNEL_HEALTH_ACTIVITIES` | `health-activities` | 運動・活動記録 |
| `CHANNEL_HEALTH_SLEEP` | `health-sleep` | 睡眠記録 |
| `CHANNEL_HEALTH_WELLNESS` | `health-wellness` | 総合健康管理 |
| `CHANNEL_HEALTH_ANALYTICS` | `health-analytics` | 健康データ分析 |

### レガシーチャンネル（後方互換性）

| 設定名 | Discord チャンネル名 | 用途 |
|--------|-------------------|------|
| `CHANNEL_ACTIVITY_LOG` | `activity-log` | 活動ログ |
| `CHANNEL_DAILY_TASKS` | `daily-tasks` | 日次タスク |
| `CHANNEL_LOGS` | `logs` | システムログ |

## セットアップ方法

### 1. Discordでチャンネルを作成

Discordサーバーで、上記の表に記載されたチャンネル名でテキストチャンネルを作成します。

例：
```
📝 inbox
🎤 voice
📎 files
💰 money
📊 finance-reports
✅ tasks
📋 productivity-reviews
🔔 notifications
🤖 commands
```

### 2. ボットの起動

**それだけです！** 環境変数でのチャンネルID設定は不要です。

ボット起動時に、作成されたチャンネルが自動的に検出され、利用可能になります。

## 使用方法

### プログラムでのチャンネルアクセス

```python
# ChannelConfigインスタンスを取得
channel_config = bot.channel_config

# チャンネル名でアクセス
inbox_channel = channel_config.get_channel_by_name("inbox")
voice_channel = channel_config.get_channel_by_name("voice")

# 便利なヘルパーメソッド
inbox_channel = channel_config.get_inbox_channel()
expenses_channel = channel_config.get_expenses_channel()
tasks_channel = channel_config.get_tasks_channel()

# パターンマッチング
finance_channels = channel_config.find_channels_by_name_pattern("finance.*")
health_channels = channel_config.find_channels_by_name_pattern("health.*")

# 監視状態の確認
if channel_config.is_monitored_channel_by_name("inbox"):
    print("Inbox channel is being monitored")

# 全監視チャンネル名の取得
monitored_names = channel_config.get_all_monitored_channel_names()
```

### 自動チャンネル検出

ボットは起動時に以下の処理を実行します：

1. 標準チャンネル名のリストを取得
2. Discordサーバー内で該当する名前のチャンネルを検索
3. 見つかったチャンネルを自動設定
4. 見つからない必須チャンネルについて警告を出力

## トラブルシューティング

### チャンネルが見つからない場合

```
WARNING: Required channel not found channel_name=inbox
```

**解決方法：**
1. Discordサーバーに該当チャンネルが存在するか確認
2. チャンネル名のスペルが正確か確認（小文字、ハイフン区切り）
3. ボットがサーバーにアクセス権限を持っているか確認

### 重複チャンネル名

同じ名前のチャンネルが複数存在する場合、最初に見つかったチャンネルが使用されます。

**推奨解決方法：**
- チャンネル名をユニークにする
- カテゴリで整理する

### 権限エラー

```
PermissionError: Bot cannot access channel
```

**解決方法：**
1. ボットにチャンネルの読み取り権限があるか確認
2. ボットにメッセージ送信権限があるか確認
3. サーバー管理者にボット権限の確認を依頼

## ベストプラクティス

### 1. チャンネル命名規則

- 英小文字とハイフンのみを使用
- 意味のある分かりやすい名前を付ける
- カテゴリごとにプレフィックスを使用（例：`finance-reports`, `health-sleep`）

### 2. チャンネル整理

Discordサーバーでカテゴリを作成して整理：

```
📝 MEMO SYSTEM
  ├── inbox
  ├── voice
  └── files

💰 FINANCE
  ├── money
  ├── income
  ├── subscriptions
  └── finance-reports

✅ PRODUCTIVITY
  ├── tasks
  ├── projects
  ├── productivity-reviews
  └── goal-tracking

🏃 HEALTH
  ├── health-activities
  ├── health-sleep
  ├── health-wellness
  └── health-analytics

🔧 SYSTEM
  ├── notifications
  ├── commands
  └── logs
```

### 3. 段階的導入

1. **最小構成**：`inbox`, `voice`, `money`, `tasks`, `notifications`, `commands`
2. **基本構成**：上記 + `files`, `finance-reports`, `productivity-reviews`
3. **完全構成**：全チャンネルを作成

### 4. 監視と保守

- ボット起動ログでチャンネル検出状況を確認
- 定期的にチャンネル権限を確認
- 不要になったチャンネルは環境変数からも削除

## 移行ガイド

### 既存設定からの移行

現在チャンネルIDのみで設定している場合：

1. **段階的移行**：
   - 既存のチャンネルIDは継続使用
   - 新しく対応するチャンネル名のチャンネルを作成
   - ボット再起動で両方が利用可能になる

2. **完全移行**：
   - 全ての必要チャンネルを適切な名前で作成
   - 環境変数は従来通り設定（後方互換性のため）
   - ボット再起動で新システムが有効化

### 注意事項

- チャンネルIDベースの機能は引き続きサポート
- 急激な変更は避け、段階的に移行を推奨
- テスト環境で動作確認後、本番環境に適用

## API リファレンス

詳細なAPIドキュメントについては、ソースコード内のdocstringを参照してください：

- `src/bot/channel_config.py` - チャンネル管理の主要クラス
- `src/config/settings.py` - 設定管理
