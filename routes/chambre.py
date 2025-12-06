from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import sys
import os

# Ajouter le chemin pour les imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models import db, Chambre, Batiment, Talibe
from decorators import role_required

chambre_bp = Blueprint('chambre', __name__)

@chambre_bp.route('/chambres', methods=['GET'])
@jwt_required()
def get_chambres():
    try:
        chambres = Chambre.query.all()
        return jsonify([chambre.to_dict() for chambre in chambres]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chambre_bp.route('/chambres/<int:id>', methods=['GET'])
@jwt_required()
def get_chambre(id):
    try:
        chambre = db.session.get(Chambre, id)
        if not chambre:
            return jsonify({'error': 'Chambre non trouvée'}), 404
        return jsonify(chambre.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chambre_bp.route('/chambres/create', methods=['POST'])
@role_required('ADMIN')
def create_chambre():
    try:
        print("=== DÉBUT CREATE CHAMBRE ===")
        data = request.get_json()
        print(f"Données reçues: {data}")
        
        required_fields = ['numero', 'batiment_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Le champ {field} est requis'}), 400
        
        # Vérifier que le batiment existe
        batiment = db.session.get(Batiment, data['batiment_id'])
        if not batiment:
            return jsonify({'error': 'Batiment non trouvé'}), 404
        
        chambre = Chambre(
            numero=data['numero'],
            nb_lits=data.get('nb_lits', 0),
            batiment_id=data['batiment_id']
        )
        
        db.session.add(chambre)
        db.session.commit()
        
        print(f"Chambre créée avec ID: {chambre.id}")
        print("=== FIN CREATE CHAMBRE ===")
        
        return jsonify({
            'message': 'Chambre créée avec succès',
            'chambre': chambre.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"ERREUR CREATE CHAMBRE: {str(e)}")
        import traceback
        print(f"TRACEBACK: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@chambre_bp.route('/chambres/<int:id>', methods=['PUT'])
@role_required('ADMIN')
def update_chambre(id):
    try:
        chambre = db.session.get(Chambre, id)
        if not chambre:
            return jsonify({'error': 'Chambre non trouvée'}), 404
            
        data = request.get_json()
        
        if 'numero' in data:
            chambre.numero = data['numero']
        if 'nb_lits' in data:
            chambre.nb_lits = data['nb_lits']
        if 'batiment_id' in data:
            # Vérifier que le nouveau batiment existe
            batiment = db.session.get(Batiment, data['batiment_id'])
            if not batiment:
                return jsonify({'error': 'Batiment non trouvé'}), 404
            chambre.batiment_id = data['batiment_id']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Chambre mise à jour avec succès',
            'chambre': chambre.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@chambre_bp.route('/chambres/<int:id>', methods=['DELETE'])
@role_required('ADMIN')
def delete_chambre(id):
    try:
        chambre = db.session.get(Chambre, id)
        if not chambre:
            return jsonify({'error': 'Chambre non trouvée'}), 404
        
        db.session.delete(chambre)
        db.session.commit()
        
        return jsonify({'message': 'Chambre supprimée avec succès'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500



@chambre_bp.route('/chambres/<int:id>/talibes', methods=['GET'])
@jwt_required()
def get_talibes_by_chambre(id):
    try:
        chambre = db.session.get(Chambre, id)
        if not chambre:
            return jsonify({'error': 'Chambre non trouvée'}), 404
            
        talibes = Talibe.query.filter_by(chambre_id=id).all()
        return jsonify([talibe.to_dict() for talibe in talibes]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chambre_bp.route('/chambres/<int:id>/affecter-talibe', methods=['POST'])
@jwt_required()
@role_required('ADMIN')
def affecter_talibe_chambre(id):
    """Affecter un talibé à une chambre"""
    try:
        print(f"=== DÉBUT AFFECTATION TALIBE CHAMBRE {id} ===")
        data = request.get_json()
        print(f"Données reçues: {data}")
        
        if not data.get('talibe_id'):
            return jsonify({'error': 'ID du talibé requis'}), 400
        
        # CORRECTION: Utiliser db.session.get() au lieu de Query.get()
        chambre = db.session.get(Chambre, id)
        if not chambre:
            return jsonify({'error': 'Chambre non trouvée'}), 404
            
        talibe = db.session.get(Talibe, data['talibe_id'])
        if not talibe:
            return jsonify({'error': 'Talibé non trouvé'}), 404
        
        # Vérifier si la chambre a de la place
        if chambre.nb_lits > 0:
            talibes_dans_chambre = Talibe.query.filter_by(chambre_id=id).count()
            if talibes_dans_chambre >= chambre.nb_lits:
                return jsonify({'error': 'La chambre est pleine'}), 400
        
        # Retirer le talibé de son ancienne chambre s'il en a une
        if talibe.chambre_id:
            ancienne_chambre = db.session.get(Chambre, talibe.chambre_id)
            if ancienne_chambre:
                print(f"Talibé retiré de l'ancienne chambre: {ancienne_chambre.id}")
        
        # CORRECTION: Utiliser datetime.now(timezone.utc)
        from datetime import datetime, timezone
        
        # Affecter à la nouvelle chambre
        talibe.chambre_id = id
        talibe.date_entree = datetime.now(timezone.utc).date()  # CORRECTION
        
        db.session.commit()
        
        print(f"Talibé {talibe.id} affecté à la chambre {id}")
        print("=== FIN AFFECTATION TALIBE CHAMBRE ===")
        
        return jsonify({
            'message': 'Talibé affecté à la chambre avec succès',
            'talibe': talibe.to_dict(),
            'chambre': chambre.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"ERREUR AFFECTATION TALIBE CHAMBRE: {str(e)}")
        import traceback
        print(f"TRACEBACK: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@chambre_bp.route('/chambres/<int:id>/retirer-talibe/<int:talibe_id>', methods=['POST'])
@role_required('ADMIN')
def retirer_talibe_chambre(id, talibe_id):
    try:
        chambre = db.session.get(Chambre, id)
        if not chambre:
            return jsonify({'error': 'Chambre non trouvée'}), 404
            
        talibe = db.session.get(Talibe, talibe_id)
        if not talibe:
            return jsonify({'error': 'Talibé non trouvé'}), 404
        
        if talibe.chambre_id != id:
            return jsonify({'error': 'Ce talibé n\'est pas dans cette chambre'}), 400
        
        talibe.chambre_id = None
        db.session.commit()
        
        return jsonify({
            'message': 'Talibé retiré de la chambre avec succès',
            'talibe': talibe.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@chambre_bp.route('/chambres/<int:id>/lits', methods=['GET'])
@jwt_required()
def get_lits_by_chambre(id):
    try:
        chambre = db.session.get(Chambre, id)
        if not chambre:
            return jsonify({'error': 'Chambre non trouvée'}), 404
            
        lits = chambre.lits
        return jsonify([lit.to_dict() for lit in lits]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chambre_bp.route('/chambres/statistiques', methods=['GET'])
@jwt_required()
def get_statistiques_chambres():
    try:
        total_chambres = Chambre.query.count()
        chambres_pleines = 0
        chambres_vides = 0
        total_talibes = 0
        total_lits = 0
        
        chambres = Chambre.query.all()
        for chambre in chambres:
            nb_talibes = len(chambre.talibes)
            nb_lits = chambre.nb_lits
            total_talibes += nb_talibes
            total_lits += nb_lits
            
            if nb_lits > 0 and nb_talibes >= nb_lits:
                chambres_pleines += 1
            elif nb_talibes == 0:
                chambres_vides += 1
        
        return jsonify({
            'total_chambres': total_chambres,
            'chambres_pleines': chambres_pleines,
            'chambres_vides': chambres_vides,
            'chambres_partiellement_occupees': total_chambres - chambres_pleines - chambres_vides,
            'total_talibes_heberges': total_talibes,
            'total_lits': total_lits,
            'taux_occupation': round((total_talibes / total_lits * 100) if total_lits > 0 else 0, 2)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500