from flask import Flask, render_template, request, jsonify, session, redirect, url_for, g
from pathlib import Path
import sqlite3
import json
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import random
from functools import wraps
from werkzeug.exceptions import HTTPException
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_mapping(
    DATABASE='majorbuddy.db',
    SECRET_KEY='your-secret-key',  # Change this in production!
    MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16MB max request size
)

def get_db():
    """Get database connection, storing it in g object"""
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    """Close database connection at the end of request"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize database with schema"""
    if not Path(app.config['DATABASE']).exists():
        with app.app_context():
            db = get_db()
            with app.open_resource('schema.sql', mode='r') as f:
                db.cursor().executescript(f.read())
            db.commit()

def validate_questionnaire_input(data):
    """Validate questionnaire input data"""
    if 'scores' not in data:
        raise ValueError("Missing 'scores' field in questionnaire data")
        
    required_fields = ['analytical_score', 'creative_score', 'social_score', 'technical_score']
    scores = data['scores']
    
    if not all(field in scores for field in required_fields):
        raise ValueError("Missing required fields in scores data")
    
    for field in required_fields:
        score = scores[field]
        if not isinstance(score, (int, float)) or score < 0 or score > 10:
            raise ValueError(f"Invalid score for {field}. Must be number between 0 and 10")

    return True

def get_personality_type(scores):
    """Calculate personality type based on questionnaire scores."""
    try:
        # Simple mapping of scores to personality dimensions
        # High analytical/technical -> Thinking (T), low -> Feeling (F)
        # High creative -> Intuitive (N), low -> Sensing (S)
        # High social -> Extravert (E), low -> Introvert (I)
        # High technical/creative -> Perceiving (P), low -> Judging (J)
        
        # Calculate each dimension
        ei_score = scores['social_score'] / 10.0
        sn_score = scores['creative_score'] / 10.0
        tf_score = (scores['analytical_score'] + scores['technical_score']) / 20.0
        jp_score = (scores['technical_score'] + scores['creative_score']) / 20.0
        
        # Determine type code
        type_code = ''
        type_code += 'E' if ei_score >= 0.5 else 'I'
        type_code += 'N' if sn_score >= 0.5 else 'S'
        type_code += 'T' if tf_score >= 0.5 else 'F'
        type_code += 'P' if jp_score >= 0.5 else 'J'
        
        # Calculate dimension scores
        dimension_scores = {
            'ei': ei_score,
            'sn': sn_score,
            'tf': tf_score,
            'jp': jp_score
        }
        
        # Return both the type code and dimension scores
        return {'code': type_code, 'scores': dimension_scores}, dimension_scores
    except Exception as e:
        logger.error(f"Error in personality type calculation: {str(e)}")
        raise

def get_personality_type_id(type_code):
    """Get or create a personality type record."""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Try to get existing type
        cursor.execute('SELECT id FROM personality_types WHERE code = ?', (type_code,))
        result = cursor.fetchone()
        
        if result:
            return result['id']
        else:
            # Create new type with basic info
            cursor.execute('''
                INSERT INTO personality_types (code, name, description)
                VALUES (?, ?, ?)
            ''', (type_code, f"Type {type_code}", "Personality type description"))
            db.commit()
            return cursor.lastrowid
    except Exception as e:
        logger.error(f"Error getting/creating personality type: {str(e)}")
        raise

def calculate_major_matches(scores, personality_type_id=None):
    """Calculate match scores for all majors based on questionnaire scores and personality."""
    db = get_db()
    majors = db.execute('SELECT * FROM majors').fetchall()
    
    # Convert scores to 0-1 scale
    scaler = MinMaxScaler()
    score_values = np.array([[
        scores['analytical_score'],
        scores['creative_score'],
        scores['social_score'],
        scores['technical_score']
    ]])
    normalized_scores = scaler.fit_transform(score_values)[0]
    
    matches = []
    for major in majors:
        # Calculate match percentage for each dimension
        analytical_match = 1 - abs(normalized_scores[0] - major['analytical_weight'])
        creative_match = 1 - abs(normalized_scores[1] - major['creative_weight'])
        social_match = 1 - abs(normalized_scores[2] - major['social_weight'])
        technical_match = 1 - abs(normalized_scores[3] - major['technical_weight'])
        
        # Get personality match if available
        personality_match = 0.5  # Default to neutral
        if personality_type_id:
            personality_match_data = db.execute('''
                SELECT match_strength 
                FROM major_personality_matches 
                WHERE major_id = ? AND personality_type_id = ?
            ''', (major['id'], personality_type_id)).fetchone()
            
            if personality_match_data:
                personality_match = personality_match_data['match_strength']
        
        # Calculate overall match score (weighted average)
        match_score = (
            (analytical_match + creative_match + social_match + technical_match) / 4 * 0.7 +  # Skills weight
            personality_match * 0.3  # Personality weight
        )
        
        matches.append({
            'major_id': major['id'],
            'name': major['name'],
            'description': major['description'],
            'career_opportunities': major['career_opportunities'],
            'required_skills': major['required_skills'],
            'match_score': match_score,
            'analytical_match': analytical_match,
            'creative_match': creative_match,
            'social_match': social_match,
            'technical_match': technical_match,
            'personality_match': personality_match
        })
    
    # Sort matches by score in descending order
    matches.sort(key=lambda x: x['match_score'], reverse=True)
    return matches

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/questionnaire')
def questionnaire():
    return render_template('questionnaire.html')

