# Discord-Obsidian Memo Bot デプロイメントガイド

## 概要

このガイドではDiscord-Obsidian Memo BotをGoogle Cloud Runにデプロイする方法を説明します。

## 前提条件

- Google Cloud Projectが作成済み
- Google Cloud CLIがインストール・認証済み
- Docker がインストール済み
- 必要なAPIが有効化済み：
  - Cloud Run API
  - Cloud Build API
  - Secret Manager API
  - Container Registry API

## 環境変数一覧

### 必須環境変数

| 環境変数名 | 説明 | 例 |
|-----------|------|-----|
| `ENVIRONMENT` | 実行環境 | `production` |
| `DISCORD_BOT_TOKEN` | Discord botトークン | `MTAx...` |
| `DISCORD_GUILD_ID` | Discord サーバーID | `123456789` |
| `GEMINI_API_KEY` | Google Gemini APIキー | `AIza...` |
| `OBSIDIAN_VAULT_PATH` | Obsidian Vaultパス | `/app/vault` |

### Discord チャンネルID設定

| 環境変数名 | 説明 |
|-----------|------|
| `CHANNEL_INBOX` | 📝 INBOXチャンネルID |
| `CHANNEL_VOICE` | 🎤 VOICEチャンネルID |
| `CHANNEL_FILES` | 📎 FILESチャンネルID |
| `CHANNEL_MONEY` | 💰 MONEYチャンネルID |
| `CHANNEL_FINANCE_REPORTS` | 📊 FINANCE REPORTSチャンネルID |
| `CHANNEL_TASKS` | 📋 TASKSチャンネルID |
| `CHANNEL_PRODUCTIVITY_REVIEWS` | 🔄 PRODUCTIVITY REVIEWSチャンネルID |
| `CHANNEL_NOTIFICATIONS` | 🔔 NOTIFICATIONSチャンネルID |
| `CHANNEL_COMMANDS` | ⚙️ COMMANDSチャンネルID |

### オプション環境変数

| 環境変数名 | 説明 | デフォルト |
|-----------|------|-----------|
| `GOOGLE_CLOUD_PROJECT` | Google Cloud プロジェクトID | None |
| `USE_SECRET_MANAGER` | Secret Manager使用フラグ | `false` |
| `ENABLE_ACCESS_LOGGING` | アクセスログ有効化 | `true` |
| `LOG_LEVEL` | ログレベル | `INFO` |
| `GEMINI_API_DAILY_LIMIT` | Gemini API 日次制限 | `1500` |
| `SPEECH_API_MONTHLY_LIMIT_MINUTES` | Speech API 月次制限（分） | `60` |

## デプロイメント手順

### 1. プロジェクト設定

```bash
# Google Cloud プロジェクトを設定
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# 必要なAPIを有効化
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### 2. Secret Manager の設定

```bash
# Discord Bot Token
gcloud secrets create discord-bot-token --data-file=- <<< "YOUR_DISCORD_BOT_TOKEN"

# Gemini API Key
gcloud secrets create gemini-api-key --data-file=- <<< "YOUR_GEMINI_API_KEY"

# Speech API Key（オプション）
gcloud secrets create speech-api-key --data-file=- <<< "YOUR_SPEECH_API_KEY"

# Discord 設定
gcloud secrets create discord-config --data-file=- <<< "YOUR_GUILD_ID"
```

### 3. Cloud Build を使用したデプロイメント

```bash
# Cloud Build trigger の作成
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_DISCORD_BOT_TOKEN="projects/$PROJECT_ID/secrets/discord-bot-token/versions/latest",_GEMINI_API_KEY="projects/$PROJECT_ID/secrets/gemini-api-key/versions/latest"
```

### 4. 手動デプロイメント

```bash
# Dockerイメージのビルド
docker build -t gcr.io/$PROJECT_ID/discord-obsidian-memo-bot:latest .

# イメージをプッシュ
docker push gcr.io/$PROJECT_ID/discord-obsidian-memo-bot:latest

# Cloud Runにデプロイ
gcloud run deploy discord-obsidian-memo-bot \
  --image gcr.io/$PROJECT_ID/discord-obsidian-memo-bot:latest \
  --region asia-northeast1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300s \
  --concurrency 5 \
  --set-env-vars="ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,USE_SECRET_MANAGER=true,OBSIDIAN_VAULT_PATH=/app/vault"
```

## 環境変数設定ファイル例

### `.env.production`
```bash
# Core Configuration
ENVIRONMENT=production
GOOGLE_CLOUD_PROJECT=your-project-id
USE_SECRET_MANAGER=true
ENABLE_ACCESS_LOGGING=true

