import pytest
import sys
import os

# Ajouter le dossier backend au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.app import create_app
from backend.models import db

@pytest.fixture
def app():
    """Application fixture for pytest-flask"""
    app = create_app(testing=True)
    
    # Créer les tables dans le contexte de l'application
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Client fixture for testing"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Runner fixture for testing CLI commands"""
    return app.test_cli_runner()