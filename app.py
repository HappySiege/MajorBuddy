from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from pathlib import Path
import sqlite3
import json
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import random

app = Flask(__name__)
app.config['DATABASE'] = 'majorbuddy.db'
app.secret_key = 'your-secret-key'  # Add a secret key for session management

def get_db():
    db = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    return db

def init_db():
    if not Path(app.config['DATABASE']).exists():
        with app.app_context():
            db = get_db()
            with app.open_resource('schema.sql', mode='r') as f:
                db.cursor().executescript(f.read())
            db.commit()

def get_personality_type(scores):
    # Simple personality type determination based on scores
    personality_types = {
        'INTJ': {
            'name': 'Architect',
            'description': 'Imaginative and strategic thinkers with a plan for everything',
            'recommended_majors': [
                {'name': 'Computer Science', 'match': 0.95},
                {'name': 'Systems Engineering', 'match': 0.90},
                {'name': 'Physics', 'match': 0.85}
            ]
        },
        'INTP': {
            'name': 'Logician',
            'description': 'Innovative inventors with an unquenchable thirst for knowledge',
            'recommended_majors': [
                {'name': 'Mathematics', 'match': 0.95},
                {'name': 'Software Engineering', 'match': 0.90},
                {'name': 'Philosophy', 'match': 0.85}
            ]
        },
        'ENTJ': {
            'name': 'Commander',
            'description': 'Bold, imaginative and strong-willed leaders',
            'recommended_majors': [
                {'name': 'Business Administration', 'match': 0.95},
                {'name': 'Economics', 'match': 0.90},
                {'name': 'Political Science', 'match': 0.85}
            ]
        },
        'ISTJ': {
            'name': 'Logistician',
            'description': 'Practical and fact-minded individuals',
            'recommended_majors': [
                {'name': 'Accounting', 'match': 0.95},
                {'name': 'Civil Engineering', 'match': 0.90},
                {'name': 'Information Systems', 'match': 0.85}
            ]
        }
    }

    # Determine primary type based on scores
    if scores['analytical_score'] > 7 and scores['technical_score'] > 7:
        primary_type = 'INTJ'
    elif scores['analytical_score'] > 7 and scores['creative_score'] > 7:
        primary_type = 'INTP'
    elif scores['analytical_score'] > 7 and scores['social_score'] > 7:
        primary_type = 'ENTJ'
    else:
        primary_type = 'ISTJ'

    # Get similar types
    similar_types = []
    for code, type_info in personality_types.items():
        if code != primary_type:
            similarity = 0.7 + (random.random() * 0.2)  # Random similarity between 70-90%
            similar_type = {
                'code': code,
                'name': type_info['name'],
                'description': type_info['description'],
                'similarity': similarity,
                'recommended_majors': type_info['recommended_majors']
            }
            similar_types.append(similar_type)
    
    # Sort by similarity and take top 2
    similar_types.sort(key=lambda x: x['similarity'], reverse=True)
    similar_types = similar_types[:2]

    return {
        'code': primary_type,
        'name': personality_types[primary_type]['name'],
        'description': personality_types[primary_type]['description'],
        'recommended_majors': personality_types[primary_type]['recommended_majors']
    }, similar_types

def get_personality_type_id(type_code):
    """Get or create a personality type record."""
    db = get_db()
    personality_type = db.execute(
        'SELECT id FROM personality_types WHERE code = ?',
        (type_code,)
    ).fetchone()
    
    if not personality_type:
        # Insert basic personality type if it doesn't exist
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO personality_types (code, name) VALUES (?, ?)',
            (type_code, type_code)  # Using code as name temporarily
        )
        db.commit()
        return cursor.lastrowid
    
    return personality_type['id']

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
    data = request.get_json()
    
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
        json.dumps(data['responses'])
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

@app.route('/recommendations')
def recommendations():
    try:
        scores = session.get('scores')
        if not scores:
            return redirect(url_for('questionnaire'))

        # Get personality types
        primary_type, similar_types = get_personality_type(scores)

        # Get all majors from the database
        cursor = get_db().cursor()
        cursor.execute('SELECT * FROM majors')
        majors = cursor.fetchall()

        # Calculate match scores for each major
        recommended_majors = []
        for major in majors:
            analytical_match = 1 - abs(major['analytical_requirement'] - scores['analytical_score']) / 10
            creative_match = 1 - abs(major['creative_requirement'] - scores['creative_score']) / 10
            social_match = 1 - abs(major['social_requirement'] - scores['social_score']) / 10
            technical_match = 1 - abs(major['technical_requirement'] - scores['technical_score']) / 10
            
            skills_match = (analytical_match + creative_match + social_match + technical_match) / 4
            personality_match = 0.8 + (random.random() * 0.2)  # Random match between 80-100%

            match_score = (skills_match * 0.7) + (personality_match * 0.3)  # Weight skills more than personality

            recommended_majors.append({
                'name': major['name'],
                'description': major['description'],
                'career_opportunities': major['career_opportunities'],
                'required_skills': major['required_skills'],
                'analytical_match': analytical_match,
                'creative_match': creative_match,
                'social_match': social_match,
                'technical_match': technical_match,
                'personality_match': personality_match,
                'match_score': match_score
            })

        # Sort majors by match score
        recommended_majors.sort(key=lambda x: x['match_score'], reverse=True)

        return render_template('recommendations.html',
                            scores=scores,
                            primary_type=primary_type,
                            similar_types=similar_types,
                            recommended_majors=recommended_majors[:5])
    except Exception as e:
        return render_template('recommendations.html', error=str(e))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
