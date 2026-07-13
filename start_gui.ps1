$env:PYTHONPATH = "src"

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    .\.venv\Scripts\Activate.ps1
}

python -m pixel_bot.interface.control_center