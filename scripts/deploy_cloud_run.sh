#!/usr/bin/env bash
# Deploy WhatsApp webhook to Cloud Run. Usage:
#   export PROJECT_ID=your-project-id
#   ./scripts/deploy_cloud_run.sh
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-jeans-recommender-whatsapp}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "Set PROJECT_ID to your GCP project id, e.g. export PROJECT_ID=my-project-123"
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

gcloud config set project "$PROJECT_ID"
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com --quiet

gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --region "$REGION" \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 1 \
  --timeout 120 \
  --set-env-vars "PYTHONUNBUFFERED=1"

echo ""
echo "Set your Twilio WhatsApp webhook POST URL to:"
echo "  https://SERVICE-URL/webhook"
echo "(Exact URL was printed by gcloud run deploy above.)"
