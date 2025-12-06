# backend/tests/test_talibe.py
import pytest
import json
from datetime import date
from backend.models import Utilisateur, db, RoleEnum

def create_test_admin(client):
    """Créer un admin directement dans la base de test et obtenir un token"""
    
    # Nettoyer d'abord les utilisateurs existants
    Utilisateur.query.filter_by(email="admin_test@example.com").delete()
    db.session.commit()
    
    # Créer un admin directement avec toutes les données requises
    admin = Utilisateur(
        matricule="ADMIN_TEST",
        nom="Admin",
        prenom="Test",
        email="admin_test@example.com",
        role=RoleEnum.ADMIN.value,
        date_naissance=date(1990, 1, 1),  # Date obligatoire
        lieu_naissance="Dakar",
        date_entree=date.today(),  # Date obligatoire
        age=35,
        nb_annees=5
    )
    admin.set_password("123456")
    
    db.session.add(admin)
    db.session.commit()
    
    # Maintenant se connecter pour obtenir le token
    login_data = {
        "email": "admin_test@example.com",
        "password": "123456"
    }
    
    res = client.post("/api/login", json=login_data)
    data = res.get_json()
    print(f"Login Response: {data}")
    
    if 'access_token' in data:
        return data['access_token']
    else:
        raise Exception(f"Échec de la connexion: {data}")

def test_create_talibe_simple(client):
    """Test création basique d'un talibé"""
    try:
        token = create_test_admin(client)
        print(f"Token obtenu: {token[:50]}...")
        
        talibe_data = {
            "matricule": "TAL001",
            "nom": "Diallo",
            "prenom": "Moussa",
            "email": "moussa@example.com",
            "password": "123456",
            "date_naissance": "2005-05-15",  # Date obligatoire
            "lieu_naissance": "Dakar",
            "date_entree": "2024-01-01",  # Date obligatoire
            "age": 19,
            "nb_annees": 1,
            "niveau": "Débutant"
        }

        res = client.post("/api/talibes", 
                         json=talibe_data,
                         headers={"Authorization": f"Bearer {token}"})

        print(f"Création talibé - Status: {res.status_code}")
        print(f"Création talibé - Response: {res.get_json()}")

        # Vérifier le succès ou afficher l'erreur
        if res.status_code != 201:
            error_data = res.get_json()
            print(f"ERREUR: {error_data}")
        
        assert res.status_code == 201
        data = res.get_json()
        assert "message" in data
        
    except Exception as e:
        print(f"Erreur durant le test: {str(e)}")
        raise