from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt, unset_jwt_cookies
from flask_jwt_extended import verify_jwt_in_request
from flask_jwt_extended.exceptions import JWTExtendedException
import sys
import os
import traceback

# Ajouter le chemin pour les imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models import db, Utilisateur, Talibe, Enseignant, RoleEnum
from decorators import role_required  # Maintenant ça devrait fonctionner
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        print("=== DÉBUT REGISTER ===")
        print(f"Données: {data}")
        
        # Validation basique
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        required = ['matricule', 'nom', 'prenom', 'email', 'password', 'role']
        for field in required:
            if not data.get(field):
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        # Gérer l'héritage correctement
        user = None
        if data['role'] == 'Talibé':
            user = Talibe()
            user.pere = data.get('pere', '')
            user.mere = data.get('mere', '')
            user.niveau = data.get('niveau', 'Débutant')
            user.extrait_naissance = data.get('extrait_naissance', False)
        elif data['role'] == 'Enseignant':
            user = Enseignant()
            user.specialite = data.get('specialite', 'Général')
            user.telephone = data.get('telephone', '')
            user.etat_civil = data.get('etat_civil', 'CELIBATAIRE')
            user.grade = data.get('grade', 'Débutant')
        else:
            user = Utilisateur()
        
        # Champs communs
        user.matricule = data['matricule']
        user.nom = data['nom']
        user.prenom = data['prenom']
        user.email = data['email']
        user.set_password(data['password'])
        user.role = RoleEnum(data['role'])
        user.date_naissance = datetime.now().date()
        user.lieu_naissance = data.get('lieu_naissance', 'Dakar')
        user.age = data.get('age', 25)
        user.adresse = data.get('adresse', '')
        user.date_entree = datetime.now().date()
        user.nb_annees = data.get('nb_annees', 1)
        
        print(f"Utilisateur créé: {user.__class__.__name__}")
        
        db.session.add(user)
        db.session.commit()
        
        print(f"Utilisateur sauvegardé avec ID: {user.id}")
        
        # CORRECTION : Utiliser l'email comme identity (doit être une string)
        token = create_access_token(identity=user.email)
        
        response = {
            'message': 'Success',
            'access_token': token,
            'user': user.to_dict()
        }
        
        print(f"Réponse: {response}")
        print("=== FIN REGISTER ===")
        
        return jsonify(response), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"ERREUR: {str(e)}")
        print(f"TRACEBACK: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        print("=== DÉBUT LOGIN ===")
        print(f"Données: {data}")
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
        
        user = Utilisateur.query.filter_by(email=data['email']).first()
        print(f"Utilisateur trouvé: {user}")
        
        if user and user.check_password(data['password']):
            # CORRECTION : Utiliser l'email comme identity (doit être une string)
            token = create_access_token(identity=user.email)
            response = {'access_token': token, 'user': user.to_dict()}
            print(f"Réponse succès: {response}")
            print("=== FIN LOGIN ===")
            return jsonify(response), 200
        else:
            print("Échec authentification")
            print("=== FIN LOGIN ===")
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        print(f"ERREUR LOGIN: {str(e)}")
        print(f"TRACEBACK: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        print("=== DÉBUT PROFILE ===")
        
        # Récupérer l'email depuis le token JWT
        user_email = get_jwt_identity()
        print(f"Email du token JWT: {user_email}")
        
        # Trouver l'utilisateur par email
        user = Utilisateur.query.filter_by(email=user_email).first()
        print(f"Utilisateur trouvé en DB: {user}")
        
        if not user:
            print("Utilisateur non trouvé en base de données")
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
            
        print(f"Profil retourné: {user.to_dict()}")
        print("=== FIN PROFILE ===")
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        print(f"ERREUR PROFILE: {str(e)}")
        import traceback
        print(f"TRACEBACK: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500
    
    

@auth_bp.route('/logout', methods=['POST'])
def logout_expired_friendly():
    """
    Déconnexion qui gère proprement les tokens expirés
    """
    try:
        print("🔄 Traitement déconnexion")
        
        # Variables pour les infos du token
        user_email = None
        token_status = "unknown"
        
        # Essayer de vérifier le token (même expiré)
        try:
            verify_jwt_in_request(optional=True)
            user_email = get_jwt_identity()
            
            if user_email:
                token_status = "valid"
                print(f"✅ Token valide pour: {user_email}")
            else:
                token_status = "invalid_or_missing"
                print("ℹ️ Pas de token valide")
                
        except Exception as jwt_error:
            token_status = "expired_or_invalid"
            print(f"⚠️ Token expiré/invalide: {str(jwt_error)}")
        
        # Réponse adaptée
        if user_email:
            response_data = {
                'success': True,
                'message': 'Déconnexion réussie',
                'user': user_email,
                'token_status': token_status
            }
        else:
            response_data = {
                'success': True,
                'message': 'Session fermée',
                'user': None,
                'token_status': token_status,
                'note': 'Le token était expiré ou manquant'
            }
        
        response = jsonify(response_data)
        
        # Nettoyer les cookies
        try:
            unset_jwt_cookies(response)
        except:
            # Fallback si unset_jwt_cookies échoue
            response.set_cookie('access_token_cookie', '', expires=0)
            response.set_cookie('refresh_token_cookie', '', expires=0)
        
        print(f"📤 Réponse: {response_data}")
        return response, 200
        
    except Exception as e:
        print(f"🔥 Erreur critique: {str(e)}")
        # Réponse minimaliste en cas d'erreur critique
        return jsonify({
            'success': True,
            'message': 'Déconnexion prise en compte'
        }), 200