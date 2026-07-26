# Run pending SQL migrations against Docker Postgres
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

Write-Host "Starting Docker Postgres..."
docker compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker is not running. Start Docker Desktop, then re-run this script."
}
Start-Sleep -Seconds 6

$files = @(
    "infra/seed/03_migrate.sql",
    "infra/seed/05_run_metadata.sql",
    "infra/seed/06_connections.sql",
    "infra/seed/07_e5_tenancy.sql",
    "infra/seed/08_e6_delivery.sql"
)

foreach ($f in $files) {
    Write-Host "Applying $f ..."
    Get-Content $f -Raw | docker compose exec -T db psql -U insight -d insightbridge -v ON_ERROR_STOP=1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Migration failed: $f"
    }
}

Write-Host "Done. Active connections:"
docker compose exec -T db psql -U insight -d insightbridge -c "SELECT id, name, dialect, is_active FROM app.connections;"
