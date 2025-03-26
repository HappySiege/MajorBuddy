import pytest
import sqlite3
import tempfile
import os
from pathlib import Path

@pytest.fixture(scope='session')
def test_db():
    """Create a test database and populate it with test data"""
    db_fd, db_path = tempfile.mkstemp()
    
    # Create test database
    conn = sqlite3.connect(db_path)
    
    # Read and execute schema
    with open(Path(__file__).parent.parent / 'schema.sql', 'r') as f:
        conn.executescript(f.read())
    
    # Insert test data
    test_majors = [
        (
            "Test Major 1",
            "Test Description 1",
            "Test Careers 1",
            "Test Skills 1",
            0.8, 0.6, 0.4, 0.7
        ),
        (
            "Test Major 2",
            "Test Description 2",
            "Test Careers 2",
            "Test Skills 2",
            0.6, 0.8, 0.7, 0.5
        )
    ]
    
    conn.executemany('''
        INSERT INTO majors (
            name, description, career_opportunities, required_skills,
            analytical_weight, creative_weight, social_weight, technical_weight
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', test_majors)
    
    # Insert test personality types
    test_personality_types = [
        ('INTJ', 'Architect', 'Test Description'),
        ('INTP', 'Logician', 'Test Description'),
        ('ENTJ', 'Commander', 'Test Description'),
        ('ISTJ', 'Logistician', 'Test Description')
    ]
    
    conn.executemany('''
        INSERT INTO personality_types (code, name, description)
        VALUES (?, ?, ?)
    ''', test_personality_types)
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def sample_major_data():
    """Sample major data for testing"""
    return {
        "name": "Test Major",
        "description": "Test Description",
        "career_opportunities": "Test Careers",
        "required_skills": "Test Skills",
        "analytical_weight": 0.7,
        "creative_weight": 0.6,
        "social_weight": 0.8,
        "technical_weight": 0.5
    }

@pytest.fixture
def sample_personality_data():
    """Sample personality type data for testing"""
    return {
        "code": "TEST",
        "name": "Test Type",
        "description": "Test Description",
        "strengths": "Test Strengths",
        "weaknesses": "Test Weaknesses"
    }
