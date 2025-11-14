web: python start.py
bot: PYTHONPATH=/app:/app/src python -m src.main
webapp: PYTHONPATH=/app:/app/src uvicorn src.web.main:app --host 0.0.0.0 --port $PORT

