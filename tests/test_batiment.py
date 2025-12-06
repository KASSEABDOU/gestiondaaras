import json

def create_admin(client):
    """Créer un utilisateur admin et retourner le token"""
    res = client.post("/api/register", json={
        "matricule": "ADMIN_BAT",
        "nom": "Admin",
        "prenom": "Batiment",
        "email": "admin_bat@example.com",
        "password": "123456",
        "role": "ADMIN"
    })
    return res.get_json()["access_token"]

def create_daara(client, token):
    """Créer un daara pour les tests"""
    res = client.post("/api/create", json={
        "nom": "Daara Test Batiment",
        "lieu": "Dakar",
        "proprietaire": "Proprio Test"
    }, headers={"Authorization": f"Bearer {token}"})
    return res.get_json()["daara"]["id"]

def test_create_batiment_as_admin(client):
    """Test création d'un batiment par un admin"""
    token = create_admin(client)
    daara_id = create_daara(client, token)
    
    res = client.post("/api/batiments", json={
        "nom": "Batiment A",
        "nb_chambres": 5,
        "daara_id": daara_id
    }, headers={"Authorization": f"Bearer {token}"})
    
    assert res.status_code == 201
    data = res.get_json()
    assert data["batiment"]["nom"] == "Batiment A"
    assert data["batiment"]["nb_chambres"] == 5
    assert data["batiment"]["daara_id"] == daara_id

def test_create_batiment_denied_for_non_admin(client):
    """Test que les non-admins ne peuvent pas créer de batiments"""
    # Créer un non-admin
    res = client.post("/api/register", json={
        "matricule": "USER_BAT",
        "nom": "User",
        "prenom": "Batiment",
        "email": "user_bat@example.com",
        "password": "123456",
        "role": "TALIBE"
    })
    token = res.get_json()["access_token"]
    
    res = client.post("/api/batiments", json={
        "nom": "Batiment B",
        "nb_chambres": 3,
        "daara_id": 1
    }, headers={"Authorization": f"Bearer {token}"})
    
    assert res.status_code == 403

def test_get_batiments(client):
    """Test récupération de la liste des batiments"""
    token = create_admin(client)
    
    res = client.get("/api/batiments", headers={"Authorization": f"Bearer {token}"})
    
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)

def test_get_batiment_by_id(client):
    """Test récupération d'un batiment spécifique"""
    token = create_admin(client)
    daara_id = create_daara(client, token)
    
    # Créer un batiment
    create_res = client.post("/api/batiments", json={
        "nom": "Batiment Test",
        "nb_chambres": 4,
        "daara_id": daara_id
    }, headers={"Authorization": f"Bearer {token}"})
    batiment_id = create_res.get_json()["batiment"]["id"]
    
    # Récupérer le batiment
    res = client.get(f"/api/batiments/{batiment_id}", headers={"Authorization": f"Bearer {token}"})
    
    assert res.status_code == 200
    data = res.get_json()
    assert data["nom"] == "Batiment Test"

def test_update_batiment(client):
    """Test mise à jour d'un batiment"""
    token = create_admin(client)
    daara_id = create_daara(client, token)
    
    # Créer un batiment
    create_res = client.post("/api/batiments", json={
        "nom": "Batiment Original",
        "nb_chambres": 3,
        "daara_id": daara_id
    }, headers={"Authorization": f"Bearer {token}"})
    batiment_id = create_res.get_json()["batiment"]["id"]
    
    # Mettre à jour
    res = client.put(f"/api/batiments/{batiment_id}", json={
        "nom": "Batiment Modifié",
        "nb_chambres": 6
    }, headers={"Authorization": f"Bearer {token}"})
    
    assert res.status_code == 200
    data = res.get_json()
    assert data["batiment"]["nom"] == "Batiment Modifié"
    assert data["batiment"]["nb_chambres"] == 6

def test_delete_batiment(client):
    """Test suppression d'un batiment"""
    token = create_admin(client)
    daara_id = create_daara(client, token)
    
    # Créer un batiment
    create_res = client.post("/api/batiments", json={
        "nom": "Batiment à Supprimer",
        "nb_chambres": 2,
        "daara_id": daara_id
    }, headers={"Authorization": f"Bearer {token}"})
    batiment_id = create_res.get_json()["batiment"]["id"]
    
    # Supprimer
    res = client.delete(f"/api/batiments/{batiment_id}", headers={"Authorization": f"Bearer {token}"})
    
    assert res.status_code == 200
    
    # Vérifier qu'il n'existe plus - cette partie peut causer des problèmes
    # Essayons plutôt de vérifier que la liste ne contient plus ce batiment
    get_res = client.get("/api/batiments", headers={"Authorization": f"Bearer {token}"})
    batiments = get_res.get_json()
    batiment_ids = [b["id"] for b in batiments]
    assert batiment_id not in batiment_ids