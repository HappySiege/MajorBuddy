import sqlite3
from pathlib import Path

def populate_majors():
    # Connect to database
    conn = sqlite3.connect('majorbuddy.db')
    cursor = conn.cursor()
    
    # Sample majors with their dimension weights
    majors = [
        {
            'name': 'Computer Science',
            'description': 'Study of computation, programming, and information systems',
            'career_opportunities': 'Software Developer, Data Scientist, Systems Analyst, AI Engineer',
            'required_skills': 'Problem-solving, Mathematical thinking, Programming, Logical reasoning',
            'weights': (0.9, 0.6, 0.4, 0.8)  # analytical, creative, social, technical
        },
        {
            'name': 'Psychology',
            'description': 'Study of human behavior, mental processes, and emotional well-being',
            'career_opportunities': 'Counselor, Research Psychologist, Human Resources, Social Worker',
            'required_skills': 'Active listening, Empathy, Research, Critical thinking',
            'weights': (0.7, 0.5, 0.9, 0.3)
        },
        {
            'name': 'Fine Arts',
            'description': 'Study and practice of visual arts, including painting, sculpture, and digital media',
            'career_opportunities': 'Artist, Art Director, Curator, Art Teacher',
            'required_skills': 'Creativity, Visual thinking, Artistic technique, Design principles',
            'weights': (0.3, 0.9, 0.6, 0.7)
        },
        {
            'name': 'Mechanical Engineering',
            'description': 'Design and manufacturing of mechanical systems and devices',
            'career_opportunities': 'Mechanical Engineer, Product Designer, Project Manager, Research Engineer',
            'required_skills': 'Mathematics, Physics, CAD, Problem-solving',
            'weights': (0.8, 0.7, 0.5, 0.9)
        },
        {
            'name': 'Business Administration',
            'description': 'Study of business operations, management, and organizational leadership',
            'career_opportunities': 'Business Manager, Entrepreneur, Consultant, Project Manager',
            'required_skills': 'Leadership, Analysis, Communication, Strategic thinking',
            'weights': (0.6, 0.6, 0.8, 0.4)
        },
        {
            'name': 'Nursing',
            'description': 'Healthcare profession focused on patient care and medical support',
            'career_opportunities': 'Registered Nurse, Nurse Practitioner, Clinical Specialist, Healthcare Manager',
            'required_skills': 'Patient care, Medical knowledge, Communication, Critical thinking',
            'weights': (0.7, 0.4, 0.9, 0.7)
        },
        {
            'name': 'English Literature',
            'description': 'Study of literature, writing, and literary analysis',
            'career_opportunities': 'Writer, Editor, Teacher, Content Strategist',
            'required_skills': 'Writing, Analysis, Research, Communication',
            'weights': (0.6, 0.8, 0.7, 0.3)
        },
        {
            'name': 'Physics',
            'description': 'Study of matter, energy, and the fundamental forces of nature',
            'career_opportunities': 'Physicist, Research Scientist, Data Analyst, Engineer',
            'required_skills': 'Mathematics, Problem-solving, Research, Analytical thinking',
            'weights': (0.9, 0.5, 0.4, 0.8)
        }
    ]
    
    # Insert majors into database
    for major in majors:
        cursor.execute('''
            INSERT INTO majors (
                name, description, career_opportunities, required_skills,
                analytical_weight, creative_weight, social_weight, technical_weight
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            major['name'],
            major['description'],
            major['career_opportunities'],
            major['required_skills'],
            major['weights'][0],  # analytical
            major['weights'][1],  # creative
            major['weights'][2],  # social
            major['weights'][3]   # technical
        ))
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    print("Database populated with sample majors!")

if __name__ == '__main__':
    # Create database if it doesn't exist
    if not Path('majorbuddy.db').exists():
        conn = sqlite3.connect('majorbuddy.db')
        with open('schema.sql', 'r') as f:
            conn.executescript(f.read())
        conn.close()
    
    # Populate with sample data
    populate_majors()
