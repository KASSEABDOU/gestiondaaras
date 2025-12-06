from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models import db, Enseignant, Cours,RoleEnum, Talibe, Inscription
from decorators import role_required

enseignant_bp = Blueprint('enseignant', __name__)

@enseignant_bp.route('/enseignants', methods=['GET'])
@jwt_required()
def get_enseignants():
    try:
        enseignants = Enseignant.query.all()
        return jsonify([enseignant.to_dict() for enseignant in enseignants]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@enseignant_bp.route('/enseignants/<int:id>', methods=['GET'])
@jwt_required()
def get_enseignant(id):
    try:
        enseignant = Enseignant.query.get(id)
        if not enseignant:
            return jsonify({'error': 'Enseignant non trouvé'}), 404
        return jsonify(enseignant.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@enseignant_bp.route('/enseignants/create', methods=['POST'])
@jwt_required()
@role_required('ADMIN')
def create_enseignant():
    try:
        data = request.get_json()
        print(f"Données création enseignant: {data}")
        
        if not data:
            return jsonify({'error': 'Données JSON requises'}), 400
        
        required_fields = ['matricule', 'nom', 'prenom', 'email', 'password']
        for field in required_fields:
            if field not in data or not data.get(field):
                return jsonify({'error': f'Le champ {field} est requis'}), 400
        
        # Vérifier si le matricule existe déjà
        existing_enseignant = Enseignant.query.filter_by(matricule=data['matricule']).first()
        if existing_enseignant:
            return jsonify({'error': 'Un enseignant avec ce matricule existe déjà'}), 409
        
        # Vérifier si l'email existe déjà
        existing_email = Enseignant.query.filter_by(email=data['email']).first()
        if existing_email:
            return jsonify({'error': 'Un enseignant avec cet email existe déjà'}), 409
        
        enseignant = Enseignant()
        enseignant.matricule = data['matricule']
        enseignant.nom = data['nom']
        enseignant.prenom = data['prenom']
        enseignant.email = data['email']
        enseignant.set_password(data['password'])
        enseignant.role = RoleEnum.ENSEIGNANT.value
        enseignant.specialite = data.get('specialite')
        enseignant.telephone = data.get('telephone', '')
        enseignant.etat_civil = data.get('etat_civil')
        enseignant.grade = data.get('grade', 'Débutant')
        enseignant.sexe = data.get('sexe')
        enseignant.diplome = data.get('diplome')
        enseignant.diplome_origine= data.get('diplome_origine')
        enseignant.statut = data.get('statut')
        enseignant.nationalite = data.get('nationalite')
        
        # Gestion des dates
        if data.get('date_naissance'):
            enseignant.date_naissance = datetime.strptime(data['date_naissance'], '%Y-%m-%d').date()
        
        enseignant.lieu_naissance = data.get('lieu_naissance', '')
        
        if data.get('date_entree'):
            enseignant.date_entree = datetime.strptime(data['date_entree'], '%Y-%m-%d').date()
        else:
            enseignant.date_entree = datetime.utcnow().date()
        
        enseignant.adresse = data.get('adresse')
        
        db.session.add(enseignant)
        db.session.commit()
        
        print(f"Enseignant créé avec ID: {enseignant.id}")
        
        return jsonify({
            'message': 'Enseignant créé avec succès',
            'enseignant': enseignant.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Erreur création enseignant: {str(e)}")
        return jsonify({'error': f'Erreur lors de la création: {str(e)}'}), 500

@enseignant_bp.route('/enseignants/<int:id>', methods=['PUT'])
@jwt_required()
@role_required('ADMIN')
def update_enseignant(id):
    try:
        enseignant = Enseignant.query.get(id)
        if not enseignant:
            return jsonify({'error': 'Enseignant non trouvé'}), 404
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données JSON requises'}), 400
        
        # Champs modifiables
        updatable_fields = ['nom', 'prenom', 'specialite', 'telephone', 'etat_civil', 
                           'grade', 'lieu_naissance', 'age', 'nb_annees', 'adresse']
        
        for field in updatable_fields:
            if field in data:
                setattr(enseignant, field, data[field])
        
        # Gestion des dates
        if 'date_naissance' in data and data['date_naissance']:
            enseignant.date_naissance = datetime.strptime(data['date_naissance'], '%Y-%m-%d').date()
        
        if 'date_entree' in data and data['date_entree']:
            enseignant.date_entree = datetime.strptime(data['date_entree'], '%Y-%m-%d').date()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Enseignant mis à jour avec succès',
            'enseignant': enseignant.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@enseignant_bp.route('/enseignants/<int:id>', methods=['DELETE'])
@jwt_required()
@role_required('ADMIN')
def delete_enseignant(id):
    try:
        enseignant = Enseignant.query.get(id)
        if not enseignant:
            return jsonify({'error': 'Enseignant non trouvé'}), 404
        
        # Vérifier si l'enseignant a des cours
        if enseignant.cours:
            return jsonify({'error': 'Impossible de supprimer l\'enseignant car il est associé à des cours'}), 400
        
        db.session.delete(enseignant)
        db.session.commit()
        
        return jsonify({'message': 'Enseignant supprimé avec succès'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@enseignant_bp.route('/enseignants/<int:id>/cours', methods=['GET'])
@jwt_required()
def get_cours_enseignant(id):
    try:
        enseignant = Enseignant.query.get(id)
        if not enseignant:
            return jsonify({'error': 'Enseignant non trouvé'}), 404
            
        cours_list = enseignant.cours
        return jsonify([cours.to_dict() for cours in cours_list]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@enseignant_bp.route('/enseignants/<int:id>/talibes', methods=['GET'])
@jwt_required()
def get_talibes_enseignant(id):
    try:
        enseignant = Enseignant.query.get(id)
        if not enseignant:
            return jsonify({'error': 'Enseignant non trouvé'}), 404
        
        # Vérifier si l'enseignant a des cours
        if not enseignant.cours or len(enseignant.cours) == 0:
            return jsonify({'error': 'Cet enseignant n\'a pas de cours assignés'}), 404
        
        # Récupérer tous les ID des cours de l'enseignant
        cours_ids = [cours.id for cours in enseignant.cours]
        
        # Récupérer les talibés inscrits dans ces cours
        talibes = Talibe.query\
            .join(Inscription)\
            .filter(Inscription.cours_id.in_(cours_ids))\
            .distinct()\
            .all()
        
        if not talibes:
            return jsonify({'error': 'Aucun talibé trouvé pour les cours de cet enseignant'}), 404
        
        return jsonify([talibe.to_dict() for talibe in talibes]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@enseignant_bp.route('/enseignants/<int:id>/affecter-cours', methods=['POST'])
@jwt_required()
@role_required('ADMIN')
def affecter_cours_enseignant(id):
    try:
        enseignant = Enseignant.query.get(id)
        if not enseignant:
            return jsonify({'error': 'Enseignant non trouvé'}), 404
            
        data = request.get_json()
        if not data or 'cours_ids' not in data:
            return jsonify({'error': 'Liste des cours_ids requise'}), 400
        
        cours_ids = data['cours_ids']
        if not isinstance(cours_ids, list):
            return jsonify({'error': 'cours_ids doit être une liste'}), 400
        
        # Vérifier que tous les cours existent
        cours_list = Cours.query.filter(Cours.id.in_(cours_ids)).all()
        if len(cours_list) != len(cours_ids):
            return jsonify({'error': 'Un ou plusieurs cours non trouvés'}), 404
        
        # Affecter les cours à l'enseignant
        for cours in cours_list:
            if cours not in enseignant.cours:
                enseignant.cours.append(cours)
        
        db.session.commit()
        
        return jsonify({
            'message': f'{len(cours_list)} cours affectés à l\'enseignant avec succès',
            'enseignant': enseignant.to_dict(),
            'cours_affectes': [cours.to_dict() for cours in cours_list]
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@enseignant_bp.route('/enseignants/statistiques', methods=['GET'])
@jwt_required()
def get_statistiques_enseignants():
    try:
        total_enseignants = Enseignant.query.count()
        enseignants_avec_cours = db.session.query(Enseignant).filter(Enseignant.cours.any()).count()
        enseignants_sans_cours = total_enseignants - enseignants_avec_cours
        
        # Enseignant avec le plus de cours
        from sqlalchemy import func
        enseignant_plus_cours = db.session.query(
            Enseignant,
            func.count(Cours.id).label('nb_cours')
        ).join(Enseignant.cours).group_by(Enseignant.id).order_by(func.count(Cours.id).desc()).first()
        
        stats = {
            'total_enseignants': total_enseignants,
            'enseignants_avec_cours': enseignants_avec_cours,
            'enseignants_sans_cours': enseignants_sans_cours,
            'taux_affectation': round((enseignants_avec_cours / total_enseignants * 100) if total_enseignants > 0 else 0, 2)
        }
        
        if enseignant_plus_cours:
            stats['enseignant_plus_actif'] = {
                'id': enseignant_plus_cours[0].id,
                'nom': enseignant_plus_cours[0].nom,
                'prenom': enseignant_plus_cours[0].prenom,
                'nb_cours': enseignant_plus_cours[1]
            }
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500