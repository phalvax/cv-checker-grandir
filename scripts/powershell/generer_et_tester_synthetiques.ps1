param(
    [int]$Count = 100,
    [int]$Seed = 20260218,
    [string]$RunName = ""
)

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
Push-Location $projectRoot
try {
    $generatorScript = Join-Path $projectRoot "src/synthetic_cv_generator/generate_synthetic_cv_dataset.py"
    if (-not (Test-Path $generatorScript)) {
        throw "Script introuvable: $generatorScript"
    }

    python $generatorScript --count $Count --seed $Seed --sync-latest

    if ($RunName -eq "") {
        $RunName = "synthetic_" + (Get-Date -Format "yyyyMMdd_HHmmss")
    }

    $incomingRunDir = Join-Path $projectRoot ("data/cv/incoming/" + $RunName)
    New-Item -ItemType Directory -Force -Path $incomingRunDir | Out-Null

    $generatedPdfDir = Join-Path $projectRoot "data/cv/generated/latest/pdfs"
    if (-not (Test-Path $generatedPdfDir)) {
        throw "Dossier introuvable: $generatedPdfDir"
    }
    Get-ChildItem -Path $generatedPdfDir -Filter *.pdf -File | Copy-Item -Destination $incomingRunDir -Force

    python scripts/python/traiter_cv_reception.py --incoming-dir $incomingRunDir --run-name $RunName
} finally {
    Pop-Location
}
