import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'election-portal-demo-key-2026-cse-prototype-secret')
    
    # Handle Render PostgreSQL or default local SQLite
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = database_url
    else:
        db_path = os.path.join(BASE_DIR, "election_portal.db").replace('\\', '/')
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file upload
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
    
    # Prototype metadata
    PORTAL_NAME = "Candidate Smart Declaration & Nomination Portal"
    ORGANIZATION = "Election Commission Academic Simulation (Prototype)"
    DISCLAIMER_TEXT = "ACADEMIC DEMONSTRATION PROTOTYPE: This portal is created solely for college educational demonstration. It is NOT connected to the Election Commission of India (ECI) or any real government system. Nominations submitted here are simulations."
