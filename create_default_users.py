from app import create_app, db

app = create_app()
with app.app_context():
    print("🗑️  Suppression de toutes les tables...")
    db.drop_all()
    print("✅ Tables supprimées")
    
    print("🗄️  Création des nouvelles tables...")
    db.create_all()
    print("✅ Nouvelles tables créées")
    
    print("🎉 Base de données réinitialisée avec succès!")