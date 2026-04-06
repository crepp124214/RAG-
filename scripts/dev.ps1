param(
    [Parameter(Position = 0)]
    [string]$Command = "dev",
    [Parameter(Position = 1)]
    [string]$Target = ""
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$DevRoot = Join-Path $ProjectRoot ".dev"
$PidRoot = Join-Path $DevRoot "pids"
$LogRoot = Join-Path $DevRoot "logs"

$Services = @{
    backend = @{
        Name = "backend"
        FilePath = "python"
        Arguments = @("-m", "uvicorn", "backend.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000")
        WorkingDirectory = $ProjectRoot
        Url = "http://127.0.0.1:8000"
    }
    frontend = @{
        Name = "frontend"
        FilePath = "cmd.exe"
        Arguments = @("/c", "npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173")
        WorkingDirectory = Join-Path $ProjectRoot "frontend"
        Url = "http://127.0.0.1:5173"
    }
    worker = @{
        Name = "worker"
        FilePath = "python"
        Arguments = @("-m", "worker.main")
        WorkingDirectory = $ProjectRoot
        Url = ""
    }
}

function Ensure-DevDirectories {
    foreach ($path in @($DevRoot, $PidRoot, $LogRoot)) {
        if (-not (Test-Path $path)) {
            New-Item -ItemType Directory -Path $path | Out-Null
        }
    }
}

function Get-PidFilePath([string]$Name) {
    return Join-Path $PidRoot "$Name.pid"
}

function Get-LogFilePath([string]$Name) {
    return Join-Path $LogRoot "$Name.log"
}

function Get-ErrorLogFilePath([string]$Name) {
    return Join-Path $LogRoot "$Name.err.log"
}

function Get-ServiceProcess([string]$Name) {
    $pidFile = Get-PidFilePath $Name
    if (-not (Test-Path $pidFile)) {
        return $null
    }

    $rawPid = (Get-Content $pidFile -Raw).Trim()
    if (-not $rawPid) {
        Remove-Item $pidFile -Force
        return $null
    }

    $process = Get-Process -Id ([int]$rawPid) -ErrorAction SilentlyContinue
    if ($null -eq $process) {
        if (Test-Path $pidFile) {
            Remove-Item $pidFile -Force
        }
    }
    return $process
}

function Start-ServiceProcess([hashtable]$Service) {
    Ensure-DevDirectories

    $existing = Get-ServiceProcess $Service.Name
    if ($null -ne $existing) {
        Write-Host "$($Service.Name) already running (PID $($existing.Id))."
        return
    }

    $stdout = Get-LogFilePath $Service.Name
    $stderr = Get-ErrorLogFilePath $Service.Name

    $process = Start-Process `
        -FilePath $Service.FilePath `
        -ArgumentList $Service.Arguments `
        -WorkingDirectory $Service.WorkingDirectory `
        -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr `
        -PassThru

    Set-Content -Path (Get-PidFilePath $Service.Name) -Value $process.Id
    Write-Host "Started $($Service.Name) (PID $($process.Id))."
    if ($Service.Url) {
        Write-Host "  URL: $($Service.Url)"
    }
    Write-Host "  Logs: $(Get-LogFilePath $Service.Name)"
}

function Stop-ServiceProcess([string]$Name) {
    $process = Get-ServiceProcess $Name
    if ($null -eq $process) {
        Write-Host "$Name is not running."
        return
    }

    Stop-Process -Id $process.Id -Force
    $pidFile = Get-PidFilePath $Name
    if (Test-Path $pidFile) {
        Remove-Item $pidFile -Force
    }
    Write-Host "Stopped $Name (PID $($process.Id))."
}

function Show-Status {
    Ensure-DevDirectories
    foreach ($entry in $Services.GetEnumerator() | Sort-Object Name) {
        $name = $entry.Key
        $service = $entry.Value
        $process = Get-ServiceProcess $name
        if ($null -eq $process) {
            Write-Host ("{0,-10} stopped" -f $name)
        } else {
            $line = ("{0,-10} running  PID={1}" -f $name, $process.Id)
            if ($service.Url) {
                $line = "$line  URL=$($service.Url)"
            }
            Write-Host $line
        }
    }
}

function Invoke-Step([string]$Label, [scriptblock]$Action) {
    Write-Host "==> $Label"
    & $Action
}

function Invoke-Health {
    $checks = @(
        @{ Name = "python"; Command = { python --version } },
        @{ Name = "node"; Command = { node --version } },
        @{ Name = "npm"; Command = { npm --version } }
    )

    foreach ($check in $checks) {
        try {
            $output = & $check.Command 2>&1
            Write-Host ("{0,-10} OK  {1}" -f $check.Name, ($output | Select-Object -First 1))
        } catch {
            Write-Host ("{0,-10} FAIL {1}" -f $check.Name, $_.Exception.Message)
        }
    }

    foreach ($path in @(".env.example", "backend/.env.example", "frontend/package.json", "frontend/tsconfig.json")) {
        $fullPath = Join-Path $ProjectRoot $path
        if (Test-Path $fullPath) {
            Write-Host ("{0,-10} OK  {1}" -f "file", $path)
        } else {
            Write-Host ("{0,-10} FAIL {1}" -f "file", $path)
        }
    }

    $envPath = Join-Path $ProjectRoot ".env"
    if (Test-Path $envPath) {
        Write-Host ("{0,-10} OK  .env" -f "config")
    } else {
        Write-Host ("{0,-10} WARN .env missing; copy from .env.example before running full stack." -f "config")
    }
}

function Invoke-Clean {
    $paths = @(
        (Join-Path $ProjectRoot "frontend/dist"),
        (Join-Path $ProjectRoot "frontend/coverage"),
        (Join-Path $ProjectRoot ".coverage"),
        $DevRoot
    )

    foreach ($path in $paths) {
        if (Test-Path $path) {
            Remove-Item -LiteralPath $path -Recurse -Force
            Write-Host "Removed $path"
        }
    }
}

function Show-Help {
    @"
RAG developer console

Usage:
  powershell -ExecutionPolicy Bypass -File scripts/dev.ps1 [command] [target]

Commands:
  dev|all          Start backend, frontend, and worker in background
  backend          Start backend only
  frontend         Start frontend only
  worker           Start worker only
  stop [target]    Stop all or one service: backend/frontend/worker
  status           Show running services
  test             Run backend and frontend tests
  lint             Run frontend lint
  check            Run tests, lint, and typecheck
  build            Run frontend production build
  coverage         Run backend coverage
  health           Check local developer prerequisites
  clean            Remove generated dev artifacts
  help             Show this help
"@ | Write-Host
}

switch ($Command.ToLowerInvariant()) {
    "dev" {
        foreach ($service in @("backend", "frontend", "worker")) {
            Start-ServiceProcess $Services[$service]
        }
    }
    "all" {
        foreach ($service in @("backend", "frontend", "worker")) {
            Start-ServiceProcess $Services[$service]
        }
    }
    "backend" {
        Start-ServiceProcess $Services.backend
    }
    "frontend" {
        Start-ServiceProcess $Services.frontend
    }
    "worker" {
        Start-ServiceProcess $Services.worker
    }
    "stop" {
        $resolvedTarget = if ($Target) { $Target.ToLowerInvariant() } else { "all" }
        if ($resolvedTarget -eq "all") {
            foreach ($service in @("backend", "frontend", "worker")) {
                Stop-ServiceProcess $service
            }
        } elseif ($Services.ContainsKey($resolvedTarget)) {
            Stop-ServiceProcess $resolvedTarget
        } else {
            throw "Unknown stop target: $Target"
        }
    }
    "status" {
        Show-Status
    }
    "test" {
        Invoke-Step "backend tests" { cmd /c scripts\test_backend.bat }
        Invoke-Step "frontend tests" { cmd /c scripts\test_frontend.bat }
    }
    "lint" {
        Invoke-Step "frontend lint" {
            Push-Location (Join-Path $ProjectRoot "frontend")
            try {
                cmd /c npm run lint
            } finally {
                Pop-Location
            }
        }
    }
    "check" {
        Invoke-Step "backend tests" { cmd /c scripts\test_backend.bat }
        Invoke-Step "frontend tests" { cmd /c scripts\test_frontend.bat }
        Invoke-Step "frontend lint" {
            Push-Location (Join-Path $ProjectRoot "frontend")
            try {
                cmd /c npm run lint
            } finally {
                Pop-Location
            }
        }
        Invoke-Step "frontend typecheck" { cmd /c scripts\check_frontend.bat }
    }
    "build" {
        Invoke-Step "frontend build" { cmd /c scripts\build_frontend.bat }
    }
    "coverage" {
        Invoke-Step "backend coverage" { cmd /c scripts\coverage_backend.bat }
    }
    "health" {
        Invoke-Health
    }
    "clean" {
        Invoke-Clean
    }
    "help" {
        Show-Help
    }
    default {
        throw "Unknown command: $Command"
    }
}
