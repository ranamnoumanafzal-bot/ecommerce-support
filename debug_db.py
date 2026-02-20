import sqlite3
import os

db_path = 'ecommerce.db'
if not os.path.exists(db_path):
    print(f"Database file {db_path} not found!")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables: {tables}")
        
        if ('support_tickets',) in tables:
            cursor.execute("SELECT * FROM support_tickets")
            tickets = cursor.fetchall()
            print(f"Tickets count: {len(tickets)}")
            for t in tickets:
                print(t)
        else:
            print("Table 'support_tickets' does not exist.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
