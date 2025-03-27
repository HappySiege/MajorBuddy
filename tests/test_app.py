import os
import tempfile
import pytest
import json
from pathlib import Path
from app import app

def init_test_db(db):
    """Initialize test database with schema"""
    schema_path = Path(__file__).parent.parent / 'schema.sql'
    with open(schema_path, 'r') as f:
        db.executescript(f.read())

@pytest.fixture
def client():
    """Create a test client for the app"""
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    app.config['DATABASE'] = db_path
    app.config['TESTING'] = True

    # Other setup actions
    with app.test_client() as client:
        with app.app_context():
            from app import get_db
            db = get_db()
            init_test_db(db)
            
            # Add test data
            cursor = db.cursor()
            
            # Add test majors
            cursor.execute('''
                INSERT INTO majors (
                    name, description, career_opportunities, required_skills,
                    analytical_weight, creative_weight, social_weight, technical_weight
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                "Computer Science",
                "Study of computation, programming, and information systems",
                "Software Engineer, Data Scientist, Systems Analyst",
                "Programming, problem-solving, mathematical reasoning",
                0.9, 0.6, 0.4, 0.9
            ))
            
            # Add test personality types
            cursor.execute('''
                INSERT INTO personality_types (code, name, description)
                VALUES (?, ?, ?)
            ''', ('INTJ', 'Architect', 'Test personality type description'))
            
            db.commit()
            
        yield client

    # Cleanup - close and remove the temporary file
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def sample_questionnaire_data():
    """Sample questionnaire data for testing"""
    return {
        "scores": {
            "analytical_score": 8,
            "creative_score": 6,
            "social_score": 7,
            "technical_score": 9
        },
        "responses": {
            "q1": "Yes",
            "q2": "No",
            "q3": "Maybe"
        }
    }

def test_index_page(client):
    """Test the index page loads correctly"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Welcome to RecruitmentBuddy' in response.data

def test_questionnaire_page(client):
    """Test the questionnaire page loads correctly"""
    response = client.get('/questionnaire')
    assert response.status_code == 200
    assert b'Questionnaire' in response.data

def test_submit_questionnaire_valid(client, sample_questionnaire_data):
    """Test submitting valid questionnaire data"""
    response = client.post('/submit_questionnaire',
                         data=json.dumps(sample_questionnaire_data),
                         content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'response_id' in data

def test_submit_questionnaire_invalid(client):
    """Test submitting invalid questionnaire data"""
    invalid_data = {
        "scores": {
            "analytical_score": 15,  # Invalid score > 10
            "creative_score": 6,
            "social_score": 7,
            "technical_score": 9
        }
    }
    response = client.post('/submit_questionnaire',
                         data=json.dumps(invalid_data),
                         content_type='application/json')
    assert response.status_code == 500
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert 'message' in data

def test_get_majors_api(client):
    """Test the /api/majors endpoint"""
    response = client.get('/api/majors')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) > 0
    major = data[0]
    required_fields = ['id', 'name', 'description', 'analytical_weight',
                      'creative_weight', 'social_weight', 'technical_weight']
    for field in required_fields:
        assert field in major

def test_get_personality_types_api(client):
    """Test the /api/personality-types endpoint"""
    response = client.get('/api/personality-types')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) > 0
    ptype = data[0]
    required_fields = ['id', 'code', 'name', 'description']
    for field in required_fields:
        assert field in ptype

def test_recommendations_page_without_session(client):
    """Test recommendations page without session data"""
    response = client.get('/recommendations')
    assert response.status_code == 302  # Should redirect to questionnaire

def test_recommendations_page_with_session(client, sample_questionnaire_data):
    """Test recommendations page with session data"""
    # First submit questionnaire to set up data
    response = client.post('/submit_questionnaire',
                         data=json.dumps(sample_questionnaire_data),
                         content_type='application/json')
    assert response.status_code == 200
    
    # Then check recommendations
    response = client.get('/recommendations')
    assert response.status_code == 200
    assert b'Your Recommended Majors' in response.data

def test_personality_type_calculation(client, sample_questionnaire_data):
    """Test personality type calculation"""
    response = client.post('/submit_questionnaire',
                         data=json.dumps(sample_questionnaire_data),
                         content_type='application/json')
    assert response.status_code == 200
    
    with client.session_transaction() as session:
        session['scores'] = sample_questionnaire_data['scores']
    
    response = client.get('/recommendations')
    assert response.status_code == 200
    assert b'Your Personality Type:' in response.data
    assert b'Dimension Scores:' in response.data

def test_database_connection(client):
    """Test database connection and basic query"""
    with app.app_context():
        from app import get_db
        db = get_db()
        cursor = db.cursor()
        
        # Test majors table
        cursor.execute('SELECT COUNT(*) FROM majors')
        count = cursor.fetchone()[0]
        assert isinstance(count, int)
        assert count > 0
        
        # Test personality_types table
        cursor.execute('SELECT COUNT(*) FROM personality_types')
        count = cursor.fetchone()[0]
        assert isinstance(count, int)
        assert count > 0

def test_input_validation():
    """Test the questionnaire input validation function"""
    from app import validate_questionnaire_input
    
    # Test valid data
    valid_data = {
        "scores": {
            "analytical_score": 7,
            "creative_score": 6,
            "social_score": 8,
            "technical_score": 9
        }
    }
    assert validate_questionnaire_input(valid_data) == True
    
    # Test invalid score
    invalid_data = {
        "scores": {
            "analytical_score": 11,  # Invalid score > 10
            "creative_score": 6,
            "social_score": 8,
            "technical_score": 9
        }
    }
    with pytest.raises(ValueError):
        validate_questionnaire_input(invalid_data)
    
    # Test missing field
    incomplete_data = {
        "scores": {
            "analytical_score": 7,
            "creative_score": 6,
            "technical_score": 9
        }
    }
    with pytest.raises(ValueError):
        validate_questionnaire_input(incomplete_data)
