$env:PYTHONPATH = (Resolve-Path "..").Path
& .\.venv\Scripts\python.exe -m jobs.runner
