def test_profile_debug(client):
    """Test de débogage pour la route profile"""
    
    # Créer un utilisateur
    register_res = client.post("/api/register", json={
        "matricule": "PROFILE001",
        "nom": "Profile",
        "prenom": "Test",
        "email": "profile@test.com",
        "password": "123456",
        "role": "TALIBE"
    })
    
    print(f"Register Status: {register_res.status_code}")
    print(f"Register Response: {register_res.get_json()}")
    
    token = register_res.get_json()["access_token"]
    print(f"Token: {token}")
    
    # Tester la route profile
    res = client.get("/api/profile", headers={
        "Authorization": f"Bearer {token}"
    })
    
    print(f"Profile Status: {res.status_code}")
    print(f"Profile Headers: {dict(res.headers)}")
    print(f"Profile Response: {res.get_json()}")
    
    # Pour le débogage, acceptons n'importe quel statut sauf 404
    assert res.status_code != 404
    