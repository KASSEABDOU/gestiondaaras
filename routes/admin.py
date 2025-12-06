from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Admin, Utilisateur, Talibe, Enseignant, Daara, Batiment, Chambre, db
from models import RoleEnum

admin_bp = Blueprint('admin', __name__)

# ============================================================================
# MIDDLEWARE - Vérifier que l'utilisateur est un admin
# ============================================================================

def admin_required(f):
    """Décorateur pour vérifier que l'utilisateur est un administrateur"""
    from functools import wraps
    
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_email = get_jwt_identity()
        user = Utilisateur.query.filter_by(email=current_user_email).first()
        
        if not user or user.role != RoleEnum.ADMIN:
            return jsonify({"error": "Accès refusé. Administrateur requis"}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

# ============================================================================
# DASHBOARD & STATISTIQUES
# ============================================================================

@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def get_dashboard():
    """Récupère les statistiques du dashboard admin"""
    try:
        # Statistiques générales
        total_talibes = Talibe.query.count()
        total_enseignants = Enseignant.query.count()
        total_daaras = Daara.query.count()
        total_batiments = Batiment.query.count()
        total_chambres = Chambre.query.count()
        
        # Talibes par daara
        talibes_par_daara = db.session.query(
            Daara.nom, 
            db.func.count(Talibe.id)
        ).outerjoin(Talibe).group_by(Daara.id).all()
        
        # Statistiques des chambres
        chambres_par_batiment = db.session.query(
            Batiment.nom,
            db.func.count(Chambre.id)
        ).outerjoin(Chambre).group_by(Batiment.id).all()
        
        return jsonify({
            "statistiques": {
                "total_talibes": total_talibes,
                "total_enseignants": total_enseignants,
                "total_daaras": total_daaras,
                "total_batiments": total_batiments,
                "total_chambres": total_chambres
            },
            "talibes_par_daara": [
                {"daara": daara, "count": count} 
                for daara, count in talibes_par_daara
            ],
            "chambres_par_batiment": [
                {"batiment": batiment, "count": count} 
                for batiment, count in chambres_par_batiment
            ]
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la récupération du dashboard: {str(e)}"}), 500

# ============================================================================
# GESTION DES UTILISATEURS
# ============================================================================

@admin_bp.route('/utilisateurs', methods=['GET'])
@admin_required
def get_all_utilisateurs():
    """Récupère tous les utilisateurs"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        role = request.args.get('role')
        
        query = Utilisateur.query
        
        if role:
            query = query.filter_by(role=RoleEnum(role))
        
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            "utilisateurs": [user.to_dict() for user in pagination.items],
            "total": pagination.total,
            "pages": pagination.pages,
            "page_courante": page
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la récupération des utilisateurs: {str(e)}"}), 500

@admin_bp.route('/utilisateurs/<int:user_id>', methods=['GET'])
@admin_required
def get_utilisateur(user_id):
    """Récupère un utilisateur spécifique"""
    try:
        user = Utilisateur.query.get_or_404(user_id)
        return jsonify({"utilisateur": user.to_dict()}), 200
        
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la récupération de l'utilisateur: {str(e)}"}), 500

@admin_bp.route('/utilisateurs/<int:user_id>', methods=['PUT'])
@admin_required
def update_utilisateur(user_id):
    """Met à jour un utilisateur"""
    try:
        user = Utilisateur.query.get_or_404(user_id)
        data = request.get_json()
        
        # Champs autorisés à la modification
        allowed_fields = ['nom', 'prenom', 'email', 'adresse', 'date_naissance', 
                         'lieu_naissance', 'role', 'photo_profil']
        
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        
        # Gestion spéciale du mot de passe
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        db.session.commit()
        
        return jsonify({
            "message": "Utilisateur mis à jour avec succès",
            "utilisateur": user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erreur lors de la mise à jour de l'utilisateur: {str(e)}"}), 500

@admin_bp.route('/utilisateurs/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_utilisateur(user_id):
    """Supprime un utilisateur"""
    try:
        user = Utilisateur.query.get_or_404(user_id)
        
        # Empêcher la suppression de soi-même
        current_user_email = get_jwt_identity()
        if user.email == current_user_email:
            return jsonify({"error": "Vous ne pouvez pas supprimer votre propre compte"}), 400
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({"message": "Utilisateur supprimé avec succès"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erreur lors de la suppression de l'utilisateur: {str(e)}"}), 500

# ============================================================================
# GESTION DES DAARAS
# ============================================================================

@admin_bp.route('/daaras', methods=['GET'])
@admin_required
def get_all_daaras():
    """Récupère tous les daaras"""
    try:
        daaras = Daara.query.all()
        return jsonify({
            "daaras": [daara.to_dict() for daara in daaras]
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la récupération des daaras: {str(e)}"}), 500

@admin_bp.route('/daaras', methods=['POST'])
@admin_required
def create_daara():
    """Crée un nouveau daara"""
    try:
        data = request.get_json()
        
        # Validation des champs requis
        required_fields = ['nom', 'lieu']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Le champ '{field}' est requis"}), 400
        
        daara = Daara(
            nom=data['nom'],
            lieu=data['lieu'],
            proprietaire=data.get('proprietaire'),
            nb_talibes=data.get('nb_talibes', 0),
            nb_enseignants=data.get('nb_enseignants', 0),
            nb_batiments=data.get('nb_batiments', 0)
        )
        
        db.session.add(daara)
        db.session.commit()
        
        return jsonify({
            "message": "Daara créé avec succès",
            "daara": daara.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erreur lors de la création du daara: {str(e)}"}), 500

@admin_bp.route('/daaras/<int:daara_id>', methods=['PUT'])
@admin_required
def update_daara(daara_id):
    """Met à jour un daara"""
    try:
        daara = Daara.query.get_or_404(daara_id)
        data = request.get_json()
        
        allowed_fields = ['nom', 'lieu', 'proprietaire', 'nb_talibes', 
                         'nb_enseignants', 'nb_batiments']
        
        for field in allowed_fields:
            if field in data:
                setattr(daara, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            "message": "Daara mis à jour avec succès",
            "daara": daara.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erreur lors de la mise à jour du daara: {str(e)}"}), 500

@admin_bp.route('/daaras/<int:daara_id>', methods=['DELETE'])
@admin_required
def delete_daara(daara_id):
    """Supprime un daara"""
    try:
        daara = Daara.query.get_or_404(daara_id)
        
        # Vérifier s'il y a des données associées
        if daara.talibes or daara.enseignants or daara.batiments:
            return jsonify({
                "error": "Impossible de supprimer ce daara car il contient des talibes, enseignants ou bâtiments"
            }), 400
        
        db.session.delete(daara)
        db.session.commit()
        
        return jsonify({"message": "Daara supprimé avec succès"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erreur lors de la suppression du daara: {str(e)}"}), 500

# ============================================================================
# GESTION DES BATIMENTS ET CHAMBRES
# ============================================================================

@admin_bp.route('/batiments', methods=['GET'])
@admin_required
def get_all_batiments():
    """Récupère tous les bâtiments"""
    try:
        batiments = Batiment.query.all()
        return jsonify({
            "batiments": [batiment.to_dict() for batiment in batiments]
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la récupération des bâtiments: {str(e)}"}), 500

@admin_bp.route('/chambres', methods=['GET'])
@admin_required
def get_all_chambres():
    """Récupère toutes les chambres"""
    try:
        chambres = Chambre.query.all()
        return jsonify({
            "chambres": [chambre.to_dict() for chambre in chambres]
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la récupération des chambres: {str(e)}"}), 500

# ============================================================================
# RAPPORTS ET EXPORT
# ============================================================================

@admin_bp.route('/rapports/talibes', methods=['GET'])
@admin_required
def rapport_talibes():
    """Génère un rapport des talibes"""
    try:
        # Talibes par daara avec détails
        talibes_par_daara = db.session.query(
            Daara.nom,
            db.func.count(Talibe.id).label('total'),
            db.func.avg(Talibe.age).label('age_moyen')
        ).outerjoin(Talibe).group_by(Daara.id).all()
        
        # Talibes par niveau
        talibes_par_niveau = db.session.query(
            Talibe.niveau,
            db.func.count(Talibe.id).label('total')
        ).group_by(Talibe.niveau).all()
        
        return jsonify({
            "talibes_par_daara": [
                {
                    "daara": daara,
                    "total": total,
                    "age_moyen": float(age_moyen) if age_moyen else 0
                }
                for daara, total, age_moyen in talibes_par_daara
            ],
            "talibes_par_niveau": [
                {
                    "niveau": niveau or "Non spécifié",
                    "total": total
                }
                for niveau, total in talibes_par_niveau
            ]
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la génération du rapport: {str(e)}"}), 500

@admin_bp.route('/rapports/enseignants', methods=['GET'])
@admin_required
def rapport_enseignants():
    """Génère un rapport des enseignants"""
    try:
        # Enseignants par daara
        enseignants_par_daara = db.session.query(
            Daara.nom,
            db.func.count(Enseignant.id).label('total')
        ).outerjoin(Enseignant).group_by(Daara.id).all()
        
        # Enseignants par spécialité
        enseignants_par_specialite = db.session.query(
            Enseignant.specialite,
            db.func.count(Enseignant.id).label('total')
        ).group_by(Enseignant.specialite).all()
        
        return jsonify({
            "enseignants_par_daara": [
                {
                    "daara": daara,
                    "total": total
                }
                for daara, total in enseignants_par_daara
            ],
            "enseignants_par_specialite": [
                {
                    "specialite": specialite or "Non spécifié",
                    "total": total
                }
                for specialite, total in enseignants_par_specialite
            ]
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la génération du rapport: {str(e)}"}), 500