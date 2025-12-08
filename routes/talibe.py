from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models import db, Talibe, Cours, RoleEnum, Inscription
from decorators import role_required
import traceback

# Import conditionnel pour Inscription
try:
    from backend.models import Inscription
    INSCRIPTION_AVAILABLE = True
except ImportError:
    INSCRIPTION_AVAILABLE = False
    print("Avertissement: Le modèle Inscription n'est pas disponible")

talibe_bp = Blueprint('talibe', __name__)

@talibe_bp.route('/talibes', methods=['GET'])
@jwt_required()
def get_talibes():
    try:
        talibes = Talibe.query.all()
        return jsonify([talibe.to_dict() for talibe in talibes]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@talibe_bp.route('/talibes/<int:id>', methods=['GET'])
@jwt_required()
def get_talibe(id):
    try:
        talibe = Talibe.query.get(id)
        if not talibe:
            return jsonify({'error': 'Talibé non trouvé'}), 404
        return jsonify(talibe.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
def to_int_or_none(value):
    return int(value) if str(value).isdigit() else None

@talibe_bp.route('talibes/create', methods=['POST'])
@jwt_required()
@role_required('ADMIN')
def create_talibe():
    try:
        data = request.get_json()
        print(f"Données création talibé: {data}")
        
        if not data:
            return jsonify({'error': 'Données JSON requises'}), 400
        
        required_fields = ['matricule', 'nom', 'prenom', 'email', 'password']
        for field in required_fields:
            if field not in data or not data.get(field):
                return jsonify({'error': f'Le champ {field} est requis'}), 400
        
        # Vérifier si le matricule existe déjà
        existing_talibe = Talibe.query.filter_by(matricule=data['matricule']).first()
        if existing_talibe:
            return jsonify({'error': 'Un talibé avec ce matricule existe déjà'}), 409
        
        # Vérifier si l'email existe déjà
        existing_email = Talibe.query.filter_by(email=data['email']).first()
        if existing_email:
            return jsonify({'error': 'Un talibé avec cet email existe déjà'}), 409
        
        talibe = Talibe()
        talibe.matricule = data['matricule']
        talibe.nom = data['nom']
        talibe.prenom = data['prenom']
        talibe.email = data['email']
        talibe.set_password(data['password'])
        talibe.role = RoleEnum.TALIBE
        talibe.pere = data.get('pere', '')
        talibe.mere = data.get('mere', '')
        talibe.niveau = data.get('niveau', 'Débutant')
        talibe.extrait_naissance = data.get('extrait_naissance', False)
        talibe.nationalite = data.get('nationalite')
        talibe.sexe = data.get('sexe')
        talibe.daara_id = to_int_or_none(data.get("daara_id"))
        talibe.chambre_id = to_int_or_none(data.get("chambre_id"))

        
        # CORRECTION : Ajouter photo_profil
        talibe.photo_profil = data.get('photo_profil')  # ← AJOUT IMPORTANT
        
        # Gestion des dates
        if data.get('date_naissance'):
            talibe.date_naissance = datetime.strptime(data['date_naissance'], '%Y-%m-%d').date()
        
        talibe.lieu_naissance = data.get('lieu_naissance', '')
        
        if data.get('date_entree'):
            talibe.date_entree = datetime.strptime(data['date_entree'], '%Y-%m-%d').date()
        else:
            talibe.date_entree = datetime.now().date() 
        
        print(f"📸 Photo à enregistrer: {talibe.photo_profil}")  # Debug
        
        db.session.add(talibe)
        db.session.commit()
        
        print(f"✅ Talibé créé avec ID: {talibe.id}, Photo: {talibe.photo_profil}")
        
        return jsonify({
            'message': 'Talibé créé avec succès',
            'talibe': talibe.to_dict()
        }), 201
        
    except Exception as e:
        traceback.print_exc()
        db.session.rollback()
        print(f"Erreur création talibé: {str(e)}")
        return jsonify({'error': f'Erreur lors de la création: {str(e)}'}), 500

@talibe_bp.route('/talibes/<int:talibe_id>/cours', methods=['POST'])
@jwt_required()
@role_required('ADMIN')
def affecter_cours_talibe(talibe_id):
    """Affecter des cours à un talibé"""
    try:
        if not INSCRIPTION_AVAILABLE:
            return jsonify({'error': 'Système d\'inscription non disponible'}), 501
        
        data = request.get_json()
        print(f"Données affectation cours: {data}")
        
        if not data or 'cours_ids' not in data:
            return jsonify({'error': 'La liste des cours_ids est requise'}), 400
        
        talibe = Talibe.query.get(talibe_id)
        if not talibe:
            return jsonify({'error': 'Talibé non trouvé'}), 404
        
        cours_ids = data['cours_ids']
        if not isinstance(cours_ids, list):
            return jsonify({'error': 'cours_ids doit être une liste'}), 400
        
        # Vérifier que tous les cours existent
        cours_list = Cours.query.filter(Cours.id.in_(cours_ids)).all()
        if len(cours_list) != len(cours_ids):
            return jsonify({'error': 'Un ou plusieurs cours non trouvés'}), 404
        
        # Créer les inscriptions
        inscriptions = []
        for cours_id in cours_ids:
            # Vérifier si l'inscription existe déjà
            inscription_existante = Inscription.query.filter_by(
                talibe_id=talibe_id, 
                cours_id=cours_id
            ).first()
            
            if not inscription_existante:
                inscription = Inscription(
                    talibe_id=talibe_id,
                    cours_id=cours_id,
                    date_inscription=datetime.utcnow()
                )
                db.session.add(inscription)
                inscriptions.append(inscription)
        
        db.session.commit()
        
        return jsonify({
            'message': f'{len(inscriptions)} cours affectés au talibé avec succès',
            'talibe': talibe.to_dict(),
            'cours_affectes': [cours.to_dict() for cours in cours_list]
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Erreur affectation cours: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ... autres routes sans dépendance à Inscription ...

@talibe_bp.route('/talibes/chambre/<int:chambre_id>', methods=['GET'])
@jwt_required()
def get_talibes_by_chambre(chambre_id):
    try:
        talibes = Talibe.query.filter_by(chambre_id=chambre_id).all()
        return jsonify([talibe.to_dict() for talibe in talibes]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@talibe_bp.route('/talibes/cours/<int:cours_id>', methods=['GET'])
@jwt_required()
def get_talibes_by_cours(cours_id):
    try:
        cours = Cours.query.get(cours_id)
        if not cours:
            return jsonify({'error': 'Cours non trouvé'}), 404
            
        # Récupérer les talibés via la table d'inscription
        inscriptions = Inscription.query.filter_by(cours_id=cours_id).all()
        talibes = [inscription.talibe for inscription in inscriptions]
        
        return jsonify([talibe.to_dict() for talibe in talibes]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@talibe_bp.route('/talibes/<int:id>/cours', methods=['GET'])
@jwt_required()
def get_cours_by_talibe(id):
    """Récupérer les cours d'un talibé"""
    try:
        talibe = Talibe.query.get(id)
        if not talibe:
            return jsonify({'error': 'Talibé non trouvé'}), 404
            
        # Récupérer les cours via la table d'inscription
        inscriptions = Inscription.query.filter_by(talibe_id=id).all()
        cours_list = [inscription.cours for inscription in inscriptions]
        
        return jsonify([cours.to_dict() for cours in cours_list]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@talibe_bp.route('/talibes/<int:id>', methods=['PUT'])
@jwt_required()
@role_required('ADMIN')
def update_talibe(id):
    """Mettre à jour un talibé"""
    try:
        talibe = Talibe.query.get(id)
        if not talibe:
            return jsonify({'error': 'Talibé non trouvé'}), 404
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données JSON requises'}), 400
        
        # Champs modifiables
        updatable_fields = ['nom', 'prenom', 'pere', 'mere', 'niveau', 'extrait_naissance', 
                           'daara_id', 'chambre_id', 'lieu_naissance', 'age', 'nb_annees']
        
        for field in updatable_fields:
            if field in data:
                setattr(talibe, field, data[field])
        
        # Gestion des dates
        if 'date_naissance' in data and data['date_naissance']:
            talibe.date_naissance = datetime.strptime(data['date_naissance'], '%Y-%m-%d').date()
        
        if 'date_entree' in data and data['date_entree']:
            talibe.date_entree = datetime.strptime(data['date_entree'], '%Y-%m-%d').date()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Talibé mis à jour avec succès',
            'talibe': talibe.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@talibe_bp.route('/talibes/delete/<int:id>', methods=['DELETE'])
@jwt_required()
@role_required('ADMIN')
def delete_talibe(id):
    """Supprimer un talibé"""
    try:
        talibe = Talibe.query.get(id)
        if not talibe:
            return jsonify({'error': 'Talibé non trouvé'}), 404
        
        # Vérifier s'il y a des inscriptions
        inscriptions = Inscription.query.filter_by(talibe_id=id).all()
        if inscriptions:
            return jsonify({'error': 'Impossible de supprimer le talibé car il est inscrit à des cours'}), 400
        
        db.session.delete(talibe)
        db.session.commit()
        
        return jsonify({'message': 'Talibé supprimé avec succès'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500