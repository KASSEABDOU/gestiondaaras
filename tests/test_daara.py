import json

def create_admin(client):
    res = client.post("/api/register", json={
        "matricule": "A100",
        "nom": "Admin",
        "prenom": "Test",
        "email": "admin@example.com",
        "password": "123456",
        "role": "ADMIN"
    })
    return res.get_json()["access_token"]


def test_create_daara_as_admin(client):
    token = create_admin(client)

    res = client.post("/api/create", json={
        "nom": "Daara Nass",
        "lieu": "Dakar"
    }, headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 201
    assert res.get_json()["daara"]["nom"] == "Daara Nass"


def test_create_daara_denied_for_non_admin(client):
    # Create non-admin
    res = client.post("/api/register", json={
        "matricule": "U004",
        "nom": "User",
        "prenom": "Test",
        "email": "user@example.com",
        "password": "123456",
        "role": "TALIBE"
    })
    token = res.get_json()["access_token"]

    # Try to create daara
    res = client.post("/api/create", json={
        "nom": "Daara X",
        "lieu": "Thiès"
    }, headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 403
    assert res.get_json()["error"] in ["Accès non autorisé", "Accès refusé"]
