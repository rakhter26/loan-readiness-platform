import os
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

_engine = None

def get_engine():
    global _engine
    if _engine is not None:
        return _engine

    db_url = os.environ.get("DATABASE_URL", "")
    if db_url:
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        _engine = create_engine(db_url)
    else:
        _engine = create_engine(
            "sqlite:///feedback.db",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return _engine


def init_db():
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS feedback (
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                step_number INTEGER,
                step_name   TEXT,
                overall_rating     INTEGER,
                ease_rating        INTEGER,
                usefulness_rating  INTEGER,
                loan_awareness     TEXT,
                comments           TEXT,
                business_name      TEXT,
                district           TEXT
            )
        """))
        conn.commit()


def save_feedback(step_number, step_name, overall_rating, ease_rating,
                  usefulness_rating, loan_awareness, comments,
                  business_name=None, district=None):
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO feedback
                    (step_number, step_name, overall_rating, ease_rating,
                     usefulness_rating, loan_awareness, comments, business_name, district)
                VALUES
                    (:step_number, :step_name, :overall_rating, :ease_rating,
                     :usefulness_rating, :loan_awareness, :comments, :business_name, :district)
            """), {
                "step_number": step_number,
                "step_name": step_name,
                "overall_rating": overall_rating,
                "ease_rating": ease_rating,
                "usefulness_rating": usefulness_rating,
                "loan_awareness": loan_awareness,
                "comments": comments or "",
                "business_name": business_name or "",
                "district": district or "",
            })
            conn.commit()
        return True
    except Exception as e:
        print(f"DB save error: {e}")
        return False


def get_all_feedback():
    import pandas as pd
    try:
        engine = get_engine()
        return pd.read_sql("SELECT * FROM feedback ORDER BY created_at DESC", engine)
    except Exception:
        return pd.DataFrame()


def get_step_stats():
    import pandas as pd
    try:
        engine = get_engine()
        return pd.read_sql("""
            SELECT
                step_number,
                step_name,
                COUNT(*)                          AS responses,
                ROUND(AVG(overall_rating), 2)     AS avg_overall,
                ROUND(AVG(ease_rating), 2)        AS avg_ease,
                ROUND(AVG(usefulness_rating), 2)  AS avg_usefulness
            FROM feedback
            GROUP BY step_number, step_name
            ORDER BY step_number
        """, engine)
    except Exception:
        return pd.DataFrame()
