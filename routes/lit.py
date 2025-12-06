from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import sys
import os

# Ajouter le chemin pour les imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models import db, Lit, Chambre
from decorators import role_required

lit_bp = Blueprint('lit', __name__)

# === ROUTES POUR LITS ===

@lit_bp.route('/lits', methods=['GET'])
@jwt_required()
def get_lits():
    """
    Récupérer tous les lits
    """
    try:
        lits = Lit.query.all()
        
        lits_data = []
        for lit in lits:
            lit_data = lit.to_dict()
            lit_data['chambre'] = lit.chambre.to_dict() if lit.chambre else None
            lits_data.append(lit_data)
            
        return jsonify(lits_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lit_bp.route('/lits/<int:id>', methods=['GET'])
@jwt_required()
def get_lit(id):
    """
    Récupérer un lit spécifique
    """
    try:
        lit = db.session.get(Lit, id)
        if not lit:
            return jsonify({'error': 'Lit non trouvé'}), 404
        
        lit_data = lit.to_dict()
        lit_data['chambre'] = lit.chambre.to_dict() if lit.chambre else None
        if lit.chambre:
            lit_data['batiment'] = lit.chambre.batiment.to_dict() if lit.chambre.batiment else None
        
        return jsonify(lit_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lit_bp.route('/lits/create', methods=['POST'])
@role_required('ADMIN')
def create_lit():
    """
    Créer un nouveau lit
    """
    try:
        data = request.get_json()
        
        required_fields = ['numero', 'chambre_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Le champ {field} est requis'}), 400
        
        # Vérifier si la chambre existe
        chambre = db.session.get(Chambre, data['chambre_id'])
        if not chambre:
            return jsonify({'error': 'Chambre non trouvée'}), 404
        
        # Vérifier si le numéro de lit existe déjà dans cette chambre
        existing_lit = Lit.query.filter_by(
            numero=data['numero'], 
            chambre_id=data['chambre_id']
        ).first()
        if existing_lit:
            return jsonify({'error': 'Un lit avec ce numéro existe déjà dans cette chambre'}), 400
        
        lit = Lit(
            numero=data['numero'],
            chambre_id=data['chambre_id']
        )
        
        db.session.add(lit)
        db.session.commit()
        
        # Mettre à jour le nombre de lits dans la chambre
        chambre.nb_lits = Lit.query.filter_by(chambre_id=chambre.id).count()
        db.session.commit()
        
        return jsonify({
            'message': 'Lit créé avec succès',
            'lit': lit.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@lit_bp.route('/lits/<int:id>', methods=['PUT'])
@role_required('ADMIN')
def update_lit(id):
    """
    Mettre à jour un lit
    """
    try:
        lit = db.session.get(Lit, id)
        if not lit:
            return jsonify({'error': 'Lit non trouvé'}), 404
            
        data = request.get_json()
        
        if 'numero' in data:
            # Vérifier si le nouveau numéro existe déjà dans la même chambre
            existing_lit = Lit.query.filter_by(
                numero=data['numero'], 
                chambre_id=lit.chambre_id
            ).first()
            if existing_lit and existing_lit.id != id:
                return jsonify({'error': 'Un lit avec ce numéro existe déjà dans cette chambre'}), 400
            lit.numero = data['numero']
        
        if 'chambre_id' in data:
            # Vérifier si la nouvelle chambre existe
            chambre = db.session.get(Chambre, data['chambre_id'])
            if not chambre:
                return jsonify({'error': 'Chambre non trouvée'}), 404
            
            # Mettre à jour les compteurs des anciennes et nouvelles chambres
            old_chambre_id = lit.chambre_id
            lit.chambre_id = data['chambre_id']
            
            # Mettre à jour le compteur de l'ancienne chambre
            old_chambre = db.session.get(Chambre, old_chambre_id)
            if old_chambre:
                old_chambre.nb_lits = Lit.query.filter_by(chambre_id=old_chambre_id).count()
            
            # Mettre à jour le compteur de la nouvelle chambre
            chambre.nb_lits = Lit.query.filter_by(chambre_id=data['chambre_id']).count()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Lit mis à jour avec succès',
            'lit': lit.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@lit_bp.route('/lits/<int:id>', methods=['DELETE'])
@role_required('ADMIN')
def delete_lit(id):
    """
    Supprimer un lit
    """
    try:
        lit = db.session.get(Lit, id)
        if not lit:
            return jsonify({'error': 'Lit non trouvé'}), 404
        
        # Sauvegarder l'ID de la chambre pour mettre à jour le compteur
        chambre_id = lit.chambre_id
        
        db.session.delete(lit)
        db.session.commit()
        
        # Mettre à jour le compteur de lits de la chambre
        chambre = db.session.get(Chambre, chambre_id)
        if chambre:
            chambre.nb_lits = Lit.query.filter_by(chambre_id=chambre_id).count()
            db.session.commit()
        
        return jsonify({'message': 'Lit supprimé avec succès'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@lit_bp.route('/lits/chambre/<int:chambre_id>', methods=['GET'])
@jwt_required()
def get_lits_by_chambre(chambre_id):
    """
    Récupérer tous les lits d'une chambre
    """
    try:
        chambre = db.session.get(Chambre, chambre_id)
        if not chambre:
            return jsonify({'error': 'Chambre non trouvée'}), 404
            
        lits = Lit.query.filter_by(chambre_id=chambre_id).all()
        
        lits_data = []
        for lit in lits:
            lit_data = lit.to_dict()
            lits_data.append(lit_data)
        
        return jsonify(lits_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lit_bp.route('/lits/statistiques', methods=['GET'])
@jwt_required()
def get_statistiques_lits():
    """
    Récupérer les statistiques des lits
    """
    try:
        total_lits = Lit.query.count()
        total_chambres = Chambre.query.count()
        
        # Calculer les lits occupés (en supposant qu'un talibé = un lit occupé)
        chambres = Chambre.query.all()
        lits_occupes = 0
        
        for chambre in chambres:
            lits_occupes += len(chambre.talibes)
        
        return jsonify({
            'total_lits': total_lits,
            'total_chambres': total_chambres,
            'lits_occupes': lits_occupes,
            'lits_disponibles': total_lits - lits_occupes,
            'taux_occupation_lits': round((lits_occupes / total_lits * 100) if total_lits > 0 else 0, 2),
            'moyenne_lits_par_chambre': round(total_lits / total_chambres, 2) if total_chambres > 0 else 0
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lit_bp.route('/lits/recherche', methods=['GET'])
@jwt_required()
def rechercher_lits():
    """
    Rechercher des lits avec filtres
    """
    try:
        chambre_id = request.args.get('chambre_id', type=int)
        batiment_id = request.args.get('batiment_id', type=int)
        disponible = request.args.get('disponible', type=str)
        
        query = Lit.query
        
        if chambre_id:
            query = query.filter_by(chambre_id=chambre_id)
        
        if batiment_id:
            query = query.join(Chambre).filter(Chambre.batiment_id == batiment_id)
        
        lits = query.all()
        
        # Filtrer par disponibilité si demandé
        if disponible:
            lits_filtres = []
            for lit in lits:
                # Un lit est considéré comme occupé si sa chambre a plus de talibés que de lits disponibles
                chambre = lit.chambre
                lits_occupes = len(chambre.talibes)
                est_occupe = lits_occupes >= chambre.nb_lits
                
                if disponible.lower() == 'true' and not est_occupe:
                    lits_filtres.append(lit)
                elif disponible.lower() == 'false' and est_occupe:
                    lits_filtres.append(lit)
            
            lits = lits_filtres
        
        lits_data = []
        for lit in lits:
            lit_data = lit.to_dict()
            lit_data['chambre'] = lit.chambre.to_dict() if lit.chambre else None
            if lit.chambre and lit.chambre.batiment:
                lit_data['batiment'] = lit.chambre.batiment.to_dict()
            
            # Déterminer si le lit est disponible
            chambre = lit.chambre
            lits_occupes = len(chambre.talibes)
            lit_data['disponible'] = lits_occupes < chambre.nb_lits
            
            lits_data.append(lit_data)
        
        return jsonify(lits_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500