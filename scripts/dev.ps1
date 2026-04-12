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

$BackendCheckUrl = if ($env:RAG_DEV_BACKEND_URL) { $env:RAG_DEV_BACKEND_URL.TrimEnd('/') } else { $Services.backend.Url }
$FrontendCheckUrl = if ($env:RAG_DEV_FRONTEND_URL) { $env:RAG_DEV_FRONTEND_URL.TrimEnd('/') } else { $Services.frontend.Url }

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

function Read-EnvFile([string]$Path) {
    $values = @{}
    if (-not (Test-Path $Path)) {
        return $values
    }

    foreach ($line in Get-Content -Path $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#")) {
            continue
        }

        $parts = $trimmed.Split("=", 2)
        if ($parts.Count -ne 2) {
            continue
        }

        $values[$parts[0].Trim()] = $parts[1].Trim()
    }

    return $values
}

function Write-CheckResult([string]$Name, [string]$Level, [string]$Detail) {
    Write-Host ("{0,-10} {1,-4} {2}" -f $Name, $Level, $Detail)
}

function Test-HttpJsonEndpoint([string]$Name, [string]$Url) {
    try {
        $response = Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 8
        $status = if ($response.data.status) { $response.data.status } else { "ok" }
        Write-CheckResult $Name "OK" "$Url ($status)"
        return $true
    } catch {
        Write-CheckResult $Name "FAIL" "$Url ($($_.Exception.Message))"
        return $false
    }
}

function Invoke-JsonEndpointDetailed([string]$Name, [string]$Url) {
    $request = [System.Net.HttpWebRequest]::Create($Url)
    $request.Method = "GET"
    $request.Timeout = 8000

    $response = $null
    $errorDetail = $null
    try {
        $response = $request.GetResponse()
    } catch [System.Net.WebException] {
        $response = $_.Exception.Response
        $errorDetail = $_.Exception.Message
    } catch {
        return @{
            Name = $Name
            Success = $false
            HttpStatus = 0
            Payload = $null
            ErrorDetail = $_.Exception.Message
        }
    }

    if ($null -eq $response) {
        return @{
            Name = $Name
            Success = $false
            HttpStatus = 0
            Payload = $null
            ErrorDetail = $errorDetail
        }
    }

    $statusCode = 0
    $bodyText = $null
    try {
        $statusCode = [int]$response.StatusCode
    } catch {
        $statusCode = 0
    }

    try {
        $reader = New-Object System.IO.StreamReader($response.GetResponseStream())
        $bodyText = $reader.ReadToEnd()
        $reader.Close()
    } catch {
        $bodyText = $null
    } finally {
        $response.Close()
    }

    $payload = $null
    if ($bodyText) {
        try {
            $payload = $bodyText | ConvertFrom-Json
        } catch {
            $payload = $null
        }
    }

    return @{
        Name = $Name
        Success = ($statusCode -ge 200 -and $statusCode -lt 400)
        HttpStatus = $statusCode
        Payload = $payload
        ErrorDetail = $errorDetail
    }
}

function Test-HttpTextEndpoint([string]$Name, [string]$Url) {
    try {
        $response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec 8
        Write-CheckResult $Name "OK" "$Url (HTTP $($response.StatusCode))"
        return $true
    } catch {
        Write-CheckResult $Name "FAIL" "$Url ($($_.Exception.Message))"
        return $false
    }
}

function Get-ReadyPayloadData([hashtable]$Result) {
    if ($null -eq $Result.Payload) {
        return $null
    }
    if ($null -eq $Result.Payload.data) {
        return $null
    }
    return $Result.Payload.data
}

function Write-ReadinessComponents($Components) {
    if ($null -eq $Components) {
        Write-CheckResult "ready" "FAIL" "missing readiness component details"
        return $false
    }

    $allRequiredHealthy = $true
    foreach ($component in $Components) {
        $detail = if ($component.detail) { $component.detail } else { "" }
        $requiredText = if ($component.required) { "required" } else { "optional" }
        $message = "$($component.label) [$requiredText]"
        if ($detail) {
            $message = "$message - $detail"
        }

        switch ($component.status) {
            "ready" {
                Write-CheckResult $component.name "OK" $message
            }
            "skipped" {
                Write-CheckResult $component.name "WARN" $message
            }
            "failed" {
                if ($component.required) {
                    Write-CheckResult $component.name "FAIL" $message
                    $allRequiredHealthy = $false
                } else {
                    Write-CheckResult $component.name "WARN" $message
                }
            }
            default {
                Write-CheckResult $component.name "WARN" "$message - unexpected status: $($component.status)"
                if ($component.required) {
                    $allRequiredHealthy = $false
                }
            }
        }
    }

    return $allRequiredHealthy
}

function Test-ManagedServiceState([string]$Name, [bool]$Required) {
    $process = Get-ServiceProcess $Name
    if ($null -eq $process) {
        $level = if ($Required) { "FAIL" } else { "WARN" }
        $detail = if ($Required) {
            "not running under scripts/dev.ps1"
        } else {
            "not managed by scripts/dev.ps1"
        }
        Write-CheckResult "$Name-proc" $level $detail
        return $false
    }

    Write-CheckResult "$Name-proc" "OK" "PID $($process.Id)"
    return $true
}

