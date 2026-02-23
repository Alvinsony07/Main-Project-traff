import sqlite3

try:
    conn = sqlite3.connect('traffic.db')
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE user ADD COLUMN full_name VARCHAR(150)")
    cursor.execute("ALTER TABLE user ADD COLUMN phone_number VARCHAR(20)")
    cursor.execute("ALTER TABLE user ADD COLUMN organization VARCHAR(150)")
    conn.commit()
    conn.close()
    print("Columns added to traffic.db successfully.")
except Exception as e:
    print(e)
