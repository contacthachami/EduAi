param(
  [int]$BackendPort = 8000,
  [int]$FrontendPort = 3000
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$FrontendDir = Join-Path $Root "frontend"
$HealthUrl = "http://127.0.0.1:$BackendPort/health"
$BackendUrl = "http://127.0.0.1:$BackendPort"
$LogDir = Join-Path $Root "logs"
$BackendOutLog = Join-Path $LogDir "backend-dev.out.log"
$BackendErrLog = Join-Path $LogDir "backend-dev.err.log"

function Test-Url {
  param([string]$Url)
  try {
    $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
    return $response.StatusCode -ge 200 -and $response.StatusCode -lt 500
  } catch {
    return $false
  }
}

function Wait-Backend {
  param([string]$Url, [int]$Seconds = 180)
  $deadline = (Get-Date).AddSeconds($Seconds)
  while ((Get-Date) -lt $deadline) {
    if (Test-Url $Url) {
      return $true
    }
    Start-Sleep -Seconds 2
  }
  return $false
}

Write-Host "EduAI dev launcher" -ForegroundColor Cyan
Write-Host "Root: $Root"

if (Get-Command docker -ErrorAction SilentlyContinue) {
  try {
    Write-Host "Starting MongoDB with Docker Compose..."
    Push-Location $Root
    docker compose up -d mongodb | Out-Host
  } catch {
    Write-Warning "MongoDB was not started by Docker Compose. Start MongoDB manually if the backend cannot connect."
  } finally {
    Pop-Location
  }
} else {
  Write-Warning "Docker is not available. Make sure MongoDB is running on localhost:27017."
}

$backendProcess = $null
$backendAlreadyRunning = Test-Url $HealthUrl

if ($backendAlreadyRunning) {
  Write-Host "Backend already healthy at $HealthUrl"
} else {
  New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
  foreach ($logFile in @($BackendOutLog, $BackendErrLog)) {
    if (Test-Path $logFile) {
      Remove-Item -LiteralPath $logFile -Force
    }
  }

  Write-Host "Starting FastAPI backend on port $BackendPort..."
  $backendProcess = Start-Process `
    -FilePath "python" `
    -ArgumentList @("-m", "uvicorn", "backend.main:app", "--reload", "--port", "$BackendPort") `
    -WorkingDirectory $Root `
    -RedirectStandardOutput $BackendOutLog `
    -RedirectStandardError $BackendErrLog `
    -PassThru `
    -WindowStyle Hidden

  if (-not (Wait-Backend $HealthUrl)) {
    if ($backendProcess -and -not $backendProcess.HasExited) {
      Stop-Process -Id $backendProcess.Id -Force
    }
    throw "Backend did not become healthy at $HealthUrl. Check $BackendOutLog and $BackendErrLog"
  }

  Write-Host "Backend ready at $BackendUrl"
}

try {
  Write-Host "Starting Next.js frontend on port $FrontendPort..."
  Push-Location $FrontendDir
  $env:BACKEND_URL = $BackendUrl
  npm run dev -- --port $FrontendPort
} finally {
  Pop-Location
  if ($backendProcess -and -not $backendProcess.HasExited) {
    Write-Host "Stopping backend process..."
    Stop-Process -Id $backendProcess.Id -Force
  }
}
