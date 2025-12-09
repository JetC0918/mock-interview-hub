param (
    [Parameter(Mandatory=$false)]
    [string]$Command = "help"
)

function Show-Usage {
    Write-Host "Usage: .\manage.ps1 [command]"
    Write-Host "Commands:"
    Write-Host "  install   - Install dependencies (uv sync)"
    Write-Host "  run       - Run the development server"
    Write-Host "  test      - Run tests"
    Write-Host "  clean     - Remove cache directories"
}

switch ($Command) {
    "install" {
        Write-Host "Running install..."
        uv sync
    }
    "run" {
        Write-Host "Starting server..."
        uv run uvicorn app.main:app --reload --port 8000
    }
    "test" {
        Write-Host "Running tests..."
        uv run pytest
    }
    "clean" {
        Write-Host "Cleaning cache..."
        Get-ChildItem -Path . -Recurse -Directory | Where-Object { $_.Name -in "__pycache__", ".pytest_cache" } | Remove-Item -Recurse -Force
        Write-Host "Clean complete."
    }
    Default {
        Show-Usage
    }
}
