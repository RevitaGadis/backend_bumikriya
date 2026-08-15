<<<<<<< HEAD
web: alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
=======
web: python scripts/init_db.py && alembic upgrade head && python scripts/create_membership_tables.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
>>>>>>> 6906e6475b2f7f0fb276ee3b9cd7e137bcbf708e
