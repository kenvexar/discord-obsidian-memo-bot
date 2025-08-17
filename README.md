# Discord-Obsidian Memo Bot

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

AI駆動の個人ナレッジマネジメントシステム - Discordを介してメモを収集し、自動的にObsidianで整理

## 概要

Discord-Obsidian Memo Botは、Discordを統合インターフェースとして使用し、AI分析による自動メモ処理とObsidianナレッジベースへの保存を提供する包括的な個人ナレッジマネジメントシステムです。

### 主要機能

🤖 **AI駆動の自動処理**
- Google Gemini AIによるメッセージの自動分析・分類・要約
- URLコンテンツの自動取得と要約
- インテリジェントなタグ付けとカテゴリ分類

🎤 **音声メモ対応**
- Google Cloud Speech-to-Textによる高精度音声認識
- 複数音声フォーマット対応（MP3, WAV, FLAC, OGG, M4A, WEBM）

📝 **Obsidian完全統合**
- 構造化Markdownノートの自動生成
- 内容に基づく自動フォルダ分類
- デイリーノートとの統合
- 柔軟なテンプレートシステム

💰 **金融管理機能**
- 支出・収入の自動記録と分類
- 定期購入（サブスクリプション）管理
- 自動家計レポート生成

✅ **タスク・プロジェクト管理**
- メッセージからのタスク自動抽出
- プロジェクト進捗追跡
- 生産性レビューの自動生成

🏃‍♂️ **健康データ統合**（オプション）
- Garmin Connect統合による活動データ同期
- 睡眠・運動パターンの分析

## クイックスタート

### 1. 前提条件
- Python 3.13以上
- [uv](https://github.com/astral-sh/uv)（高速Pythonパッケージマネージャー）
- Discord Botトークン
- Google Gemini APIキー
- Obsidianボルト

### 2. インストール
```bash
# リポジトリのクローン
git clone https://github.com/kenvexar/discord-obsidian-memo-bot.git
cd discord-obsidian-memo-bot

# 依存関係のインストール
uv sync

# 環境設定
cp .env.example .env
# .envファイルを編集してAPIキーを設定
```

### 3. 基本設定

```env
# 必須設定項目のみ
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_GUILD_ID=your_guild_id
GEMINI_API_KEY=your_gemini_api_key
OBSIDIAN_VAULT_PATH=/path/to/your/obsidian/vault
```

**それだけです！** チャンネルIDの設定は不要です。

### 4. 起動
```bash
uv run python -m src.main
```

### 5. Discordチャンネル作成

以下のチャンネルを作成するだけ：
```
📝 inbox          ← メインメモ（必須）
🔔 notifications  ← システム通知（必須）
🤖 commands       ← ボットコマンド（必須）
```

追加機能が必要なら：
```
🎤 voice     ← 音声メモ
📎 files     ← ファイル
💰 money     ← 家計簿
✅ tasks     ← タスク管理
```

### 6. 使用開始
設定したDiscordチャンネルにメッセージを投稿するだけ！AIが自動的に処理してObsidianに保存します。

> **✨ 特徴：チャンネルID設定不要**
> 標準的なチャンネル名（`inbox`, `voice`, `money`等）で自動検出します。
> 面倒なチャンネルIDのコピペは不要です！

## ドキュメント

詳細な情報については、以下のドキュメントをご参照ください：

### 📚 ユーザー向け
- **[簡単セットアップガイド](docs/EASY_SETUP.md)** - 🆕 チャンネルID設定不要の5分セットアップ
- **[チャンネル管理ガイド](docs/CHANNEL_MANAGEMENT.md)** - 詳細なチャンネル設定方法
- **[ローカルテスト手順](docs/LOCAL_TESTING.md)** - 開発・テスト環境での動作確認

### 🛠️ 開発者向け
- **[開発ガイド](docs/developer/development-guide.md)** - 開発環境構築
- **[アーキテクチャ](docs/developer/architecture.md)** - システム設計
- **[API仕様](docs/developer/api-reference.md)** - API詳細
- **[コントリビューション](docs/developer/contributing.md)** - 貢献方法

### 🚀 運用者向け
- **[デプロイメント](docs/operations/deployment.md)** - 本番環境へのデプロイ
- **[トラブルシューティング](docs/operations/troubleshooting.md)** - 問題解決
- **[監視](docs/operations/monitoring.md)** - 監視とログ管理

### 📖 完全ガイド
すべての情報を網羅した **[ドキュメントインデックス](docs-index.md)** も利用可能です。

## 主な特徴

### 🎯 ゼロ設定の自動化
メッセージを投稿するだけで、AIが内容を分析し適切なフォルダに構造化して保存

### 🔄 シームレスな統合
Discord ↔ AI処理 ↔ Obsidian の完全自動化されたワークフロー

### 🧠 インテリジェントな分類
機械学習による内容の自動分類とタグ付け

### 📊 包括的な管理
メモ、タスク、金融、健康データを一元管理

### 🔒 セキュリティ重視
Google Cloud Secret Managerによる安全な認証情報管理

## サポートされる環境

- **開発**: ローカル開発環境（モックモード対応）
- **本番**: Google Cloud Run（24時間365日稼働）
- **コンテナ**: Docker対応
- **OS**: macOS, Linux, Windows（WSL2）

## コミュニティとサポート

- **Issues**: [GitHub Issues](https://github.com/kenvexar/discord-obsidian-memo-bot/issues)でバグ報告・機能要求
- **Discussions**: プロジェクトについて議論
- **Documentation**: 包括的なドキュメントでサポート

## ライセンス

MIT License - 詳細は[LICENSE](LICENSE)ファイルをご覧ください。

## 貢献

プロジェクトへの貢献を歓迎します！詳細は[コントリビューションガイド](docs/developer/contributing.md)をご確認ください。

---

**プロジェクト情報**
- バージョン: 0.1.0
- Python要求バージョン: 3.13以上
- メンテナー: Kent
- 最終更新: 2025年8月17日
