import json

def create_admin(client):
    """Créer un utilisateur admin et retourner le token"""
    res = client.post("/api/register", json={
        "matricule": "ADMIN_LIT",
        "nom": "Admin",
        "prenom": "Lit",
        "email": "admin_lit@example.com",
        "password": "123456",
        "role": "ADMIN"
    })
    return res.get_json()["access_token"]

def create_chambre(client, token):
    """Créer une chambre pour les tests"""
    # Créer daara -> batiment -> chambre
    daara_res = client.post("/api/create", json={
        "nom": "Daara Test Lit",
        "lieu": "Dakar"
    }, headers={"Authorization": f"Bearer {token}"})
    daara_id = daara_res.get_json()["daara"]["id"]
    
    bat_res = client.post("/api/batiments", json={
        "nom": "Batiment Test Lit",
        "nb_chambres": 0,
        "daara_id": daara_id
    }, headers={"Authorization": f"Bearer {token}"})
    batiment_id = bat_res.get_json()["batiment"]["id"]
    
    chambre_res = client.post("/api/chambres", json={
        "numero": "401",
        "nb_lits": 0,
        "batiment_id": batiment_id
    }, headers={"Authorization": f"Bearer {token}"})
    return chambre_res.get_json()["chambre"]["id"]

def test_create_lit_as_admin(client):
    """Test création d'un lit par un admin"""
    token = create_admin(client)
    chambre_id = create_chambre(client, token)
    
    res = client.post("/api/lits", json={
        "numero": "1",
        "chambre_id": chambre_id
    }, headers={"Authorization": f"Bearer {token}"})
    
    assert res.status_code == 201
    data = res.get_json()
    assert data["lit"]["numero"] == "1"
    assert data["lit"]["chambre_id"] == chambre_id

def test_create_lit_denied_for_non_admin(client):
    """Test que les non-admins ne peuvent pas créer de lits"""
    # Créer un non-admin
    res = client.post("/api/register", json={
        "matricule": "USER_LIT",
        "nom": "User",
        "prenom": "Lit",
        "email": "user_lit@example.com",
        "password": "123456",
        "role": "TALIBE"
    })
    token = res.get_json()["access_token"]
    
    res = client.post("/api/lits", json={
        "numero": "2",
        "chambre_id": 1
    }, headers={"Authorization": f"Bearer {token}"})
    
    assert res.status_code == 403

def test_get_lits(client):
    """Test récupération de la liste des lits"""
    token = create_admin(client)
    
    res = client.get("/api/lits", headers={"Authorization": f"Bearer {token}"})
    
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)

def test_get_lits_by_chambre(client):
    """Test récupération des lits d'une chambre"""
    token = create_admin(client)
    chambre_id = create_chambre(client, token)
    
    # Créer des lits
    client.post("/api/lits", json={
        "numero": "A1",
        "chambre_id": chambre_id
    }, headers={"Authorization": f"Bearer {token}"})
    
    client.post("/api/lits", json={
        "numero": "A2", 
        "chambre_id": chambre_id
    }, headers={"Authorization": f"Bearer {token}"})
    
    # Récupérer les lits de la chambre
    res = client.get(f"/api/lits/chambre/{chambre_id}", headers={"Authorization": f"Bearer {token}"})
    
    assert res.status_code == 200
    lits = res.get_json()
    assert len(lits) == 2
    assert any(lit["numero"] == "A1" for lit in lits)
    assert any(lit["numero"] == "A2" for lit in lits)

def test_statistiques_lits(client):
    """Test des statistiques des lits"""
    token = create_admin(client)
    chambre_id = create_chambre(client, token)
    
    # Créer quelques lits
    client.post("/api/lits", json={
        "numero": "S1",
        "chambre_id": chambre_id
    }, headers={"Authorization": f"Bearer {token}"})
    
    # Récupérer les statistiques
    res = client.get("/api/lits/statistiques", headers={"Authorization": f"Bearer {token}"})
    
    assert res.status_code == 200
    stats = res.get_json()
    assert "total_lits" in stats
    assert "lits_occupes" in stats
    assert "lits_disponibles" in stats
    assert "taux_occupation_lits" in stats