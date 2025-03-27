from app import app, get_db
import os

def init_database():
    print("Initializing database...")
    
    # Remove existing database if it exists
    if os.path.exists('recruitmentbuddy.db'):
        print("Removing existing database...")
        os.remove('recruitmentbuddy.db')
    
    # Initialize the database with schema
    with app.app_context():
        try:
            db = get_db()
            print("Database connection established")
            
            # Read and execute schema
            with open('schema.sql', 'r') as f:
                schema = f.read()
                print("Executing schema...")
                db.executescript(schema)
                db.commit()
                print("Schema executed successfully")
            
            # Create test user
            print("\nCreating test user...")
            from werkzeug.security import generate_password_hash
            
            test_user = {
                'first_name': 'Test',
                'last_name': 'User',
                'email': 'test@example.com',
                'password': generate_password_hash('test123')
            }
            
            db.execute(
                'INSERT INTO users (first_name, last_name, email, password) VALUES (?, ?, ?, ?)',
                (test_user['first_name'], test_user['last_name'], test_user['email'], test_user['password'])
            )
            db.commit()
            print("Test user created successfully")
            
            # Verify user was created
            user = db.execute('SELECT * FROM users WHERE email = ?', ('test@example.com',)).fetchone()
            if user:
                print(f"\nVerification successful:")
                print(f"User ID: {user['id']}")
                print(f"Name: {user['first_name']} {user['last_name']}")
                print(f"Email: {user['email']}")
            else:
                print("Error: User verification failed!")
            
        except Exception as e:
            print(f"Error initializing database: {str(e)}")
            raise

if __name__ == '__main__':
    init_database()
