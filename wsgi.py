"""Entrypoint usado pelo Gunicorn em produção: `gunicorn wsgi:app`."""
from app_clinica import app

if __name__ == "__main__":
    app.run()
