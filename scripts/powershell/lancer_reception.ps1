param(
    [string]$IncomingDir = "data/cv/incoming",
    [string]$RunName = ""
)

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
Push-Location $projectRoot
try {
    $args = @(
        "scripts/python/traiter_cv_reception.py",
        "--incoming-dir", $IncomingDir
    )
    if ($RunName -ne "") {
        $args += @("--run-name", $RunName)
    }
    python @args
} finally {
    Pop-Location
}
