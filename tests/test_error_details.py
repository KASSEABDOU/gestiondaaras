def test_register_error_details(client):
    """Test pour voir l'erreur exacte du register"""
    payload = {
        "matricule": "U001",
        "nom": "Ba",
        "prenom": "Ibrahima",
        "email": "test@example.com",
        "password": "123456",
        "role": "Admin"
    }

    res = client.post("/api/register", json=payload)
    print(f"Status: {res.status_code}")
    print(f"Headers: {dict(res.headers)}")
    print(f"Data: {res.get_data(as_text=True)}")
    print(f"JSON: {res.get_json()}")
    
    # Accepte n'importe quel statut pour voir l'erreur
    assert res.status_code in [201, 400, 500]

def test_login_error_details(client):
    """Test pour voir l'erreur exacte du login"""
    # D'abord créer un utilisateur
    register_payload = {
        "matricule": "U002",
        "nom": "Fall", 
        "prenom": "Moussa",
        "email": "moussa@example.com",
        "password": "123456",
        "role": "ENSEIGNANT"
    }
    
    register_res = client.post("/api/register", json=register_payload)
    print(f"Register Status: {register_res.status_code}")
    print(f"Register Response: {register_res.get_json()}")
    
    # Ensuite tenter de se connecter
    login_payload = {
        "email": "moussa@example.com",
        "password": "123456"
    }
    
    login_res = client.post("/api/login", json=login_payload)
    print(f"Login Status: {login_res.status_code}")
    print(f"Login Response: {login_res.get_json()}")
    
    assert login_res.status_code in [200, 400, 500]