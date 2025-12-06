import os
import time  # AJOUT: Import manquant
from werkzeug.utils import secure_filename
from flask import request, jsonify, send_from_directory
from flask import Blueprint
from flask_jwt_extended import jwt_required
from models import Talibe

# Configuration upload
UPLOAD_FOLDER = 'uploads/profiles'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Créer le dossier uploads s'il n'existe pas
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# CORRECTION: Utiliser un préfixe cohérent pour le blueprint
upload_bp = Blueprint('upload', __name__, url_prefix='/api')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@upload_bp.route('/upload/photo', methods=['POST'])
@jwt_required()
def upload_photo():
    try:
        print("📤 Début de l'upload...")
        
        # CORRECTION: Vérifier les deux noms possibles
        file = None
        if 'photo' in request.files:
            file = request.files['photo']
        elif 'file' in request.files:  # Nom souvent utilisé par les clients
            file = request.files['file']
        
        if not file:
            print("❌ Aucun fichier trouvé (noms cherchés: 'photo', 'file')")
            print("📦 Fichiers reçus:", list(request.files.keys()))  # Debug
            return jsonify({'error': 'Aucun fichier'}), 400
        
        print(f"📄 Fichier reçu: {file.filename} (via champ: {file.name if hasattr(file, 'name') else 'unknown'})")
        
        if file.filename == '':
            print("❌ Nom de fichier vide")
            return jsonify({'error': 'Aucun fichier sélectionné'}), 400
        
        # Vérifier le type de fichier
        if not allowed_file(file.filename):
            print(f"❌ Type de fichier non autorisé: {file.filename}")
            return jsonify({'error': 'Type de fichier non autorisé. Utilisez JPG, JPEG ou PNG'}), 400
        
        # Vérifier la taille
        file.seek(0, os.SEEK_END)
        file_length = file.tell()
        file.seek(0)  # Remettre le curseur au début
        
        print(f"📏 Taille du fichier: {file_length} bytes")
        
        if file_length > MAX_FILE_SIZE:
            print(f"❌ Fichier trop volumineux: {file_length} > {MAX_FILE_SIZE}")
            return jsonify({'error': 'Fichier trop volumineux. Maximum 5MB'}), 400
        
        # Créer le dossier s'il n'existe pas
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Générer un nom de fichier sécurisé et unique
        filename = secure_filename(file.filename)
        unique_filename = f"{int(time.time())}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        print(f"💾 Sauvegarde vers: {file_path}")
        
        # Sauvegarder le fichier
        file.save(file_path)
        
        # Vérifier que le fichier a été sauvegardé
        if not os.path.exists(file_path):
            print("❌ Échec de la sauvegarde du fichier")
            return jsonify({'error': 'Erreur lors de la sauvegarde'}), 500
        
        file_size = os.path.getsize(file_path)
        print(f"✅ Fichier sauvegardé: {file_size} bytes - {unique_filename}")
        
        # URL pour accéder au fichier
        photo_url = f"http://localhost:5000/api/uploads/{unique_filename}"
        
        return jsonify({
            'url': photo_url,
            'filename': unique_filename,
            'size': file_length
        }), 200
        
    except Exception as e:
        print(f"💥 Erreur lors de l'upload: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Erreur serveur: {str(e)}'}), 500

# CORRECTION: Cette route doit être dans le même blueprint
@upload_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    try:
        print(f"📥 Demande de fichier: {filename}")  # Debug
        return send_from_directory(UPLOAD_FOLDER, filename)
    except FileNotFoundError:
        print(f"❌ Fichier non trouvé: {filename}")  # Debug
        return jsonify({'error': 'Fichier non trouvé'}), 404

@upload_bp.route('/upload/photo/<filename>', methods=['DELETE'])
@jwt_required()
def delete_photo(filename):
    try:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'message': 'Photo supprimée'}), 200
        else:
            return jsonify({'error': 'Fichier non trouvé'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@upload_bp.route('/cleanup-orphaned', methods=['POST'])
def cleanup_orphaned_photos():
    """Supprimer les photos qui ne sont pas référencées dans la BD"""
    try:
        # Photos référencées en BD
        talibes_avec_photos = Talibe.query.filter(Talibe.photo_profil.isnot(None)).all()
        photos_referencees = {t.photo_profil for t in talibes_avec_photos}
        
        # Photos sur le disque
        if os.path.exists(UPLOAD_FOLDER):
            photos_disque = set(os.listdir(UPLOAD_FOLDER))
            photos_orphelines = photos_disque - photos_referencees
            
            # Supprimer les orphelines
            for photo in photos_orphelines:
                photo_path = os.path.join(UPLOAD_FOLDER, photo)
                os.remove(photo_path)
                print(f"🗑️ Photo orpheline supprimée: {photo}")
            
            return jsonify({
                'photos_referencees': len(photos_referencees),
                'photos_disque': len(photos_disque),
                'photos_orphelines_supprimees': len(photos_orphelines),
                'liste_orphelines': list(photos_orphelines)
            })
        
        return jsonify({'message': 'Aucune photo orpheline'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500