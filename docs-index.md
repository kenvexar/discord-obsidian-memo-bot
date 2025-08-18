# Discord-Obsidian Memo Bot ドキュメントインデックス

このドキュメントインデックスは、 Discord-Obsidian Memo Bot の全ドキュメントへの包括的なナビゲーションを提供します。

## 📋 目次

- [クイックアクセス](#クイックアクセス)
- [ユーザー向けドキュメント](#ユーザー向けドキュメント)
- [開発者向けドキュメント](#開発者向けドキュメント)
- [運用者向けドキュメント](#運用者向けドキュメント)
- [リファレンス資料](#リファレンス資料)
- [ドキュメント使用ガイド](#ドキュメント使用ガイド)

## 🚀 クイックアクセス

### まず最初に読むべきドキュメント

| 目的 | ドキュメント | 推定読了時間 |
|------|-------------|--------------|
| **プロジェクト概要を知りたい** | [README.md](README.md) | 3 分 |
| **すぐに動かしたい** | [クイックスタート](docs/user/quick-start.md) | 10 分 |
| **基本的な使い方を学びたい** | [基本的な使い方](docs/user/basic-usage.md) | 15 分 |
| **問題を解決したい** | [トラブルシューティング](docs/operations/troubleshooting.md) | 適宜 |

### 役割別推奨読了順序

**🔰 初心者ユーザー**
1. [README.md](README.md) → 2. [クイックスタート](docs/user/quick-start.md) → 3. [基本的な使い方](docs/user/basic-usage.md)

**👤 一般ユーザー**
1. [インストール手順](docs/user/installation.md) → 2. [コマンドリファレンス](docs/user/commands-reference.md) → 3. [基本的な使い方](docs/user/basic-usage.md)

**👨‍💻 開発者**
1. [開発ガイド](docs/developer/development-guide.md) → 2. [アーキテクチャ](docs/developer/architecture.md) → 3. [コマンドリファレンス](docs/user/commands-reference.md)

**🚀 運用者**
1. [デプロイメント](docs/operations/deployment.md) → 2. [監視](docs/operations/monitoring.md) → 3. [トラブルシューティング](docs/operations/troubleshooting.md)

## 📚 ユーザー向けドキュメント

### 🏃‍♂️ はじめる
- **[クイックスタート](docs/user/quick-start.md)** - 10 分で動かす最短手順
- **[インストール手順](docs/user/installation.md)** - 詳細なセットアップ方法とトラブル対応

### 📖 使い方
- **[基本的な使い方](docs/user/basic-usage.md)** - 日常的な使い方とベストプラクティス
- **[使用例](docs/user/examples.md)** - 実際の使用例とワークフロー
- **[コマンドリファレンス](docs/user/commands-reference.md)** - 全 Discord コマンドの詳細仕様

### 💡 実践
- **[使用例とユースケース](docs/user/examples.md)** - 実際の使用例とワークフロー
- **[チュートリアル](docs/TUTORIAL.md)** - ステップバイステップのガイド

## 🛠️ 開発者向けドキュメント

### 🏗️ 設計・アーキテクチャ
- **[システムアーキテクチャ](docs/developer/architecture.md)** - 全体設計思想とモジュール構成

### 💻 開発
- **[開発環境構築](docs/developer/development-guide.md)** - 環境構築からデバッグまで
- **[ローカルテスト](docs/LOCAL_TESTING.md)** - 開発・テスト環境での動作確認

### 🤝 貢献
- **[セットアップガイド](docs/setup-guide.md)** - 詳細なセットアップ方法

## 🚀 運用者向けドキュメント

### 🏭 デプロイメント
- **[デプロイメントガイド](docs/operations/deployment.md)** - 本番環境へのデプロイ手順
- **[チャンネル管理](docs/CHANNEL_MANAGEMENT.md)** - 詳細なチャンネル設定方法

### 📊 監視・保守
- **[監視とログ](docs/operations/monitoring.md)** - ログ設定、メトリクス、アラート
- **[トラブルシューティング](docs/operations/troubleshooting.md)** - 問題解決手順

## 📖 リファレンス資料

### 🔧 技術仕様
- **[簡単セットアップ](docs/EASY_SETUP.md)** - チャンネル ID 設定不要の 5 分セットアップ
- **[コマンドリファレンス](docs/user/commands-reference.md)** - 全 Discord コマンドの詳細仕様

### 📋 その他
- **[使用例](docs/user/examples.md)** - 実際の使用例とワークフロー
- **[チュートリアル](docs/TUTORIAL.md)** - ステップバイステップのガイド

## 📚 ドキュメント使用ガイド

### ドキュメントの読み方

**🎯 目的別選択**
- **すぐ使いたい**: [クイックスタート](docs/user/quick-start.md) から開始
- **詳しく学びたい**: [インストール手順](docs/user/installation.md) → [基本的な使い方](docs/user/basic-usage.md) の順で読む
- **カスタマイズしたい**: [チャンネル管理](docs/CHANNEL_MANAGEMENT.md) → [使用例](docs/user/examples.md)

**🔍 検索と参照**
- 特定のコマンドを調べたい: [コマンドリファレンス](docs/user/commands-reference.md)
- セットアップで困ったら: [簡単セットアップ](docs/EASY_SETUP.md)
- 問題を解決したい: [トラブルシューティング](docs/operations/troubleshooting.md)

### ドキュメント構造の説明

```
docs/
├── user/                    # エンドユーザー向け
│   ├── quick-start.md      # 最小限の手順（ 10 分で動かす）
│   ├── installation.md     # 詳細なセットアップ
│   ├── basic-usage.md      # 日常的な使用方法
│   ├── commands-reference.md # コマンド完全リファレンス
│   └── examples.md         # 実用例とユースケース
│
├── developer/               # 開発者向け
│   ├── architecture.md     # システム設計
│   └── development-guide.md # 開発環境とワークフロー
│
├── operations/              # 運用者向け
│   ├── deployment.md       # デプロイメント手順
│   ├── monitoring.md       # 監視・ログ
│   └── troubleshooting.md  # 問題解決
│
├── EASY_SETUP.md             # 5 分セットアップガイド
├── CHANNEL_MANAGEMENT.md     # チャンネル管理ガイド
├── LOCAL_TESTING.md          # ローカルテスト手順
├── TUTORIAL.md               # ステップバイステップガイド
└── setup-guide.md            # 詳細セットアップ
```

### 貢献とフィードバック

このドキュメントの改善にご協力ください：

- **誤字・脱字を見つけた**: [Issue](https://github.com/kenvexar/discord-obsidian-memo-bot/issues) を作成
- **説明が不明確**: [Issue](https://github.com/kenvexar/discord-obsidian-memo-bot/issues) で詳細を報告
- **新しいセクションが必要**: [Discussion](https://github.com/kenvexar/discord-obsidian-memo-bot/discussions) で提案
- **実際に貢献したい**: [セットアップガイド](docs/setup-guide.md) を参照

---

**ドキュメント最終更新**: 2025 年 8 月 18 日
**バージョン**: 0.1.0
