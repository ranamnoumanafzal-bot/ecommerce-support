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
            print(f"\n--- Tickets count: {len(tickets)} ---")
            for t in tickets:
                print(t)
        
        if ('conversation_analytics',) in tables:
            cursor.execute("SELECT * FROM conversation_analytics")
            analytics = cursor.fetchall()
            print(f"\n--- Analytics count: {len(analytics)} ---")
            for a in analytics:
                print(a)
        else:
            print("\nTable 'conversation_analytics' does not exist.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
