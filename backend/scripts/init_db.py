"""Deprecated: schema is now managed by Alembic migrations.

Run `uv run alembic upgrade head` (from backend/) instead of this script.
"""

if __name__ == "__main__":
    raise SystemExit("Use `uv run alembic upgrade head` to create/update the database schema.")
