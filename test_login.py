import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

def test_login():
    print("\n=== Database Test ===")
    
    # Check database existence
    db_path = 'recruitmentbuddy.db'
    print(f"Database path: {os.path.abspath(db_path)}")
    print(f"Database exists: {os.path.exists(db_path)}")
    
    if not os.path.exists(db_path):
        print("Error: Database file not found!")
        return
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check tables
    print("\nChecking database tables...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    if not tables:
        print("Error: No tables found in database!")
        return
    
    print("\nTables found:")
    for table in tables:
        print(f"- {table['name']}")
        cursor.execute(f"PRAGMA table_info({table['name']})")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  * {col['name']} ({col['type']})")
    
    # Check users table
    print("\nChecking users table...")
    try:
        cursor.execute("SELECT COUNT(*) as count FROM users")
        count = cursor.fetchone()['count']
        print(f"Total users in database: {count}")
        
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        print("\nAll users:")
        for user in users:
            print(f"- ID: {user['id']}")
            print(f"  Email: '{user['email']}'")
            print(f"  Name: {user['first_name']} {user['last_name']}")
            print(f"  Password hash length: {len(user['password'])}")
        
        # Test specific login
        test_email = 'test@example.com'
        test_password = 'test123'
        
        print(f"\nTesting login with:")
        print(f"Email: {test_email}")
        print(f"Password: {test_password}")
        
        cursor.execute('SELECT * FROM users WHERE email = ?', (test_email,))
        user = cursor.fetchone()
        
        if user:
            print("\nUser found!")
            print(f"- ID: {user['id']}")
            print(f"- Email: '{user['email']}'")
            print(f"- Name: {user['first_name']} {user['last_name']}")
            print(f"- Password hash: {user['password'][:20]}...")
            
            # Test password
            if check_password_hash(user['password'], test_password):
                print("\nPassword check: SUCCESS!")
            else:
                print("\nPassword check: FAILED!")
                print("Note: Password hashes don't match")
        else:
            print(f"\nError: No user found with email '{test_email}'")
            
    except Exception as e:
        print(f"\nError during test: {str(e)}")
        import traceback
        print("Traceback:", traceback.format_exc())
    finally:
        conn.close()

if __name__ == '__main__':
    test_login()
