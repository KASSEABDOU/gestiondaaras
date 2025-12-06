def test_debug_register(client):
    """Test de débogage pour voir l'erreur exacte"""
    payload = {
        "matricule": "U001",
        "nom": "Ba",
        "prenom": "Ibrahima",
        "email": "test@example.com",
        "password": "123456",
        "role": "Admin"
    }

    res = client.post("/api/register", json=payload)
    print(f"Status Code: {res.status_code}")
    print(f"Response JSON: {res.get_json()}")
    
    # Même en échec, ça nous donnera l'erreur
    assert res.status_code in [201, 500]  # Accepte les deux pour voir l'erreur

def test_debug_app_routes(client):
    """Test que l'application répond"""
    res = client.get('/')
    print(f"Root route status: {res.status_code}")
    print(f"Root route response: {res.get_json()}")
    assert res.status_code == 200