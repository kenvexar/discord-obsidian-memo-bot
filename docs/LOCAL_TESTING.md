# ローカルテスト手順

このドキュメントでは、Discord-Obsidian Memo Botをローカル環境でテストする方法について説明します。

## 📋 目次

1. [開発環境セットアップ](#開発環境セットアップ)
2. [モックモードでのテスト](#モックモードでのテスト)
3. [個別機能テスト](#個別機能テスト)
4. [実APIを使用したテスト](#実apiを使用したテスト)
5. [Dockerでの動作確認](#dockerでの動作確認)
6. [トラブルシューティング](#トラブルシューティング)

## 🚀 開発環境セットアップ

### 1. 依存関係のインストール

```bash
# 開発用依存関係をインストール
uv sync --dev

# 本番用依存関係のみの場合
uv sync
```

### 2. 環境変数の設定

開発環境では2つの選択肢があります：

**Option A: モックモード（推奨）**
```bash
# 開発用設定をコピー（APIキー不要）
cp .env.development .env
```

**Option B: 実API使用**
```bash
# サンプル設定をコピーして編集
cp .env.example .env
# 実際のAPIキーとトークンを設定
```

## 🧪 モックモードでのテスト

### モックモードとは
- 実際のDiscord API、Gemini API、Garmin APIを使用せずにテスト
- `.env.development`で`ENABLE_MOCK_MODE=true`に設定済み
- APIキーがなくてもアプリケーションの動作を確認可能

### 起動方法

```bash
# モックモードで起動
ENVIRONMENT=development uv run python -m src.main

# または直接.env.developmentを使用
uv run python -m src.main
```

### モックモードの特徴

- **Obsidian Vault**: `./test_vault`に自動作成
- **Discord**: モックレスポンスを返す
- **AI処理**: 固定レスポンスまたはランダム生成
- **音声処理**: サンプル音声ファイルを使用
- **Garmin**: 固定の健康データを返す

## 🔧 個別機能テスト

### 基本テスト実行

```bash
# 全テスト実行
uv run pytest

# 詳細出力
uv run pytest -v

# カバレッジ付き
uv run pytest --cov=src
```

### 特定モジュールのテスト

```bash
# Obsidian統合テスト
uv run pytest tests/unit/test_obsidian.py -v

# AI処理テスト
uv run pytest tests/unit/test_ai_processing.py -v

# メッセージ処理テスト
uv run pytest tests/unit/test_message_processor.py -v

# 統合テスト
uv run pytest tests/integration/ -v
```

### スタンドアロン機能テスト

```bash
# AI機能のテスト
uv run python test_advanced_ai.py

# Garmin統合テスト
uv run python test_garmin_integration.py

# 健康データ分析テスト
uv run python test_health_analysis.py

# 健康モデルのみテスト
uv run python test_health_models_only.py

# URL処理のみテスト
uv run python test_url_processor_only.py
```

## 🎯 実APIを使用したテスト

実際のAPIを使用してテストする場合は `ENVIRONMENT=testing` を設定します。
(`staging`、`integration` も同等に機能します)

### 必要な設定

1. **Discord Bot Token**
   - Discord Developer Portalでボットを作成
   - トークンを取得して`DISCORD_BOT_TOKEN`に設定

2. **Gemini API Key**
   - Google AI Studioでキーを取得
   - `GEMINI_API_KEY`に設定

3. **チャンネルID**
   - テスト用DiscordサーバーのチャンネルIDを取得
   - 各機能に対応するチャンネルIDを設定

### 実行方法

```bash
# .envファイルを編集
vim .env

# テスト環境で実APIを使用して起動
ENVIRONMENT=testing ENABLE_MOCK_MODE=false uv run python -m src.main

# またはデバッグモードで起動
uv run python -m src.main --debug
```

### 設定例

```env
# 必須設定
DISCORD_BOT_TOKEN=your_actual_discord_bot_token
DISCORD_GUILD_ID=your_discord_server_id
GEMINI_API_KEY=your_actual_gemini_api_key
OBSIDIAN_VAULT_PATH=/path/to/your/obsidian/vault

# チャンネルID（実際のチャンネルIDに変更）
CHANNEL_INBOX=123456789012345678
CHANNEL_VOICE=123456789012345679
# ... 他のチャンネル

# 環境設定とモックモード
ENVIRONMENT=testing
ENABLE_MOCK_MODE=false
```

## 🐳 Dockerでの動作確認

### ビルドと実行

```bash
# Dockerイメージをビルド
docker build -t discord-obsidian-memo-bot .

# 開発環境で実行
docker run --env-file .env.development discord-obsidian-memo-bot

# 本番設定で実行
docker run --env-file .env discord-obsidian-memo-bot

# ボリュームマウント付きで実行（開発用）
docker run -v $(pwd):/app --env-file .env.development discord-obsidian-memo-bot
```

## 🔍 コード品質チェック

### フォーマット・リント

```bash
# Ruffでフォーマットとリント
uv run ruff check src/ --fix && uv run ruff format src/

# 型チェック
uv run mypy src/

# 全品質チェック
uv run ruff check src/ --fix && uv run ruff format src/ && uv run mypy src/
```

### Pre-commit フック（オプション）

```bash
# セットアップ
uv run pre-commit install

# 手動実行
uv run pre-commit run --all-files
```

## 🛠 トラブルシューティング

### よくある問題と解決方法

#### 1. 依存関係エラー
```bash
# キャッシュクリア
uv cache clean

# 依存関係再インストール
rm uv.lock
uv sync --dev
```

#### 2. 権限エラー（Obsidian Vault）
```bash
# テスト用vaultディレクトリの権限確認
ls -la ./test_vault

# 権限修正
chmod 755 ./test_vault
```

#### 3. ポートエラー
```bash
# 使用中のポート確認
lsof -i :8080

# プロセス終了
pkill -f "python -m src.main"
```

#### 4. 環境変数が読み込まれない
```bash
# 環境変数を明示的に指定
export $(cat .env.development | xargs) && uv run python -m src.main

# または
python-dotenv run -- uv run python -m src.main
```

### デバッグモード

```bash
# 詳細ログ出力
LOG_LEVEL=DEBUG uv run python -m src.main

# 特定のモジュールのデバッグ
PYTHONPATH=src python -c "from src.config.settings import get_settings; print(get_settings())"
```

## 📊 テストカバレッジの確認

```bash
# HTMLレポート生成
uv run pytest --cov=src --cov-report=html

# レポート確認
open htmlcov/index.html
```

## 🚀 デプロイ前チェックリスト

- [ ] 全テストが通過 (`uv run pytest`)
- [ ] コード品質チェック通過 (`ruff check` + `mypy`)
- [ ] モックモードでの動作確認完了
- [ ] 実APIでの動作確認完了（可能であれば）
- [ ] Dockerビルドが成功
- [ ] 環境変数設定の確認
- [ ] ログレベルの調整（本番では`INFO`）

## 📚 関連ドキュメント

- [CLAUDE.md](../CLAUDE.md) - プロジェクト概要と開発ガイド
- [README.md](../README.md) - プロジェクト説明
- [pyproject.toml](../pyproject.toml) - 依存関係とプロジェクト設定