function Test-ReadyEndpoint([string]$BaseUrl) {
    $url = "$BaseUrl/api/ready"
    $result = Invoke-JsonEndpointDetailed "ready" $url
    if ($null -eq $result.Payload) {
        Write-CheckResult "ready" "FAIL" "$url ($($result.ErrorDetail))"
        return @{
            Passed = $false
            RequiredHealthy = $false
        }
    }

    $data = Get-ReadyPayloadData $result
    if ($null -eq $data) {
        Write-CheckResult "ready" "FAIL" "$url (missing payload data)"
        return @{
            Passed = $false
            RequiredHealthy = $false
        }
    }

    $summaryLevel = if ($data.ready) {
        if ($data.degraded) { "WARN" } else { "OK" }
    } else {
        "FAIL"
    }
    Write-CheckResult "ready" $summaryLevel "$url ($($data.status))"
    $requiredHealthy = Write-ReadinessComponents $data.components

    return @{
        Passed = [bool]$data.ready
        RequiredHealthy = $requiredHealthy
    }
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
            Write-CheckResult $check.Name "OK" ($output | Select-Object -First 1)
        } catch {
            Write-CheckResult $check.Name "FAIL" $_.Exception.Message
        }
    }

    foreach ($path in @(".env.example", "backend/.env.example", "frontend/package.json", "frontend/tsconfig.json")) {
        $fullPath = Join-Path $ProjectRoot $path
        if (Test-Path $fullPath) {
            Write-CheckResult "file" "OK" $path
        } else {
            Write-CheckResult "file" "FAIL" $path
        }
    }

    $envPath = Join-Path $ProjectRoot ".env"
    if (-not (Test-Path $envPath)) {
        Write-CheckResult "config" "WARN" ".env missing; copy from .env.example before running full stack."
        return
    }

    Write-CheckResult "config" "OK" ".env"
    $envValues = Read-EnvFile $envPath

    foreach ($requiredKey in @("APP_ENV", "DATABASE_URL", "REDIS_URL", "FILE_STORAGE_PATH")) {
        if ($envValues.ContainsKey($requiredKey) -and $envValues[$requiredKey]) {
            Write-CheckResult "env" "OK" $requiredKey
        } else {
            Write-CheckResult "env" "FAIL" "missing $requiredKey"
        }
    }

    $appEnv = if ($envValues.ContainsKey("APP_ENV")) { $envValues["APP_ENV"].ToLowerInvariant() } else { "" }
    $llmMode = if ($envValues.ContainsKey("LLM_MODE")) { $envValues["LLM_MODE"].ToLowerInvariant() } else { "" }
    if ($appEnv -eq "production" -and $llmMode -eq "acceptance") {
        Write-CheckResult "llm_mode" "FAIL" "production 环境不得使用 acceptance 模式"
    } elseif ($llmMode) {
        Write-CheckResult "llm_mode" "OK" $llmMode
    } else {
        Write-CheckResult "llm_mode" "WARN" "LLM_MODE missing; backend defaults to production"
    }

    if ($envValues.ContainsKey("NEO4J_URI") -and $envValues["NEO4J_URI"]) {
        Write-CheckResult "neo4j" "OK" "configured: $($envValues["NEO4J_URI"])"
    } else {
        Write-CheckResult "neo4j" "WARN" "NEO4J_URI missing; GraphRAG will use degraded path"
    }
}

function Invoke-Smoke {
    $backendOk = Test-HttpJsonEndpoint "backend" "$BackendCheckUrl/api/health"
    $readyResult = Test-ReadyEndpoint $BackendCheckUrl
    $frontendOk = Test-HttpTextEndpoint "frontend" $FrontendCheckUrl

    if (-not ($backendOk -and $readyResult.Passed -and $frontendOk)) {
        throw "Smoke check failed. Ensure backend/frontend are running and inspect readiness details."
    }
}

function Invoke-Acceptance {
    $backendProcessOk = Test-ManagedServiceState "backend" $false
    $frontendProcessOk = Test-ManagedServiceState "frontend" $false
    $workerProcessOk = Test-ManagedServiceState "worker" $true

    $backendOk = Test-HttpJsonEndpoint "backend" "$BackendCheckUrl/api/health"
    $readyResult = Test-ReadyEndpoint $BackendCheckUrl
    $frontendOk = Test-HttpTextEndpoint "frontend" $FrontendCheckUrl

    if ($backendOk -and -not $backendProcessOk) {
        Write-CheckResult "backend" "WARN" "health endpoint reachable but backend is not managed by scripts/dev.ps1"
    }
    if ($frontendOk -and -not $frontendProcessOk) {
        Write-CheckResult "frontend" "WARN" "frontend endpoint reachable but frontend is not managed by scripts/dev.ps1"
    }

    $acceptancePassed = $backendOk -and $readyResult.Passed -and $readyResult.RequiredHealthy -and $frontendOk -and $workerProcessOk
    if (-not $acceptancePassed) {
        [Console]::Error.WriteLine("acceptance FAIL: inspect readiness components, service state, and endpoint availability above.")
        throw "Acceptance check failed."
    }

    Write-Host "acceptance OK: backend, frontend, worker, and required readiness components passed."
}

function Invoke-SmokeFlow {
    Invoke-Smoke
    Write-CheckResult "smoke-flow" "OK" "starting end-to-end upload/query verification"
    & python (Join-Path $ProjectRoot "scripts\smoke_flow.py") --backend-url $BackendCheckUrl
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
  health           Check local developer prerequisites and .env safety
  smoke            Check running backend/frontend health and readiness endpoints
  acceptance       Run acceptance-oriented checks with readiness details and worker status
  smoke-flow       Run end-to-end upload/query smoke flow against the live backend
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
    "smoke" {
        Invoke-Smoke
    }
    "acceptance" {
        Invoke-Acceptance
    }
    "smoke-flow" {
        Invoke-SmokeFlow
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
