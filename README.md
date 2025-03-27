# RecruitmentBuddy - Degree Program Recommender

A web-based application that helps students find suitable degree programs based on their personality traits and academic interests.

## Features

- Interactive questionnaire with Likert scale questions
- Real-time progress tracking
- Personalized major recommendations
- Mobile-responsive design

## Tech Stack

- Backend: Python/Flask
- Database: SQLite
- Frontend: HTML, CSS, JavaScript

## Project Structure

```
RecruitmentBuddy/
├── app.py              # Main Flask application
├── schema.sql          # Database schema
├── populate_db.py      # Sample data population script
├── requirements.txt    # Python dependencies
├── static/
│   ├── css/
│   │   ├── style.css
│   │   ├── questionnaire.css
│   │   └── recommendations.css
│   └── js/
│       └── questionnaire.js
└── templates/
    ├── index.html
    ├── questionnaire.html
    └── recommendations.html
```

## Setup Instructions

1. Clone the repository:
```bash
git clone [repository-url]
cd RecruitmentBuddy
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python populate_db.py
```

5. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## For Frontend Developers

- All frontend code is in the `/static` and `/templates` directories
- The questionnaire uses a single-page-per-question design with custom radio buttons
- CSS is modular with separate files for different components
- JavaScript handles form validation and navigation

## For AI Integration

- The application is designed to support AI-based recommendations
- Current matching uses a weighted scoring system
- Integration points for AI model:
  1. `app.py`: Look for the `calculate_major_matches` function
  2. Database schema includes weights for different dimensions
  3. Questionnaire responses are normalized for consistent scoring

## Database Schema

The SQLite database (`majorbuddy.db`) includes tables for:
- Majors and their dimension weights
- Questionnaire responses
- Major recommendations

See `schema.sql` for detailed structure.

## Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Submit a pull request

## Future Enhancements

- AI model integration for more sophisticated recommendations
- Additional personality dimensions
- User accounts and saved recommendations
- Detailed major information and career paths
