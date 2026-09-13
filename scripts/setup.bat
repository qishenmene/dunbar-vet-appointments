@echo off
REM Clean-checkout setup for Windows: venv, dependencies, config, database.
python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist .env copy .env.example .env
flask --app run.py init-db
echo Setup complete. Run scripts\run_dev.bat to start the app.
