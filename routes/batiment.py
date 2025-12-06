from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import sys
import os

# Ajouter le chemin pour les imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models import db, Batiment, Daara, Chambre
from decorators import role_required

batiment_bp = Blueprint('batiment', __name__)

@batiment_bp.route('/batiments', methods=['GET'])
@jwt_required()
def get_batiments():
    try:
        batiments = Batiment.query.all()
        return jsonify([batiment.to_dict() for batiment in batiments]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@batiment_bp.route('/batiments/<int:id>', methods=['GET'])
@jwt_required()
def get_batiment(id):
    try:
        batiment = Batiment.query.get_or_404(id)
        return jsonify(batiment.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@batiment_bp.route('/batiments/create', methods=['POST'])
@role_required('ADMIN')
def create_batiment():
    try:
        print("=== DÉBUT CREATE BATIMENT ===")
        data = request.get_json()
        print(f"Données reçues: {data}")
        
        required_fields = ['nom', 'daara_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Le champ {field} est requis'}), 400
        
        # Vérifier que le daara existe
        daara = db.session.get(Daara, data['daara_id'])
        if not daara:
            return jsonify({'error': 'Daara non trouvé'}), 404
        
        batiment = Batiment(
            nom=data['nom'],
            nb_chambres=data.get('nb_chambres', 0),
            daara_id=data['daara_id']
        )
        
        db.session.add(batiment)
        db.session.commit()
        
        print(f"Batiment créé avec ID: {batiment.id}")
        print("=== FIN CREATE BATIMENT ===")
        
        return jsonify({
            'message': 'Batiment créé avec succès',
            'batiment': batiment.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"ERREUR CREATE BATIMENT: {str(e)}")
        import traceback
        print(f"TRACEBACK: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@batiment_bp.route('/batiments/<int:id>', methods=['PUT'])
@role_required('ADMIN')
def update_batiment(id):
    try:
        batiment = Batiment.query.get_or_404(id)
        data = request.get_json()
        
        if 'nom' in data:
            batiment.nom = data['nom']
        if 'nb_chambres' in data:
            batiment.nb_chambres = data['nb_chambres']
        if 'daara_id' in data:
            # Vérifier que le nouveau daara existe
            daara = db.session.get(Daara, data['daara_id'])
            if not daara:
                return jsonify({'error': 'Daara non trouvé'}), 404
            batiment.daara_id = data['daara_id']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Batiment mis à jour avec succès',
            'batiment': batiment.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
@batiment_bp.route('/batiments/<int:id>', methods=['DELETE'])
@role_required('ADMIN')
def delete_batiment(id):
    try:
        print(f"=== DÉBUT DELETE BATIMENT {id} ===")
        batiment = Batiment.query.get_or_404(id)
        print(f"Batiment trouvé: {batiment.nom}")
        
        db.session.delete(batiment)
        db.session.commit()
        
        print(f"Batiment {id} supprimé avec succès")
        print("=== FIN DELETE BATIMENT ===")
        
        return jsonify({'message': 'Batiment supprimé avec succès'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"ERREUR DELETE BATIMENT: {str(e)}")
        import traceback
        print(f"TRACEBACK: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@batiment_bp.route('/batiments/daara/<int:daara_id>', methods=['GET'])
@jwt_required()
def get_batiments_by_daara(daara_id):
    try:
        batiments = Batiment.query.filter_by(daara_id=daara_id).all()
        return jsonify([batiment.to_dict() for batiment in batiments]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    
@batiment_bp.route('/chambres/batiment/<int:batiment_id>', methods=['GET'])
@jwt_required()
def get_chambres_by_batiment(batiment_id):
    try:
        chambres = Chambre.query.filter_by(batiment_id=batiment_id).all()
        return jsonify([chambre.to_dict() for chambre in chambres]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500