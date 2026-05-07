import os
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "feedback.db"


def _is_railway():
    return bool(os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("RAILWAY_PROJECT_ID"))


def init_db():
    if _is_railway():
        return
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            created_at        TEXT DEFAULT (datetime('now')),
            step_number       INTEGER,
            step_name         TEXT,
            overall_rating    INTEGER,
            ease_rating       INTEGER,
            usefulness_rating INTEGER,
            loan_awareness    TEXT,
            comments          TEXT,
            business_name     TEXT,
            district          TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_feedback(step_number, step_name, overall_rating, ease_rating,
                  usefulness_rating, loan_awareness, comments,
                  business_name=None, district=None):
    if _is_railway():
        return True  # email-only on Railway; no local DB

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            INSERT INTO feedback
                (step_number, step_name, overall_rating, ease_rating,
                 usefulness_rating, loan_awareness, comments, business_name, district)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (step_number, step_name, overall_rating, ease_rating,
              usefulness_rating, loan_awareness, comments or "",
              business_name or "", district or ""))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"DB error: {e}")
        return False


def get_all_feedback():
    import pandas as pd
    if not DB_PATH.exists():
        return pd.DataFrame()
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql("SELECT * FROM feedback ORDER BY created_at DESC", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()


def get_step_stats():
    import pandas as pd
    if not DB_PATH.exists():
        return pd.DataFrame()
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql("""
            SELECT
                step_number,
                step_name,
                COUNT(*)                              AS responses,
                ROUND(AVG(overall_rating), 2)         AS avg_overall,
                ROUND(AVG(ease_rating), 2)            AS avg_ease,
                ROUND(AVG(usefulness_rating), 2)      AS avg_usefulness
            FROM feedback
            GROUP BY step_number, step_name
            ORDER BY step_number
        """, conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()
