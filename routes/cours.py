from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError
from models import db, Cours, Inscription, Talibe,Enseignant,enseignant_cours
from schemas import CoursCreateSchema, CoursUpdateSchema
from decorators import role_required
from datetime import datetime, timezone

cours_bp = Blueprint('cours', __name__)

@cours_bp.route('/cours', methods=['GET'])
@jwt_required()
def get_cours():
    """Récupère tous les cours avec filtres optionnels"""
    try:
        # Filtres optionnels
        categorie = request.args.get('categorie')
        niveau = request.args.get('niveau')
        actif = request.args.get('actif', type=lambda x: x.lower() == 'true')
        
        query = Cours.query
        
        if categorie:
            query = query.filter(Cours.categorie == categorie)
        if niveau:
            query = query.filter(Cours.niveau == niveau)
        if actif is not None:
            query = query.filter(Cours.is_active == actif)
        
        cours_list = query.all()
        return jsonify([cours.to_dict() for cours in cours_list]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cours_bp.route('/cours/<int:id>', methods=['GET'])
@jwt_required()
def get_cour(id):
    """Récupère un cours spécifique par son ID"""
    try:
        cours = db.session.get(Cours, id)
        if not cours:
            return jsonify({'error': 'Cours non trouvé'}), 404
        return jsonify(cours.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cours_bp.route('/cours/create', methods=['POST'])
@jwt_required()
@role_required('ADMIN')
def create_cours():
    """Crée un nouveau cours avec tous les champs du formulaire"""
    try:
        data = request.get_json()
        
        # Validation avec Marshmallow
        schema = CoursCreateSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as err:
            return jsonify({'errors': err.messages}), 400
        
        # Générer un code si non fourni
        if not validated_data.get('code') and validated_data.get('libelle'):
            cours_temp = Cours(libelle=validated_data['libelle'])
            cours_temp.generate_code_suggestion()
            validated_data['code'] = cours_temp.code
        
        # Création du cours avec tous les champs
        cours = Cours(**validated_data)
        
        db.session.add(cours)
        db.session.commit()
        
        return jsonify({
            'message': 'Cours créé avec succès',
            'cours': cours.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@cours_bp.route('/cours/<int:id>', methods=['PUT'])
@jwt_required()
@role_required('ADMIN')
def update_cours(id):
    """Met à jour un cours existant"""
    try:
        cours = db.session.get(Cours, id)
        if not cours:
            return jsonify({'error': 'Cours non trouvé'}), 404
        
        data = request.get_json()
        
        # Validation avec Marshmallow
        schema = CoursUpdateSchema(context={'instance': cours})
        try:
            validated_data = schema.load(data, partial=True)
        except ValidationError as err:
            return jsonify({'errors': err.messages}), 400
        
        # Mise à jour des champs
        for key, value in validated_data.items():
            if hasattr(cours, key):
                setattr(cours, key, value)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Cours mis à jour avec succès',
            'cours': cours.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@cours_bp.route('/cours/<int:id>', methods=['DELETE'])
@jwt_required()
@role_required('ADMIN')
def delete_cours(id):
    """Supprime un cours"""
    try:
        cours = db.session.get(Cours, id)
        if not cours:
            return jsonify({'error': 'Cours non trouvé'}), 404
        
        # Vérifier s'il y a des talibés inscrits
        if cours.talibes:
            return jsonify({
                'error': 'Impossible de supprimer ce cours car des talibés y sont inscrits'
            }), 400
        
        db.session.delete(cours)
        db.session.commit()
        
        return jsonify({'message': 'Cours supprimé avec succès'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@cours_bp.route('/cours/suggestions', methods=['GET'])
@jwt_required()
def get_code_suggestions():
    """Génère des suggestions de code basées sur le libellé"""
    try:
        libelle = request.args.get('libelle', '')
        
        if len(libelle) < 3:
            return jsonify({'suggestions': []})
        
        prefix = libelle[:3].upper()
        suggestions = []
        
        for i in range(3):
            code = f"{prefix}{101 + i}"
            # Vérifier si le code n'existe pas déjà
            existing = Cours.query.filter_by(code=code).first()
            if not existing:
                suggestions.append(code)
        
        return jsonify({'suggestions': suggestions}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cours_bp.route('/cours/categories', methods=['GET'])
@jwt_required()
def get_categories():
    """Retourne la liste des catégories disponibles"""
    try:
        categories = [
            {'value': 'Coran', 'label': 'Coran', 'icon': 'menu_book'},
            {'value': 'Hadith', 'label': 'Hadith', 'icon': 'history_edu'},
            {'value': 'Fiqh', 'label': 'Fiqh', 'icon': 'gavel'},
            {'value': 'Tafsir', 'label': 'Tafsir', 'icon': 'auto_stories'},
            {'value': 'Langue Arabe', 'label': 'Langue Arabe', 'icon': 'translate'},
            {'value': 'Sciences Islamiques', 'label': 'Sciences Islamiques', 'icon': 'school'},
            {'value': 'Autre', 'label': 'Autre', 'icon': 'more_horiz'}
        ]
        return jsonify({'categories': categories}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cours_bp.route('/cours/niveaux', methods=['GET'])
@jwt_required()
def get_niveaux():
    """Retourne la liste des niveaux disponibles"""
    try:
        niveaux = [
            {'value': 'Débutant', 'label': 'Débutant'},
            {'value': 'Intermédiaire', 'label': 'Intermédiaire'},
            {'value': 'Avancé', 'label': 'Avancé'},
            {'value': 'Tous niveaux', 'label': 'Tous niveaux'}
        ]
        return jsonify({'niveaux': niveaux}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cours_bp.route('/cours/<int:id>/toggle-status', methods=['PATCH'])
@jwt_required()
@role_required('ADMIN')
def toggle_cours_status(id):
    """Active/désactive un cours"""
    try:
        cours = db.session.get(Cours, id)
        if not cours:
            return jsonify({'error': 'Cours non trouvé'}), 404
        
        cours.is_active = not cours.is_active
        db.session.commit()
        
        status = "activé" if cours.is_active else "désactivé"
        return jsonify({
            'message': f'Cours {status} avec succès',
            'cours': cours.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@cours_bp.route('/cours/<int:id>/talibes', methods=['GET'])
@jwt_required()
def get_cours_talibes(id):
    """Récupère la liste des talibés inscrits à un cours"""
    try:
        cours = db.session.get(Cours, id)
        if not cours:
            return jsonify({'error': 'Cours non trouvé'}), 404
        
        talibes_inscrits = Talibe.query\
            .join(Inscription)\
            .filter(Inscription.cours_id == cours.id)\
            .all()
        
        result = [talibe.to_dict() for talibe in talibes_inscrits]
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cours_bp.route('/cours/<int:id>/enseignants', methods=['GET'])
@jwt_required()
def get_cours_enseignants(id):
    """Récupère la liste des enseignants assignés à un cours"""
    try:
        # Vérifier que le cours existe
        cours = db.session.get(Cours, id)
        if not cours:
            return jsonify({'error': 'Cours non trouvé'}), 404
        
        # 🔥 Récupérer directement les IDs des enseignants assignés
        enseignant_ids = db.session.execute(
            enseignant_cours.select().with_only_columns(enseignant_cours.c.enseignant_id)
            .where(enseignant_cours.c.cours_id == id)
        ).scalars().all()
        
        # 🔥 Récupérer les enseignants
        enseignants = Enseignant.query.filter(Enseignant.id.in_(enseignant_ids)).all()
        
        # 🔥 Convertir en JSON
        return jsonify([enseignant.to_dict() for enseignant in enseignants]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@cours_bp.route('/cours/<int:cours_id>/confier_enseignant', methods=['POST'])
def confier_enseignant_cours(cours_id):
    """Assigner un enseignant à un cours"""
    try:
        data = request.get_json()
        enseignant_id = data.get('enseignant_id')
        role = data.get('role', 'titulaire')
        
        if not enseignant_id:
            return jsonify({'error': 'ID enseignant requis'}), 400
        
        # Vérifier que le cours existe
        cours = Cours.query.get_or_404(cours_id)
        
        # Vérifier que l'enseignant existe
        enseignant = Enseignant.query.get_or_404(enseignant_id)
        
        # Vérifier si l'enseignant est déjà assigné à ce cours
        existing = db.session.execute(
            enseignant_cours.select().where(
                enseignant_cours.c.cours_id == cours_id,
                enseignant_cours.c.enseignant_id == enseignant_id
            )
        ).first()
        
        if existing:
            return jsonify({'error': 'Cet enseignant est déjà assigné à ce cours'}), 400
        
        # Assigner l'enseignant au cours
        insert_stmt = enseignant_cours.insert().values(
            cours_id=cours_id,
            enseignant_id=enseignant_id,
            role=role,
            date_assignation=datetime.utcnow()
        )
        
        db.session.execute(insert_stmt)
        db.session.commit()
        
        return jsonify({
            'message': f'Enseignant {enseignant.prenom} {enseignant.nom} assigné au cours {cours.libelle}',
            'assignation': {
                'enseignant_id': enseignant_id,
                'cours_id': cours_id,
                'role': role,
                'date_assignation': datetime.utcnow().isoformat()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500