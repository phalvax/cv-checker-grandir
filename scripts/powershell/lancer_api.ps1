param(
    [string]$Host = "127.0.0.1",
    [int]$Port = 8000
)

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
Push-Location $projectRoot
try {
    python -m uvicorn cv_checker.main:app --app-dir src --host $Host --port $Port
} finally {
    Pop-Location
}
