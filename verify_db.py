import sqlite3

def verify_majors():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    print("\nVerifying majors in database:\n")
    print("=" * 70)
    
    cursor.execute("""
        SELECT name, description, career_opportunities, required_skills,
               analytical_weight, creative_weight, social_weight, technical_weight 
        FROM majors
    """)
    
    for row in cursor.fetchall():
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
    
    # Get total count
    cursor.execute("SELECT COUNT(*) FROM majors")
    count = cursor.fetchone()[0]
    print(f"\nTotal number of majors in database: {count}")
    
    conn.close()

if __name__ == '__main__':
    verify_majors()
