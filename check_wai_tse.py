from integrated_database import IntegratedDatabase
import sqlite3

db = IntegratedDatabase()
conn = db.get_connection()
cursor = conn.cursor()

cursor.execute('SELECT username, email, email_verified FROM users WHERE username = "Ken"')
result = cursor.fetchone()

if result:
    print(f"Username: {result[0]}")
    print(f"Email: {result[1]}")
    print(f"Email Verified: {bool(result[2])}")
    print(f"Raw value: {result[2]}")
else:
    print("Ken not found")

conn.close()
