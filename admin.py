from database import get_db_connection
from werkzeug.security import generate_password_hash


name = input("Enter admin name: ")
email = input("Enter admin email: ")
password = input("Enter admin password: ")


hashed_password = generate_password_hash(password)


conn = get_db_connection()

try:

    conn.execute(
        """
        INSERT INTO users
        (name, email, password, role)
        VALUES (?, ?, ?, ?)
        """,
        (
            name,
            email,
            hashed_password,
            "admin"
        )
    )

    conn.commit()

    print("✅ Admin account created successfully!")

except Exception as error:

    print("❌ Error:", error)

finally:

    conn.close()
