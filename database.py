import sqlite3


DATABASE = "waste_management.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = get_db_connection()

    # Waste reports table
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

    # Users table
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

    # Notifications table
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

    # Check existing waste_reports columns
    columns = conn.execute(
        "PRAGMA table_info(waste_reports)"
    ).fetchall()

    column_names = [
        column["name"]
        for column in columns
    ]

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

            conn.execute(
                f"ALTER TABLE waste_reports ADD COLUMN {column} {data_type}"
            )

    # Check existing users columns
    user_columns = conn.execute(
        "PRAGMA table_info(users)"
    ).fetchall()

    user_column_names = [
        column["name"]
        for column in user_columns
    ]

    user_new_columns = {
        "reset_token": "TEXT",
        "reset_token_expiry": "TIMESTAMP"
    }

    for column, data_type in user_new_columns.items():

        if column not in user_column_names:

            conn.execute(
                f"ALTER TABLE users ADD COLUMN {column} {data_type}"
            )

    conn.commit()
    conn.close()


if __name__ == "__main__":

    init_db()

    print("Database updated successfully!")