# Application Settings
OBSIDIAN_VAULT_PATH=/app/vault
LOG_LEVEL=INFO
LOG_FORMAT=json

# Discord Configuration (チャンネルIDを設定)
DISCORD_GUILD_ID=YOUR_GUILD_ID_HERE
CHANNEL_INBOX=YOUR_INBOX_CHANNEL_ID
CHANNEL_VOICE=YOUR_VOICE_CHANNEL_ID
CHANNEL_FILES=YOUR_FILES_CHANNEL_ID
CHANNEL_MONEY=YOUR_MONEY_CHANNEL_ID
CHANNEL_FINANCE_REPORTS=YOUR_FINANCE_REPORTS_CHANNEL_ID
CHANNEL_TASKS=YOUR_TASKS_CHANNEL_ID
CHANNEL_PRODUCTIVITY_REVIEWS=YOUR_PRODUCTIVITY_REVIEWS_CHANNEL_ID
CHANNEL_NOTIFICATIONS=YOUR_NOTIFICATIONS_CHANNEL_ID
CHANNEL_COMMANDS=YOUR_COMMANDS_CHANNEL_ID

# API Rate Limits
GEMINI_API_DAILY_LIMIT=1500
GEMINI_API_MINUTE_LIMIT=15
SPEECH_API_MONTHLY_LIMIT_MINUTES=60

# Optional Features
GARMIN_CACHE_HOURS=24.0
```

## IAM権限の設定

```bash
# Cloud Run サービスアカウントにSecret Manager権限を付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:PROJECT-NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Cloud Storageアクセス権限（バックアップ機能用）
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:PROJECT-NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
```

## 監視とログ

### Cloud Logging の設定

```bash
# ログベースのメトリクスを作成
gcloud logging metrics create discord_bot_errors \
  --description="Discord bot error count" \
  --log-filter='resource.type="cloud_run_revision" AND severity>=ERROR'

# アラートポリシーの作成
gcloud alpha monitoring policies create --policy-from-file=monitoring-policy.yaml
```

### ヘルスチェックの確認

```bash
# ボットの健康状態を確認
curl https://your-service-url.run.app/health

# 詳細なメトリクスを確認
curl https://your-service-url.run.app/metrics
```

## トラブルシューティング

### よくある問題

1. **Secret Manager アクセスエラー**
   - IAM権限を確認
   - プロジェクトIDが正しく設定されているか確認

2. **Discord 接続エラー**
   - Bot Tokenの有効性を確認
   - Guild IDが正しいか確認
   - ボットが適切なサーバーに追加されているか確認

3. **メモリ不足エラー**
   - Cloud Runのメモリ設定を1Gi以上に増やす
   - 並行処理数を調整

4. **タイムアウトエラー**
   - Cloud Runのタイムアウト設定を300秒以上に設定
   - AI処理の制限を確認

### ログの確認

```bash
# Cloud Runのログを確認
gcloud logs read "resource.type=cloud_run_revision" --limit=50

# 特定のエラーログを検索
gcloud logs read "resource.type=cloud_run_revision AND severity>=ERROR" --limit=20
```

## セキュリティのベストプラクティス

1. **Secret Manager の使用**
   - 機密情報は全てSecret Managerに保存
   - 定期的な認証情報のローテーション

2. **最小権限の原則**
   - サービスアカウントには必要最小限の権限のみ付与

3. **ネットワークセキュリティ**
   - VPCコネクターの使用を検討
   - 適切なファイアウォール規則の設定

4. **監査ログ**
   - アクセスログの有効化
   - 不審な活動の監視

## 定期メンテナンス

1. **依存関係の更新**
   ```bash
   # 依存関係の確認と更新
   uv sync --upgrade
   ```

2. **セキュリティパッチの適用**
   ```bash
   # ベースイメージの更新
   docker pull python:3.13-slim
   ```

3. **ログの確認**
   - 定期的にエラーログを確認
   - パフォーマンスメトリクスの監視

4. **バックアップの確認**
   - 自動バックアップが正常に動作しているか確認
   - 復旧テストの実施

## スケーリング設定

```bash
# オートスケーリング設定の更新
gcloud run services update discord-obsidian-memo-bot \
  --region asia-northeast1 \
  --min-instances 1 \
  --max-instances 20 \
  --concurrency 10
```

## 費用最適化

1. **リソース設定の最適化**
   - 実際の使用量に基づいてCPU/メモリを調整
   - 最小インスタンス数を0に設定（コールドスタートを許容する場合）

2. **API使用量の監視**
   - Gemini APIとSpeech APIの使用量を定期的にチェック
   - 使用量制限の適切な設定

このガイドに従ってデプロイメントを行うことで、Discord-Obsidian Memo Botを安全かつ効率的にCloud Run上で運用できます。
