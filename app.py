from flask import Flask, render_template, request, jsonify
from pathlib import Path
import sqlite3
import json
import numpy as np
from sklearn.preprocessing import MinMaxScaler

app = Flask(__name__)
app.config['DATABASE'] = 'majorbuddy.db'

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

def calculate_major_matches(scores):
    """Calculate match scores for all majors based on questionnaire scores."""
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
        
        # Calculate overall match score (weighted average)
        match_score = (analytical_match + creative_match + social_match + technical_match) / 4
        
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
            'technical_match': technical_match
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
    
    # Store questionnaire response
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        INSERT INTO questionnaire_responses 
        (analytical_score, creative_score, social_score, technical_score, raw_responses)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        data['scores']['analytical_score'],
        data['scores']['creative_score'],
        data['scores']['social_score'],
        data['scores']['technical_score'],
        json.dumps(data['responses'])
    ))
    response_id = cursor.lastrowid
    
    # Calculate and store major recommendations
    matches = calculate_major_matches(data['scores'])
    
    for match in matches:
        cursor.execute('''
            INSERT INTO major_recommendations
            (response_id, major_id, match_score, analytical_match, 
             creative_match, social_match, technical_match)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            response_id,
            match['major_id'],
            match['match_score'],
            match['analytical_match'],
            match['creative_match'],
            match['social_match'],
            match['technical_match']
        ))
    
    db.commit()
    return jsonify({'status': 'success', 'response_id': response_id})

@app.route('/recommendations')
def recommendations():
    db = get_db()
    # Get the most recent questionnaire response
    response = db.execute('''
        SELECT * FROM questionnaire_responses 
        ORDER BY timestamp DESC LIMIT 1
    ''').fetchone()
    
    if not response:
        return render_template('recommendations.html', 
                             recommended_majors=[],
                             error="No questionnaire response found")
    
    # Get recommendations for this response
    recommended_majors = db.execute('''
        SELECT m.*, mr.match_score, mr.analytical_match,
               mr.creative_match, mr.social_match, mr.technical_match
        FROM major_recommendations mr
        JOIN majors m ON mr.major_id = m.id
        WHERE mr.response_id = ?
        ORDER BY mr.match_score DESC
    ''', (response['id'],)).fetchall()
    
    return render_template('recommendations.html',
                         recommended_majors=[dict(major) for major in recommended_majors],
                         scores={
                             'analytical': response['analytical_score'],
                             'creative': response['creative_score'],
                             'social': response['social_score'],
                             'technical': response['technical_score']
                         })

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
