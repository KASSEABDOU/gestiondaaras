from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import sys
import os

# Ajouter le chemin pour les imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models import db, Daara, Talibe, Enseignant, Batiment
from decorators import role_required

daara_bp = Blueprint('daara', __name__)

@daara_bp.route('/daaras', methods=['GET'])
@jwt_required()
def get_daaras():
    try:
        daaras = Daara.query.all()
        return jsonify([daara.to_dict() for daara in daaras]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@daara_bp.route('/daara/<int:id>', methods=['GET'])
@jwt_required()
def get_daara(id):
    try:
        daara = Daara.query.get_or_404(id)
        return jsonify(daara.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@daara_bp.route('/daaras/create', methods=['POST'])
@role_required('ADMIN')
def create_daara():
    try:
        print("=== DÉBUT CREATE DAARA ===")
        data = request.get_json()
        print(f"Données reçues: {data}")
        
        required_fields = ['nom', 'lieu']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Le champ {field} est requis'}), 400
        
        daara = Daara(
            nom=data['nom'],
            proprietaire=data.get('proprietaire'),
            lieu=data['lieu'],
            nb_talibes=data.get('nb_talibes', 0),
            nb_enseignants=data.get('nb_enseignants', 0),
            nb_batiments=data.get('nb_batiments', 0)
        )
        
        db.session.add(daara)
        db.session.commit()
        
        print(f"Daara créé avec ID: {daara.id}")
        print("=== FIN CREATE DAARA ===")
        
        return jsonify({
            'message': 'Daara créé avec succès',
            'daara': daara.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"ERREUR CREATE DAARA: {str(e)}")
        import traceback
        print(f"TRACEBACK: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@daara_bp.route('/update_daara/<int:id>', methods=['PUT'])
@role_required('ADMIN')
def update_daara(id):
    try:
        daara = Daara.query.get_or_404(id)
        data = request.get_json()
        
        if 'nom' in data:
            daara.nom = data['nom']
        if 'proprietaire' in data:
            daara.proprietaire = data['proprietaire']
        if 'lieu' in data:
            daara.lieu = data['lieu']
        if 'nb_talibes' in data:
            daara.nb_talibes = data['nb_talibes']
        if 'nb_enseignants' in data:
            daara.nb_enseignants = data['nb_enseignants']
        if 'nb_batiments' in data:
            daara.nb_batiments = data['nb_batiments']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Daara mis à jour avec succès',
            'daara': daara.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@daara_bp.route('/delete_daara/<int:id>', methods=['DELETE'])
@role_required('ADMIN')
def delete_daara(id):
    try:
        daara = Daara.query.get_or_404(id)
        
        db.session.delete(daara)
        db.session.commit()
        
        return jsonify({'message': 'Daara supprimé avec succès'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@daara_bp.route('/daaras/<int:id>/talibes', methods=['GET'])
@jwt_required()
def get_talibes_by_daara(id):
    try:
        talibes = Talibe.query.filter_by(daara_id=id).all()
        return jsonify([talibe.to_dict() for talibe in talibes]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@daara_bp.route('/daaras/<int:id>/enseignants', methods=['GET'])
@jwt_required()
def get_enseignants_by_daara(id):
    try:
        enseignants = Enseignant.query.filter_by(daara_id=id).all()
        return jsonify([enseignant.to_dict() for enseignant in enseignants]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@daara_bp.route('/daaras/<int:id>/batiments', methods=['GET'])
@jwt_required()
def get_batiments_by_daara(id):
    try:
        batiments = Batiment.query.filter_by(daara_id=id).all()
        return jsonify([batiment.to_dict() for batiment in batiments]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500