#!/bin/bash
"""
Discord-Obsidian Memo Bot デプロイメントスクリプト
Google Cloud Runへの自動デプロイを実行
"""

set -e  # エラー時に停止

# カラーコードの定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ログ関数
log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# 設定変数
SERVICE_NAME="discord-obsidian-memo-bot"
REGION="asia-northeast1"
PLATFORM="managed"

# プロジェクトIDの確認
if [ -z "$PROJECT_ID" ]; then
    error "PROJECT_ID環境変数が設定されていません"
    echo "使用方法: PROJECT_ID=your-project-id $0"
    exit 1
fi

log "Google Cloud プロジェクト: $PROJECT_ID"
log "サービス名: $SERVICE_NAME"
log "リージョン: $REGION"

# Google Cloud CLIの確認
if ! command -v gcloud &> /dev/null; then
    error "gcloud CLIがインストールされていません"
    exit 1
fi

# プロジェクトの設定
log "Google Cloud プロジェクトを設定中..."
gcloud config set project $PROJECT_ID

# 必要なAPIの有効化
log "必要なAPIを有効化中..."
gcloud services enable run.googleapis.com --quiet
gcloud services enable cloudbuild.googleapis.com --quiet
gcloud services enable secretmanager.googleapis.com --quiet
gcloud services enable containerregistry.googleapis.com --quiet

# Dockerイメージのビルドとプッシュ
log "Dockerイメージをビルド中..."
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME:$(date +%Y%m%d-%H%M%S)"
docker build -t $IMAGE_NAME .

log "Dockerイメージをプッシュ中..."
docker push $IMAGE_NAME

# Cloud Runサービスの存在確認
if gcloud run services describe $SERVICE_NAME --region=$REGION --quiet >/dev/null 2>&1; then
    log "既存のサービスを更新します"
    OPERATION="update"
else
    log "新しいサービスを作成します"
    OPERATION="deploy"
fi

# Cloud Runにデプロイ
log "Cloud Runにデプロイ中..."
if [ "$OPERATION" = "deploy" ]; then
    gcloud run deploy $SERVICE_NAME \
        --image $IMAGE_NAME \
        --region $REGION \
        --platform $PLATFORM \
        --allow-unauthenticated \
        --memory 1Gi \
        --cpu 1 \
        --min-instances 0 \
        --max-instances 10 \
        --timeout 300s \
        --concurrency 5 \
        --set-env-vars="ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,USE_SECRET_MANAGER=true,OBSIDIAN_VAULT_PATH=/app/vault,PORT=8080"
else
    gcloud run services replace service.yaml --region $REGION
fi

# サービスURLの取得
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')

# デプロイメント結果の確認
log "デプロイメント結果を確認中..."
sleep 10

# ヘルスチェック
log "ヘルスチェックを実行中..."
if curl -f "$SERVICE_URL/health" >/dev/null 2>&1; then
    success "ヘルスチェック成功"
else
    warn "ヘルスチェックに失敗しました。ログを確認してください。"
fi

# 結果の表示
success "デプロイメントが完了しました!"
echo
echo "サービス情報:"
echo "  URL: $SERVICE_URL"
echo "  ヘルスチェック: $SERVICE_URL/health"
echo "  メトリクス: $SERVICE_URL/metrics"
echo
echo "ログの確認:"
echo "  gcloud logs read \"resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME\" --limit=50"
echo
echo "サービス管理:"
echo "  停止: gcloud run services delete $SERVICE_NAME --region=$REGION"
echo "  更新: $0"

# 最新のログを表示
log "最新のログ（10件）:"
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" --limit=10 --format="value(timestamp,severity,textPayload)"