"""Application entry point.

Runs the Flask development server locally (`python run.py`) or serves the app
through a production WSGI server such as waitress:

    waitress-serve --host=127.0.0.1 --port=8000 run:app
"""
from dotenv import load_dotenv

from app import create_app

load_dotenv()

app = create_app()

if __name__ == "__main__":
    app.run(host=app.config["HOST"], port=app.config["PORT"])