@app.route('/submit_questionnaire', methods=['POST'])
def submit_questionnaire():
    try:
        data = request.get_json()
        validate_questionnaire_input(data)
        
        # Get or create personality type
        primary_type, _ = get_personality_type(data['scores'])
        personality_type_id = get_personality_type_id(primary_type['code'])
        
        # Store questionnaire response
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            INSERT INTO questionnaire_responses 
            (analytical_score, creative_score, social_score, technical_score, 
             personality_type_id, raw_responses)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data['scores']['analytical_score'],
            data['scores']['creative_score'],
            data['scores']['social_score'],
            data['scores']['technical_score'],
            personality_type_id,
            json.dumps(data.get('responses', {}))  # Make responses optional
        ))
        response_id = cursor.lastrowid
        
        # Calculate and store major recommendations
        matches = calculate_major_matches(data['scores'], personality_type_id)
        
        for match in matches:
            cursor.execute('''
                INSERT INTO major_recommendations
                (response_id, major_id, match_score, analytical_match, 
                 creative_match, social_match, technical_match,
                 personality_match)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                response_id,
                match['major_id'],
                match['match_score'],
                match['analytical_match'],
                match['creative_match'],
                match['social_match'],
                match['technical_match'],
                match.get('personality_match', 0.5)  # Default to neutral if not calculated
            ))
        
        db.commit()
        session['scores'] = data['scores']  # Store scores in session
        return jsonify({'status': 'success', 'response_id': response_id})
    except ValueError as e:
        logger.error(f"Error in submitting questionnaire: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    except Exception as e:
        logger.error(f"Error in submitting questionnaire: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/recommendations')
def recommendations():
    try:
        if 'scores' not in session:
            return redirect(url_for('questionnaire'))
        
        # Get personality type and recommendations
        scores = session['scores']
        personality_type, dimension_scores = get_personality_type(scores)
        
        # Get major recommendations
        db = get_db()
        cursor = db.cursor()
        
        # Get all majors with their weights
        cursor.execute('''
            SELECT id, name, description, career_opportunities, required_skills,
                   analytical_weight, creative_weight, social_weight, technical_weight
            FROM majors
        ''')
        majors = cursor.fetchall()
        
        # Calculate match scores
        recommendations = []
        for major in majors:
            # Calculate skill match scores
            analytical_match = 1 - abs(scores['analytical_score']/10 - major['analytical_weight'])
            creative_match = 1 - abs(scores['creative_score']/10 - major['creative_weight'])
            social_match = 1 - abs(scores['social_score']/10 - major['social_weight'])
            technical_match = 1 - abs(scores['technical_score']/10 - major['technical_weight'])
            
            # Calculate overall match score (weighted average)
            match_score = (analytical_match + creative_match + social_match + technical_match) / 4
            
            recommendations.append({
                'major': major,
                'match_score': round(match_score * 100, 1),
                'analytical_match': round(analytical_match * 100, 1),
                'creative_match': round(creative_match * 100, 1),
                'social_match': round(social_match * 100, 1),
                'technical_match': round(technical_match * 100, 1)
            })
        
        # Sort recommendations by match score
        recommendations.sort(key=lambda x: x['match_score'], reverse=True)
        
        return render_template('recommendations.html',
                             personality_type=personality_type,
                             recommendations=recommendations[:5])  # Top 5 recommendations
    except Exception as e:
        logger.error(f"Error in recommendations: {str(e)}")
        return render_template('recommendations.html',
                             error=str(e))

@app.errorhandler(Exception)
def handle_error(error):
    """Global error handler"""
    code = 500
    if isinstance(error, HTTPException):
        code = error.code
    
    logger.error(f"Error occurred: {str(error)}")
    return jsonify(error=str(error)), code

@app.route('/api/majors', methods=['GET'])
def get_majors():
    """
    Get all majors
    ---
    responses:
      200:
        description: List of all majors
      500:
        description: Server error
    """
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT id, name, description, career_opportunities, 
                   required_skills, analytical_weight, creative_weight,
                   social_weight, technical_weight
            FROM majors
        ''')
        majors = [dict(row) for row in cursor.fetchall()]
        return jsonify(majors)
    except Exception as e:
        logger.error(f"Error fetching majors: {str(e)}")
        raise

@app.route('/api/personality-types', methods=['GET'])
def get_personality_types():
    """
    Get all personality types
    ---
    responses:
      200:
        description: List of all personality types
      500:
        description: Server error
    """
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM personality_types')
        types = [dict(row) for row in cursor.fetchall()]
        return jsonify(types)
    except Exception as e:
        logger.error(f"Error fetching personality types: {str(e)}")
        raise

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
