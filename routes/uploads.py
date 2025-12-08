import cloudinary
import cloudinary.uploader
from flask import request, jsonify, Blueprint
from flask_jwt_extended import jwt_required
from models import Talibe, db
import traceback
import os

# Configurer Cloudinary (à mettre dans config ou variables d'environnement)
cloudinary.config(
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key = os.environ.get("CLOUDINARY_API_KEY"),
    api_secret = os.environ.get("CLOUDINARY_API_SECRET"),
    secure = True
)

# Blueprint
upload_bp = Blueprint('upload', __name__, url_prefix='/api')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Upload générique ---
@upload_bp.route('/upload/photo', methods=['POST'])
@jwt_required()
def upload_photo():
    try:
        file = request.files.get('photo') or request.files.get('file')
        if not file or file.filename == '':
            return jsonify({'error': 'Aucun fichier sélectionné'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Type de fichier non autorisé'}), 400

        # Vérifier la taille
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        if size > MAX_FILE_SIZE:
            return jsonify({'error': 'Fichier trop volumineux'}), 400

        # Upload Cloudinary
        result = cloudinary.uploader.upload(
            file,
            folder="profiles",
            resource_type="image",
            overwrite=True
        )

        return jsonify({
            'url': result.get('secure_url'),
            'public_id': result.get('public_id'),
            'size': size
        }), 200

    except Exception as e:
        traceback.print_exc()  # affichera le détail dans les logs Render
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
        


# --- Upload pour un Talibe spécifique ---
@upload_bp.route('/upload/photo/<int:talibe_id>', methods=['POST'])
@jwt_required()
def upload_photo_for_talibe(talibe_id):
    try:
        talibe = Talibe.query.get(talibe_id)
        if not talibe:
            return jsonify({'error': 'Talibe introuvable'}), 404

        file = request.files.get('photo') or request.files.get('file')
        if not file or file.filename == '':
            return jsonify({'error': 'Aucun fichier sélectionné'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Type de fichier non autorisé'}), 400

        # Vérifier taille
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        if size > MAX_FILE_SIZE:
            return jsonify({'error': 'Fichier trop volumineux'}), 400

        # Supprimer ancienne photo si existante
        if talibe.photo_profil:
            cloudinary.uploader.destroy(talibe.photo_profil, resource_type="image")

        # Upload
        result = cloudinary.uploader.upload(
            file,
            folder="profiles",
            resource_type="image",
            overwrite=True
        )

        # Mettre à jour Talibe
        talibe.photo_profil = result.get('public_id')
        db.session.commit()

        return jsonify({
            'url': result.get('secure_url'),
            'public_id': result.get('public_id'),
            'size': size
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# --- Supprimer photo ---
@upload_bp.route('/upload/photo/<int:talibe_id>', methods=['DELETE'])
@jwt_required()
def delete_photo_for_talibe(talibe_id):
    try:
        talibe = Talibe.query.get(talibe_id)
        if not talibe:
            return jsonify({'error': 'Talibe introuvable'}), 404

        if talibe.photo_profil:
            cloudinary.uploader.destroy(talibe.photo_profil, resource_type="image")
            talibe.photo_profil = None
            db.session.commit()
            return jsonify({'message': 'Photo supprimée'}), 200
        else:
            return jsonify({'error': 'Aucune photo à supprimer'}), 404

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# --- Nettoyer photos orphelines ---
@upload_bp.route('/cleanup-orphaned', methods=['POST'])
def cleanup_orphaned_photos():
    """Supprimer les photos Cloudinary non référencées en BD"""
    try:
        talibes = Talibe.query.filter(Talibe.photo_profil.isnot(None)).all()
        photos_referencees = {t.photo_profil for t in talibes}

        # Récupérer tous les fichiers dans Cloudinary (dossier profiles)
        resources = cloudinary.Search().expression("folder:profiles").execute()
        all_public_ids = {r['public_id'] for r in resources.get('resources', [])}

        orphelines = all_public_ids - photos_referencees

        for public_id in orphelines:
            cloudinary.uploader.destroy(public_id, resource_type="image")

        return jsonify({
            'photos_referencees': len(photos_referencees),
            'photos_orphelines_supprimees': len(orphelines),
            'liste_orphelines': list(orphelines)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
