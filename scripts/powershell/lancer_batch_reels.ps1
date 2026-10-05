param(
    [string]$ApiUrl = "http://127.0.0.1:8000/analyze"
)

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
Push-Location $projectRoot
try {
    python src/cv_checker/batch_run.py --api-url $ApiUrl --cv-dir data/cv/real
} finally {
    Pop-Location
}
