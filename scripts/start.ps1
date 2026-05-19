param(
    [string]$Port = $env:PORT -or "8000"
)

if (-not (Test-Path -Path .venv)) {
    python -m venv .venv
    . .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    python -m pip install -r src/requirements.txt
} else {
    . .\.venv\Scripts\Activate.ps1
}

Write-Host "Starting Gunicorn on 0.0.0.0:$Port"

# Start gunicorn (requires gunicorn to be available in the venv)
& gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$Port "api.main:create_app"
