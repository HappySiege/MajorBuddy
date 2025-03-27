import sqlite3
from app import app

def verify_database():
    with app.app_context():
        conn = sqlite3.connect('recruitmentbuddy.db')
        cursor = conn.cursor()
        
        print("\nVerifying users in database:\n")
        print("=" * 70)
        
        try:
            cursor.execute("SELECT id, first_name, last_name, email FROM users")
            users = cursor.fetchall()
            if users:
                for user in users:
                    print(f"User ID: {user[0]}")
                    print(f"Name: {user[1]} {user[2]}")
                    print(f"Email: {user[3]}")
                    print("-" * 70)
            else:
                print("No users found in the database!")
        except sqlite3.OperationalError as e:
            print(f"Error accessing users table: {e}")
        
        print("\nVerifying majors in database:\n")
        print("=" * 70)
        
        try:
            cursor.execute("""
                SELECT name, description, career_opportunities, required_skills,
                       analytical_weight, creative_weight, social_weight, technical_weight 
                FROM majors
            """)
            
            majors = cursor.fetchall()
            if majors:
                for row in majors:
                    print(f"Major: {row[0]}")
                    print(f"Description: {row[1]}")
                    print(f"Careers: {row[2]}")
                    print(f"Required Skills: {row[3]}")
                    print(f"Weights:")
                    print(f"  - Analytical: {row[4]:.1f}")
                    print(f"  - Creative:   {row[5]:.1f}")
                    print(f"  - Social:     {row[6]:.1f}")
                    print(f"  - Technical:  {row[7]:.1f}")
                    print("-" * 70)
                
                print(f"\nTotal number of majors in database: {len(majors)}")
            else:
                print("No majors found in the database!")
        except sqlite3.OperationalError as e:
            print(f"Error accessing majors table: {e}")

if __name__ == '__main__':
    verify_database()
