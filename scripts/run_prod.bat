@echo off
REM Serve the app with the waitress production WSGI server (Windows).
call .venv\Scripts\activate.bat
waitress-serve --host=127.0.0.1 --port=8000 run:app
