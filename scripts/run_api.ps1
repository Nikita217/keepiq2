$env:PYTHONPATH = (Resolve-Path "..").Path
& .\.venv\Scripts\python.exe -m uvicorn api.app:app --reload --host 127.0.0.1 --port 8000
