# Deploy the WhatsApp webhook to Google Cloud Run

This runs the Flask app (`server.py`) on a **stable HTTPS URL** so Twilio can POST to `/webhook` without ngrok.

## What you need

- A [Google Cloud](https://cloud.google.com/) project with **billing enabled**
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) installed and logged in: `gcloud auth login`
- Your Twilio WhatsApp Sandbox (or production sender) ready to set a webhook URL

**Note:** Inbound webhooks do **not** require Twilio API credentials inside the container. Twilio credentials in `.env` are only needed for optional scripts (e.g. sending test messages locally).

## 1. Enable APIs and pick region

```bash
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"   # or europe-west1, asia-east1, etc.

gcloud config set project "$PROJECT_ID"
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
```

### 1b. Default Compute Engine service account (new projects)

Cloud Run “deploy from source” uses your project’s **default compute service account** (`PROJECT_NUMBER-compute@developer.gserviceaccount.com`) to read the uploaded zip from Cloud Storage and **push** the image to Artifact Registry. On a brand-new project, that account may lack those roles, which causes:

- `storage.objects.get` **denied** during build, or
- Build step **docker build** succeeds but the overall build **FAILURE** when pushing the image.

Replace `PROJECT_ID` and `PROJECT_NUMBER` (from Cloud Console → Project settings, or `gcloud projects describe PROJECT_ID --format='value(projectNumber)'`):

```bash
export PROJECT_ID="your-gcp-project-id"
export PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"
```

Optional (quieter Cloud Build logs): `roles/logging.logWriter` on the same member.

## 2. Build and deploy (one command)

From the **repository root** (where `Dockerfile` lives):

```bash
gcloud run deploy jeans-recommender-whatsapp \
  --source . \
  --region "$REGION" \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 1 \
  --timeout 120 \
  --set-env-vars "PYTHONUNBUFFERED=1"
```

- **`--max-instances 1`**: Conversation state is **in-memory**. More than one instance can confuse a single user if requests hit different containers.
- **`--min-instances 1`** (optional): Avoids cold starts for demos; costs more. For interviews you can use `1` during the week and `0` when idle.

After deploy, note the **Service URL**, e.g. `https://jeans-recommender-whatsapp-xxxxx-uc.a.run.app`.

## 3. Point Twilio at Cloud Run

1. Twilio Console → **Messaging** → **Try it out** / **WhatsApp sandbox** (or your WhatsApp sender config).
2. **When a message comes in** → Webhook URL:
   ```text
   https://YOUR-SERVICE-URL.run.app/webhook
   ```
3. Method: **HTTP POST**.

Open `https://YOUR-SERVICE-URL.run.app/` in a browser to confirm the page shows the same `/webhook` URL. Use `https://YOUR-SERVICE-URL.run.app/health` for monitoring.

## 4. Sandbox vs “anyone on the internet”

Twilio’s **sandbox** still requires each user to **join** once (send the join code). For your README / QR code, link to instructions or a `wa.me` link with the join message pre-filled (see current Twilio sandbox docs for the exact phrase).

## 5. Optional: build with Docker locally

```bash
docker build -t jeans-webhook .
docker run --rm -p 8080:8080 -e PORT=8080 jeans-webhook
# Visit http://localhost:8080/health
```

## Troubleshooting

| Issue | What to check |
|--------|----------------|
| Twilio 11200 / connection failed | Webhook URL must be `https`, path `/webhook`, POST. |
| Empty or wrong replies | Logs: `gcloud run services logs read jeans-recommender-whatsapp --region "$REGION"` |
| Session “forgets” mid-flow | Keep `--max-instances 1`; avoid scaling to multiple instances. |
| Cold start slow | Set `--min-instances 1` for demos. |
| `storage.objects.get` denied (403) during deploy | Apply **§1b** `storage.objectViewer` on the default compute service account. |
| Build fails after “Building Container” / push phase | Apply **§1b** `artifactregistry.writer` on the default compute service account. Check: `gcloud builds describe BUILD_ID --region=REGION` (docker step may still show SUCCESS). |
