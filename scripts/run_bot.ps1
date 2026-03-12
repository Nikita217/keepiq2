$env:PYTHONPATH = (Resolve-Path "..").Path
& .\.venv\Scripts\python.exe -m bot.main
