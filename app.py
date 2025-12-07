from flask import Flask, jsonify
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
import os
from flask_cors import CORS
from werkzeug.security import generate_password_hash
from datetime import datetime
from models import Cours, Talibe, Enseignant, Daara, Batiment, db, RoleEnum,Admin
from config import Config

# ✅ Initialiser JWTManager en dehors de la fonction create_app
jwt = JWTManager()

def create_app(testing=False):
    app = Flask(__name__)
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:4200",  # Dev
                "https://frontend-seven-nu-b1bl62wjh8.vercel.app",  # Votre frontend
                "https://*.vercel.app",  # Tous Vercel
                "https://vercel.app",  # Domaine principal
                "*"  # En dernier recours, toutes les origines
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            "allow_headers": [
                "Content-Type",
                "Authorization", 
                "Accept",
                "Origin",
                "X-Requested-With",
                "X-CSRF-Token",
                "Access-Control-Allow-Origin"
            ],
            "expose_headers": ["Content-Type", "Authorization", "Content-Length"],
            "supports_credentials": True,
            "max_age": 3600
        }
    })  # autorise ton frontend

    if testing:
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['JWT_SECRET_KEY'] = 'test-secret-key'
        app.config['SECRET_KEY'] = 'test-secret-key'
    else:
        app.config.from_object(Config)
    
    # Initialisation de SQLAlchemy AVANT tout import de modèle
    db.init_app(app)
    
    # ✅ Initialiser JWT avec l'application
    jwt.init_app(app)
    Migrate(app, db)
    
    # Configurer les handlers d'erreur JWT
    @jwt.unauthorized_loader
    def unauthorized_callback(callback):
        return jsonify({
            "error": "Token manquant ou invalide",
            "message": "L'authentification est requise"
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(callback):
        return jsonify({
            "error": "Token invalide",
            "message": "Le token fourni est invalide"
        }), 401
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            "error": "Token expiré",
            "message": "Le token a expiré, veuillez vous reconnecter"
        }), 401
    
    # Maintenant importer les blueprints (qui utilisent les modèles)
    from routes.auth import auth_bp
    from routes.daara import daara_bp
    from routes.talibe import talibe_bp
    from routes.enseignant import enseignant_bp
    from routes.cours import cours_bp
    from routes.batiment import batiment_bp
    from routes.chambre import chambre_bp
    from routes.lit import lit_bp
    from routes.inscription import inscription_bp
    from routes.admin import admin_bp
    from routes.uploads import upload_bp
    
    # Enregistrement des blueprints
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(daara_bp, url_prefix='/api')
    app.register_blueprint(talibe_bp, url_prefix='/api')
    app.register_blueprint(enseignant_bp, url_prefix='/api')
    app.register_blueprint(cours_bp, url_prefix='/api')
    app.register_blueprint(batiment_bp, url_prefix='/api')
    app.register_blueprint(chambre_bp, url_prefix='/api')
    app.register_blueprint(lit_bp, url_prefix='/api')
    app.register_blueprint(inscription_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(upload_bp, url_prefix='/api')
    
    # Gestion des erreurs
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Ressource non trouvée'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Erreur interne du serveur'}), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Requête mal formée'}), 400
    
    # Route de base
    @app.route('/')
    def home():
        return jsonify({
            "message": "Flask API is running!",
            "status": "success",
            "endpoints": {
                "health": "/api/health",
                "docs": "/api/docs"
            }
        })

    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            "status": "healthy",
            "service": "Flask API",
            "timestamp": "2024-01-01T00:00:00Z",  # Vous pouvez utiliser datetime
            "environment": os.environ.get('FLASK_ENV', 'development')
             
        })

    @app.route('/api/docs', methods=['GET'])
    def api_docs():
        return jsonify({
            "endpoints": [
                {"path": "/api/health", "method": "GET", "description": "Health check"},
                {"path": "/api/data", "method": "GET", "description": "Get all data"},
                {"path": "/api/data/<id>", "method": "GET", "description": "Get specific data"}
            ]
        })
        
    # Dans votre fichier routes (app.py ou talibe_routes.py)
    
    return app
    
    

def create_default_users():
    """Crée les utilisateurs par défaut s'ils n'existent pas"""
    try:
        print("🔍 Vérification des utilisateurs par défaut...")
        
        # Liste des utilisateurs par défaut à créer
        default_users = [
            {
                "class": Admin,
                "matricule": "ADMIN001",
                "nom": "Admin",
                "prenom": "System", 
                "email": "admin@daara.com",
                "password": "admin123",
                "role": RoleEnum.ADMIN,
                "lieu_naissance": "Dakar",
                "description": "👑 Administrateur système"
            },
            {
                "class": Admin,
                "matricule": "ADMIN002", 
                "nom": "Kane",
                "prenom": "Mamadou",
                "email": "mkane@daara.com", 
                "password": "admin456",
                "role": RoleEnum.ADMIN,
                "lieu_naissance": "Thiès",
                "description": "👑 Administrateur principal"
            },
            {
                "class": Enseignant,
                "matricule": "ENS001",
                "nom": "Diallo", 
                "prenom": "Moussa",
                "email": "enseignant@daara.com",
                "password": "enseignant123", 
                "role": RoleEnum.ENSEIGNANT,
                "lieu_naissance": "Touba",
                "description": "👨‍🏫 Enseignant coranique"
            },
            {
                "class": Talibe,
                "matricule": "TAL001",
                "nom": "Ndiaye",
                "prenom": "Ibrahima",
                "email": "talibe@daara.com",
                "password": "talibe123", 
                "role": RoleEnum.TALIBE,
                "lieu_naissance": "Saint-Louis", 
                "description": "👦 Talibé"
            }
        ]
        
        users_created = []
        
        for user_data in default_users:
            # Vérifier si l'utilisateur existe déjà
            existing_user = user_data["class"].query.filter_by(email=user_data["email"]).first()
            
            if not existing_user:
                # Créer l'utilisateur avec la bonne classe
                user = user_data["class"](
                    matricule=user_data["matricule"],
                    nom=user_data["nom"],
                    prenom=user_data["prenom"],
                    email=user_data["email"],
                    role=user_data["role"],
                    date_naissance=datetime.now().date(),
                    lieu_naissance=user_data["lieu_naissance"],
                    date_entree=datetime.now().date()
                )
                # Utiliser set_password pour hasher correctement le mot de passe
                user.set_password(user_data["password"])
                
                db.session.add(user)
                users_created.append(user_data["description"])
                print(f"✅ {user_data['description']} créé")
        
        if users_created:
            db.session.commit()
            print(f"🎉 {len(users_created)} utilisateur(s) par défaut créé(s)")
        else:
            print("ℹ️  Tous les utilisateurs par défaut existent déjà")
            
    except Exception as e:
        db.session.rollback()
        print(f"⚠️  Attention: Impossible de créer les utilisateurs par défaut: {e}")
        import traceback
        traceback.print_exc()
        
# ... tout ton code au-dessus ...

app = create_app()  # ← Ajouter ceci ici

        


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
        create_default_users()
        # Render fournit un port automatiquement → on doit l'utiliser
    port = int(os.environ.get('PORT', 5000))

    app.run(
        host="0.0.0.0",   # Obligatoire pour être accessible sur Render
        port=port,        # On utilise le port fourni
        debug=False       # Render n'aime pas debug=True
    )