# test_upload_with_auth.py
import requests
import os
import json

# Configuration
BASE_URL = 'http://localhost:5000/api'
TEST_EMAIL = "admin@daara.com"  # Remplacez par un email valide
TEST_PASSWORD = "admin123"      # Remplacez par le mot de passe

def login():
    """Se connecter et obtenir un token JWT"""
    url = f'{BASE_URL}/login'
    
    login_data = {
        'email': TEST_EMAIL,
        'password': TEST_PASSWORD
    }
    
    print("🔐 Connexion...")
    
    try:
        response = requests.post(url, json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            if token:
                print("✅ Connexion réussie!")
                return token
            else:
                print("❌ Token non reçu dans la réponse")
                return None
        else:
            print(f"❌ Échec de la connexion: {response.status_code}")
            print("Réponse:", response.text)
            return None
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return None

def create_test_image():
    """Crée un fichier image JPEG minimal pour les tests"""
    jpeg_data = bytes([
        0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
        0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
        0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
        0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
        0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
        0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
        0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
        0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01, 0x00,
        0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x14, 0x00, 0x01, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x03, 0xFF, 0xC4, 0x00, 0x14, 0x10, 0x01, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00, 0xBF,
        0xFF, 0xD9
    ])
    
    with open('test_image.jpg', 'wb') as f:
        f.write(jpeg_data)
    print("✅ Fichier test_image.jpg créé")

def test_upload(token):
    """Test l'upload avec authentification"""
    url = f'{BASE_URL}/upload/photo'
    
    print("📤 Test d'upload avec authentification...")
    
    # Créer le fichier test s'il n'existe pas
    if not os.path.exists('test_image.jpg'):
        create_test_image()
    
    try:
        with open('test_image.jpg', 'rb') as f:
            files = {'photo': ('test_image.jpg', f, 'image/jpeg')}
            
            # Headers avec le token JWT
            headers = {
                'Authorization': f'Bearer {token}'
            }
            
            response = requests.post(url, files=files, headers=headers)
            
        print("📊 Statut HTTP:", response.status_code)
        
        if response.status_code == 200:
            print("✅ SUCCÈS - Upload réussi!")
            result = response.json()
            print("📄 Réponse:", json.dumps(result, indent=2))
            return result
        else:
            print("❌ ÉCHEC - Erreur HTTP:", response.status_code)
            print("📄 Réponse d'erreur:", response.text)
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur. Vérifiez que Flask est démarré.")
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
    
    return None

def test_download(filename, token):
    """Test le téléchargement d'un fichier uploadé"""
    print(f"\n📥 Test de téléchargement pour {filename}...")
    
    url = f'{BASE_URL}/uploads/{filename}'
    
    try:
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        response = requests.get(url, headers=headers)
        print("📊 Statut téléchargement:", response.status_code)
        
        if response.status_code == 200:
            print("✅ Téléchargement réussi!")
            print("📏 Taille du fichier:", len(response.content), "bytes")
            return True
        else:
            print("❌ Échec du téléchargement")
            print("Réponse:", response.text)
            return False
            
    except Exception as e:
        print(f"❌ Erreur téléchargement: {e}")
        return False

def main():
    print("🚀 Démarrage des tests d'upload avec authentification...")
    
    # Étape 1: Obtenir un token
    token = login()
    if not token:
        print("❌ Impossible de continuer sans token JWT")
        return
    
    print(f"🔑 Token JWT obtenu: {token[:20]}...")
    
    # Étape 2: Tester l'upload
    upload_result = test_upload(token)
    
    # Étape 3: Tester le téléchargement si l'upload a réussi
    if upload_result and 'filename' in upload_result:
        test_download(upload_result['filename'], token)

if __name__ == '__main__':
    main()