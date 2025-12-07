import os
from datetime import timedelta
from urllib.parse import quote_plus
import cloudinary

class Config:
    # Secret key
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # Database (Render PostgreSQL)
    DATABASE_URL = os.environ.get('DATABASE_URL')

    if DATABASE_URL:
        # Correction Render : ajouter le driver psycopg2 + SSL si absent
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://")
        if "sslmode" not in DATABASE_URL:
            DATABASE_URL += "?sslmode=require"

        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        SQLALCHEMY_DATABASE_URI = "sqlite:///daaras.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = 'test-secret-key'
    SECRET_KEY = 'test-secret-key'
    
    
cloudinary.config(
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key = os.environ.get("CLOUDINARY_API_KEY"),
    api_secret = os.environ.get("CLOUDINARY_API_SECRET"),
    secure = True
)
