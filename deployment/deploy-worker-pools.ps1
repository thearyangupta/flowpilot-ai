param(
    [string]$Project = "flowpilot-ai-504508",
    [string]$Region = "asia-south1",
    [Parameter(Mandatory = $true)]
    [string]$Image
)

$ErrorActionPreference = "Stop"

$ServiceAccount = "flowpilot-runtime@$Project.iam.gserviceaccount.com"

$GoogleClientId = (
    "932960433777-guu3vr60tcajhakrf86rglhaan9agagv." +
    "apps.googleusercontent.com"
)

$GoogleRedirectUri = (
    "https://flowpilot-api-932960433777.asia-south1.run.app" +
    "/api/v1/auth/google/callback"
)

$EnvironmentVariables = @(
    "ENVIRONMENT=production"
    "GEMINI_MODEL=gemini-3.5-flash"
    "GOOGLE_CLIENT_ID=$GoogleClientId"
    "GOOGLE_REDIRECT_URI=$GoogleRedirectUri"
    "GEMINI_BACKEND=vertex"
    "GOOGLE_CLOUD_PROJECT=$Project"
    "GOOGLE_CLOUD_LOCATION=global"
) -join ","

$SecretBindings = @(
    "DATABASE_URL=flowpilot-database-url:latest"
    "REDIS_BROKER_URL=flowpilot-redis-broker-url:latest"
    "REDIS_RESULT_URL=flowpilot-redis-result-url:latest"
    "GEMINI_API_KEY=flowpilot-gemini-api-key:latest"
    "GOOGLE_CLIENT_SECRET=flowpilot-google-client-secret:latest"
    "JWT_SECRET=flowpilot-jwt-secret:latest"
    "TOKEN_ENCRYPTION_KEYS=flowpilot-token-encryption-keys:latest"
    "R2_ACCESS_KEY_ID=flowpilot-r2-access-key-id:latest"
    "R2_SECRET_ACCESS_KEY=flowpilot-r2-secret-access-key:latest"
) -join ","

Write-Host "===== DEPLOY FLOWPILOT WORKER ====="

gcloud beta run worker-pools deploy flowpilot-worker `
  --project=$Project `
  --region=$Region `
  --image=$Image `
  --service-account=$ServiceAccount `
  --instances=1 `
  --network=default `
  --subnet=default `
  --vpc-egress=private-ranges-only `
  --set-env-vars=$EnvironmentVariables `
  --set-secrets=$SecretBindings `
  --command=python `
  '--args=^|^-m|celery|-A|app.worker.celery_app:celery_app|worker|--loglevel=INFO|--concurrency=1|--queues=workflows,maintenance'

Write-Host "`n===== DEPLOY FLOWPILOT BEAT ====="

gcloud beta run worker-pools deploy flowpilot-beat `
  --project=$Project `
  --region=$Region `
  --image=$Image `
  --service-account=$ServiceAccount `
  --instances=1 `
  --network=default `
  --subnet=default `
  --vpc-egress=private-ranges-only `
  --set-env-vars=$EnvironmentVariables `
  --set-secrets=$SecretBindings `
  --command=python `
  '--args=^|^-m|celery|-A|app.worker.celery_app:celery_app|beat|--loglevel=INFO|--schedule=/tmp/celerybeat-schedule'

Write-Host "`nPASS: Worker and beat deployment commands completed."
