-- Drop tables if they exist
DROP TABLE IF EXISTS majors;
DROP TABLE IF EXISTS major_requirements;
DROP TABLE IF EXISTS questionnaire_responses;
DROP TABLE IF EXISTS major_recommendations;

-- Create majors table
CREATE TABLE majors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    career_opportunities TEXT,
    required_skills TEXT,
    analytical_weight FLOAT,    -- Weight for analytical skills (0-1)
    creative_weight FLOAT,      -- Weight for creative skills (0-1)
    social_weight FLOAT,        -- Weight for social skills (0-1)
    technical_weight FLOAT      -- Weight for technical skills (0-1)
);

-- Create major requirements table
CREATE TABLE major_requirements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    major_id INTEGER,
    requirement_type TEXT,      -- e.g., 'course', 'skill', 'aptitude'
    requirement_name TEXT,
    requirement_description TEXT,
    FOREIGN KEY (major_id) REFERENCES majors(id)
);

-- Create table for storing questionnaire responses
CREATE TABLE questionnaire_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    analytical_score FLOAT,     -- Score for analytical dimension (1-5)
    creative_score FLOAT,       -- Score for creative dimension (1-5)
    social_score FLOAT,         -- Score for social dimension (1-5)
    technical_score FLOAT,      -- Score for technical dimension (1-5)
    raw_responses TEXT          -- JSON of all question responses
);

-- Create table for storing major recommendations
CREATE TABLE major_recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    response_id INTEGER,
    major_id INTEGER,
    match_score FLOAT,          -- Overall match score (0-1)
    analytical_match FLOAT,     -- Match score for analytical dimension (0-1)
    creative_match FLOAT,       -- Match score for creative dimension (0-1)
    social_match FLOAT,         -- Match score for social dimension (0-1)
    technical_match FLOAT,      -- Match score for technical dimension (0-1)
    recommendation_explanation TEXT,
    FOREIGN KEY (response_id) REFERENCES questionnaire_responses(id),
    FOREIGN KEY (major_id) REFERENCES majors(id)
);
