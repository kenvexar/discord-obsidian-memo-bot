# Discord-Obsidian Memo Bot

Discord上でメモ入力、家計管理、タスク管理を行い、AI処理を経てObsidianに自動保存する包括的なライフログ・ナレッジマネジメントシステム

## 概要

このボットは、Discordを統合インターフェースとして使用し、Google Gemini APIによるAI処理を経てObsidianに自動保存する包括的なライフログ・ナレッジマネジメントシステムです。ツェッテルカステンとライフログの概念を取り入れ、メモ管理、家計管理、タスク管理を統合した体系的なナレッジ管理を支援します。

## 主な機能

### 📝 メモ・ナレッジ管理
- 複数のDiscordチャンネルからのメモ自動取得
- 🎤 音声メモのテキスト変換（Google Cloud Speech-to-Text）
- 🤖 AI による要約・分類・関連性分析（Google Gemini API）
- � GObsidian Vaultへの自動保存と整理
- 💪 Garmin健康データの統合

### 💰 家計管理
- 定期購入サービス管理（Netflix、Spotify、SaaS等）
- 支払いリマインダーと自動通知
- 収支トラッキングと予算管理
- AI による家計レポート生成

### 📋 タスク・スケジュール管理
- タスク作成・進捗管理
- 期限リマインダーシステム
- スケジュール管理
- 生産性分析レポート

### ☁️ インフラ
- Google Cloud Run での24時間365日稼働（無料枠）
- 完全な日本語対応
- セキュアな認証情報管理

## システム構成

- **Discord Bot**: Discord.py
- **AI処理**: Google Gemini API Free Tier
- **音声認識**: Google Cloud Speech-to-Text API
- **健康データ**: python-garminconnect
- **デプロイメント**: Google Cloud Run（無料枠）

## Obsidian Vault構造

```
00_Capture/        # 即座のキャプチャ（未分類メモ）
01_Process/        # 処理待ちアイテム
02_Knowledge/      # 永続的な知識ベース
03_Projects/       # プロジェクト関連
04_Life/           # ライフログ統合
  ├── Daily/       # デイリーノート
  ├── Finance/     # 家計管理
  ├── Health/      # 健康データ
  ├── Tasks/       # タスク管理
  └── Schedule/    # スケジュール管理
05_Resources/      # リソース・添付ファイル
99_Meta/           # テンプレート・システム設定
```

## Discord チャンネル構成

### 📝 CAPTURE
- #inbox: 全般的なメモ・アイデア・活動ログ
- #voice: 音声メモ専用
- #files: ファイル添付専用

### 💰 FINANCE
- #money: 収支記録・定期購入管理
- #reports: 家計レポート・統計

### 📋 PRODUCTIVITY
- #tasks: タスク・スケジュール管理
- #reviews: 振り返り・統計レポート

### ⚙️ SYSTEM
- #notifications: システム通知・リマインダー
- #commands: コマンド実行専用

## セットアップ

詳細なセットアップ手順は [docs/setup.md](docs/setup.md) を参照してください。

## 使用方法

### 基本的なメモ入力
指定されたチャンネルにメッセージを投稿するだけで、自動的にAI処理されObsidianに保存されます。

### 家計管理
💰 FINANCEカテゴリの#moneyチャンネルで支出・収入を記録し、定期購入サービスを管理できます。
- #moneyに「支出 コンビニ 500円 食費」と投稿で支出記録
- #moneyに「収入 給与 300000円」と投稿で収入記録
- 定期購入は自動リマインダーで支払い忘れを防止
- #reportsで月次家計レポートを自動受信

### タスク・スケジュール管理
📋 PRODUCTIVITYカテゴリの#tasksチャンネルで効率的なタスク管理とスケジュール管理が可能です。
- タスクの期限管理と進捗トラッキング
- 自動リマインダーで重要なタスクを見落とし防止
- #reviewsで生産性分析レポートを受信し改善点を把握

### コマンド

#### 基本コマンド
- `/help`: 利用可能なコマンド一覧
- `/status`: システム状態確認
- `/search [キーワード]`: Vault内検索
- `/stats`: 統計情報表示
- `/random_note`: ランダムノート表示

#### 家計管理コマンド
- `/sub_add [サービス名] [金額] [周期] [次回支払日]`: 定期購入追加
- `/sub_paid [サービス名]`: 支払い完了報告
- `/sub_list`: 定期購入一覧表示
- `/sub_stats [期間]`: 家計統計表示
- `/budget_set [カテゴリ] [予算]`: 予算設定
- `/finance_stats [期間]`: 収支バランス表示

#### タスク管理コマンド
- `/task_add [タスク名] [期限] [優先度] [説明]`: タスク作成
- `/task_update [タスク名] [進捗率]`: 進捗更新
- `/task_done [タスク名]`: タスク完了報告
- `/task_list`: アクティブタスク一覧
- `/schedule_add [イベント名] [日時] [場所] [説明]`: スケジュール作成
- `/task_stats [期間]`: タスク統計表示

## 開発

### 要件
- Python 3.9+
- Discord Bot Token
- Google Cloud API Keys
- Garmin Connect アカウント

### ローカル開発
```bash
pip install -r requirements.txt
python -m pytest tests/
python src/main.py
```

## ライセンス

MIT License

## 貢献

プルリクエストやイシューの報告を歓迎します。## 特徴


### 🎯 統合管理
- メモ、家計、タスクを一つのシステムで統合管理
- すべてのデータがObsidianで一元化され、横断的な分析が可能
- デイリーノートで日々の活動を包括的に記録

### 🤖 AI支援
- Google Gemini APIによる自動要約・分類
- 関連ノートの自動提案
- 家計・タスクの改善提案
- 月次レポートの自動生成

### 💸 コスト効率
- Google Cloud Runの無料枠で24時間稼働
- Google Gemini API、Speech-to-Text APIの無料枠を活用
- 追加コストなしで包括的なライフログシステムを構築

### 🔒 セキュリティ
- Google Cloud Secret Managerによる認証情報管理
- 個人データの暗号化保存
- アクセスログの記録

## API使用量管理

システムは無料枠を効率的に活用するよう設計されています：

- **Gemini API**: 月15リクエスト/分、1日1500リクエスト
- **Speech-to-Text API**: 月60分
- **Cloud Run**: 月180,000 vCPU秒、200万リクエスト

使用量が80%に達すると自動警告が送信され、制限到達時は基本機能のみで動作を継続します。

## 仕様書

詳細な仕様書は以下をご参照ください：

- [要件定義書](.kiro/specs/discord-obsidian-memo-bot/requirements.md)
- [設計書](.kiro/specs/discord-obsidian-memo-bot/design.md)
- [実装計画](.kiro/specs/discord-obsidian-memo-bot/tasks.md)