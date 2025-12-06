def test_all_auth_routes(client):
    """Test que toutes les routes d'authentification fonctionnent"""
    
    # Test register
    register_res = client.post("/api/register", json={
        "matricule": "TEST001",
        "nom": "Test",
        "prenom": "User", 
        "email": "test@test.com",
        "password": "123456",
        "role": "ADMIN"
    })
    assert register_res.status_code == 201
    assert 'access_token' in register_res.get_json()
    
    # Test login
    login_res = client.post("/api/login", json={
        "email": "test@test.com",
        "password": "123456"
    })
    assert login_res.status_code == 200
    assert 'access_token' in login_res.get_json()

def test_daara_routes_exist(client):
    """Test que les routes daara existent"""
    # S'assurer d'avoir un token admin d'abord
    register_res = client.post("/api/register", json={
        "matricule": "ADMIN001",
        "nom": "Admin",
        "prenom": "Daara",
        "email": "admin@daara.com",
        "password": "123456",
        "role": "ADMIN"
    })
    token = register_res.get_json()['access_token']
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Test GET /daaras
    res = client.get("/api/daaras", headers=headers)
    # Devrait être 200 (liste vide) ou 500 (erreur), mais pas 404
    assert res.status_code != 404
    
    # Test POST /daaras
    res = client.post("/api/daaras", 
                     json={"nom": "Test Daara", "lieu": "Dakar"},
                     headers=headers)
    # Devrait être 201 (créé) ou avoir une erreur autre que 404
    assert res.status_code != 404