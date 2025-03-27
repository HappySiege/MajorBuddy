from app import get_db, app
from werkzeug.security import generate_password_hash

def create_test_account():
    with app.app_context():
        db = get_db()
        
        # Test account credentials
        test_user = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password': 'test123'  # Simple password for testing
        }
        
        # Check if the test account already exists
        existing_user = db.execute(
            'SELECT id FROM users WHERE email = ?', (test_user['email'],)
        ).fetchone()
        
        if existing_user is None:
            # Create the test account
            db.execute(
                'INSERT INTO users (first_name, last_name, email, password) VALUES (?, ?, ?, ?)',
                (
                    test_user['first_name'],
                    test_user['last_name'],
                    test_user['email'],
                    generate_password_hash(test_user['password'])
                )
            )
            db.commit()
            print("Test account created successfully!")
            print(f"Email: {test_user['email']}")
            print(f"Password: {test_user['password']}")
        else:
            print("Test account already exists!")
            print(f"Email: {test_user['email']}")
            print(f"Password: {test_user['password']}")

if __name__ == '__main__':
    create_test_account()
