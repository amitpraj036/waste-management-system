import os
import sqlite3

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()


class DBRow(dict):
    """Row supporting both row["column"] and row[0]."""
    def __init__(self, columns, values):
        super().__init__(zip(columns, values))
        self._values = tuple(values)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return super().__getitem__(key)


class DBResult:
    def __init__(self, cursor):
        self.cursor = cursor
        self.columns = [d[0] for d in (cursor.description or [])]

    def fetchone(self):
        row = self.cursor.fetchone()
        return None if row is None else DBRow(self.columns, row)

    def fetchall(self):
        return [DBRow(self.columns, row) for row in self.cursor.fetchall()]


class DBConnection:
    def __init__(self, raw, postgres=False):
        self.raw = raw
        self.postgres = postgres

    def execute(self, sql, params=()):
        if self.postgres:
            sql = sql.replace("?", "%s")
        cursor = self.raw.cursor()
        cursor.execute(sql, params)
        return DBResult(cursor)

    def commit(self):
        self.raw.commit()

    def close(self):
        self.raw.close()


def get_db_connection():
    if DATABASE_URL:
        try:
            import psycopg2
            url = DATABASE_URL
            if url.startswith("postgres://"):
                url = "postgresql://" + url[len("postgres://"):]
            raw = psycopg2.connect(url, sslmode="require")
            return DBConnection(raw, postgres=True)
        except Exception as exc:
            raise RuntimeError(
                "PostgreSQL connection failed. Check DATABASE_URL in Render Environment Variables."
            ) from exc

    raw = sqlite3.connect("waste_management.db")
    raw.row_factory = sqlite3.Row
    return DBConnection(raw, postgres=False)


def init_db():
    conn = get_db_connection()

    if conn.postgres:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS waste_reports (
                id BIGSERIAL PRIMARY KEY,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                location TEXT NOT NULL,
                image TEXT,
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                status TEXT DEFAULT 'Pending',
                collector_name TEXT,
                pickup_date TEXT,
                pickup_time TEXT,
                collection_notes TEXT,
                user_id BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGSERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                reset_token TEXT,
                reset_token_expiry TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                report_id BIGINT,
                message TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Safe upgrades for older PostgreSQL databases.
        report_cols = {
            "latitude": "DOUBLE PRECISION",
            "longitude": "DOUBLE PRECISION",
            "collector_name": "TEXT",
            "pickup_date": "TEXT",
            "pickup_time": "TEXT",
            "collection_notes": "TEXT",
            "user_id": "BIGINT"
        }
        for col, typ in report_cols.items():
            conn.execute(f"ALTER TABLE waste_reports ADD COLUMN IF NOT EXISTS {col} {typ}")

        user_cols = {
            "reset_token": "TEXT",
            "reset_token_expiry": "TIMESTAMP"
        }
        for col, typ in user_cols.items():
            conn.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} {typ}")
    else:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS waste_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                location TEXT NOT NULL,
                image TEXT,
                latitude REAL,
                longitude REAL,
                status TEXT DEFAULT 'Pending',
                collector_name TEXT,
                pickup_date TEXT,
                pickup_time TEXT,
                collection_notes TEXT,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                reset_token TEXT,
                reset_token_expiry TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                report_id INTEGER,
                message TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        columns = conn.execute("PRAGMA table_info(waste_reports)").fetchall()
        column_names = [column["name"] for column in columns]
        new_columns = {
            "latitude": "REAL",
            "longitude": "REAL",
            "collector_name": "TEXT",
            "pickup_date": "TEXT",
            "pickup_time": "TEXT",
            "collection_notes": "TEXT",
            "user_id": "INTEGER"
        }
        for column, data_type in new_columns.items():
            if column not in column_names:
                conn.execute(f"ALTER TABLE waste_reports ADD COLUMN {column} {data_type}")

        user_columns = conn.execute("PRAGMA table_info(users)").fetchall()
        user_column_names = [column["name"] for column in user_columns]
        user_new_columns = {
            "reset_token": "TEXT",
            "reset_token_expiry": "TIMESTAMP"
        }
        for column, data_type in user_new_columns.items():
            if column not in user_column_names:
                conn.execute(f"ALTER TABLE users ADD COLUMN {column} {data_type}")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database updated successfully!")
