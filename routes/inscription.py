from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone
from models import db, Inscription, Talibe, Cours
from decorators import role_required

inscription_bp = Blueprint('inscription', __name__)

@inscription_bp.route('/inscriptions', methods=['GET'])
@jwt_required()
def get_inscriptions():
    """Récupérer toutes les inscriptions"""
    try:
        inscriptions = Inscription.query.all()
        return jsonify([inscription.to_dict() for inscription in inscriptions]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inscription_bp.route('/inscriptions/inscrire', methods=['POST'])
@jwt_required()
@role_required('ADMIN')
def create_inscription():
    """Créer une nouvelle inscription"""
    try:
        data = request.get_json()
        print(f"=== CRÉATION INSCRIPTION ===")
        print(f"Données: {data}")
        
        if not data:
            return jsonify({'error': 'Données JSON requises'}), 400
        
        required_fields = ['talibe_id', 'cours_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Le champ {field} est requis'}), 400
        
        # Vérifier que le talibé existe
        talibe = db.session.get(Talibe, data['talibe_id'])
        if not talibe:
            return jsonify({'error': 'Talibé non trouvé'}), 404
        
        # Vérifier que le cours existe
        cours = db.session.get(Cours, data['cours_id'])
        if not cours:
            return jsonify({'error': 'Cours non trouvé'}), 404
        
        # Vérifier si l'inscription existe déjà
        inscription_existante = Inscription.query.filter_by(
            talibe_id=data['talibe_id'],
            cours_id=data['cours_id']
        ).first()
        
        if inscription_existante:
            return jsonify({'error': 'Le talibé est déjà inscrit à ce cours'}), 409
        
        # Créer l'inscription
        inscription = Inscription(
            talibe_id=data['talibe_id'],
            cours_id=data['cours_id'],
            note=data.get('note')
        )
        
        db.session.add(inscription)
        db.session.commit()
        
        print(f"Inscription créée avec ID: {inscription.id}")
        print("=== FIN CRÉATION INSCRIPTION ===")
        
        return jsonify({
            'message': 'Inscription créée avec succès',
            'inscription': inscription.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"ERREUR CRÉATION INSCRIPTION: {str(e)}")
        return jsonify({'error': str(e)}), 500

@inscription_bp.route('/inscriptions/<int:id>', methods=['GET'])
@jwt_required()
def get_inscription(id):
    """Récupérer une inscription spécifique"""
    try:
        inscription = db.session.get(Inscription, id)
        if not inscription:
            return jsonify({'error': 'Inscription non trouvée'}), 404
        return jsonify(inscription.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inscription_bp.route('/inscriptions/<int:id>', methods=['PUT'])
@jwt_required()
@role_required('ADMIN')
def update_inscription(id):
    """Mettre à jour une inscription (changer la note)"""
    try:
        inscription = db.session.get(Inscription, id)
        if not inscription:
            return jsonify({'error': 'Inscription non trouvée'}), 404
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données JSON requises'}), 400
        
        if 'note' in data:
            inscription.note = data['note']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Inscription mise à jour avec succès',
            'inscription': inscription.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@inscription_bp.route('/inscriptions/desincrire/<int:id>', methods=['DELETE'])
@jwt_required()
@role_required('ADMIN')
def delete_inscription(id):
    """Supprimer une inscription"""
    try:
        inscription = db.session.get(Inscription, id)
        if not inscription:
            return jsonify({'error': 'Inscription non trouvée'}), 404
        
        db.session.delete(inscription)
        db.session.commit()
        
        return jsonify({'message': 'Inscription supprimée avec succès'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@inscription_bp.route('/talibes/<int:talibe_id>/cours', methods=['GET'])
@jwt_required()
def get_cours_by_talibe(talibe_id):
    """Récupérer les cours d'un talibé"""
    try:
        talibe = db.session.get(Talibe, talibe_id)
        if not talibe:
            return jsonify({'error': 'Talibé non trouvé'}), 404
        
        inscriptions = Inscription.query.filter_by(talibe_id=talibe_id).all()
        cours_list = [inscription.cours for inscription in inscriptions]
        
        return jsonify([cours.to_dict() for cours in cours_list]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inscription_bp.route('/cours/<int:cours_id>/talibes', methods=['GET'])
@jwt_required()
def get_talibes_by_cours(cours_id):
    """Récupérer les talibés d'un cours"""
    try:
        cours = db.session.get(Cours, cours_id)
        if not cours:
            return jsonify({'error': 'Cours non trouvé'}), 404
        
        inscriptions = Inscription.query.filter_by(cours_id=cours_id).all()
        talibes_list = [inscription.talibe for inscription in inscriptions]
        
        return jsonify([talibe.to_dict() for talibe in talibes_list]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inscription_bp.route('/inscriptions/talibe/<int:talibe_id>', methods=['GET'])
@jwt_required()
def get_inscriptions_by_talibe(talibe_id):
    """Récupérer toutes les inscriptions d'un talibé"""
    try:
        talibe = db.session.get(Talibe, talibe_id)
        if not talibe:
            return jsonify({'error': 'Talibé non trouvé'}), 404
        
        inscriptions = Inscription.query.filter_by(talibe_id=talibe_id).all()
        return jsonify([inscription.to_dict() for inscription in inscriptions]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inscription_bp.route('/inscriptions/cours/<int:cours_id>', methods=['GET'])
@jwt_required()
def get_inscriptions_by_cours(cours_id):
    """Récupérer toutes les inscriptions d'un cours"""
    try:
        cours = db.session.get(Cours, cours_id)
        if not cours:
            return jsonify({'error': 'Cours non trouvé'}), 404
        
        inscriptions = Inscription.query.filter_by(cours_id=cours_id).all()
        return jsonify([inscription.to_dict() for inscription in inscriptions]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500