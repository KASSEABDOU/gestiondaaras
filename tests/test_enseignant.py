# backend/tests/test_enseignant_simple.py
import pytest
import json
from datetime import date
from backend.models import db, Enseignant, Utilisateur, Cours, RoleEnum, EtatCivilEnum

def test_enseignant_creation_basique(app):
    """Test création basique d'un enseignant"""
    with app.app_context():
        # Créer enseignant directement sans nettoyage préalable
        enseignant = Enseignant(
            matricule="ENS_SIMPLE",
            nom="Simple",
            prenom="Test",
            email="simple_test@example.com",
            role=RoleEnum.ENSEIGNANT,  # CORRECTION: Utiliser l'objet Enum directement
            specialite="Test",
            grade="Testeur",
            date_naissance=date(1980, 1, 1),
            lieu_naissance="Dakar",
            date_entree=date.today()
        )
        enseignant.set_password("123456")
        
        db.session.add(enseignant)
        db.session.commit()
        
        # Vérifications basiques
        assert enseignant.id is not None
        assert enseignant.matricule == "ENS_SIMPLE"
        assert enseignant.specialite == "Test"
        assert enseignant.role == RoleEnum.ENSEIGNANT  # CORRECTION: Comparer avec l'objet Enum
        
        print("✅ Enseignant créé avec succès")

def test_enseignant_to_dict_basique(app):
    """Test de la méthode to_dict()"""
    with app.app_context():
        enseignant = Enseignant(
            matricule="ENS_DICT",
            nom="Dict",
            prenom="Test",
            email="dict_test@example.com",
            role=RoleEnum.ENSEIGNANT,  # CORRECTION: Utiliser l'objet Enum
            specialite="Informatique",
            telephone="771234567",
            etat_civil=EtatCivilEnum.CELIBATAIRE.value,  # CORRECTION: Utiliser une valeur valide pour l'Enum
            grade="Professeur",
            date_naissance=date(1980, 5, 15),
            lieu_naissance="Saint-Louis",
            date_entree=date(2020, 9, 1)
        )
        enseignant.set_password("123456")
        
        db.session.add(enseignant)
        db.session.commit()
        
        data = enseignant.to_dict()
        
        # Vérifier les champs de base
        assert data['matricule'] == "ENS_DICT"
        assert data['nom'] == "Dict"
        assert data['prenom'] == "Test"
        assert data['email'] == "dict_test@example.com"
        assert data['role'] == "ENSEIGNANT"  # Dans to_dict(), l'Enum est converti en string
        
        print("✅ Méthode to_dict() fonctionne")

def test_enseignant_password(app):
    """Test du système de mot de passe"""
    with app.app_context():
        enseignant = Enseignant(
            matricule="ENS_PASS",
            nom="Password",
            prenom="Test",
            email="pass_test@example.com",
            role=RoleEnum.ENSEIGNANT,  # CORRECTION
            specialite="Test",
            date_naissance=date(1980, 1, 1),
            lieu_naissance="Dakar",
            date_entree=date.today()
        )
        enseignant.set_password("123456")
        
        db.session.add(enseignant)
        db.session.commit()
        
        # Vérifier que le mot de passe est hashé
        assert enseignant.password_hash is not None
        assert enseignant.password_hash != "123456"
        
        # Vérifier que la vérification fonctionne
        assert enseignant.check_password("123456") == True
        assert enseignant.check_password("wrongpassword") == False
        
        print("✅ Système de mot de passe fonctionne")

def test_enseignant_inheritance(app):
    """Test que l'héritage fonctionne correctement"""
    with app.app_context():
        enseignant = Enseignant(
            matricule="ENS_HERITAGE",
            nom="Heritage",
            prenom="Test",
            email="heritage_test@example.com",
            role=RoleEnum.ENSEIGNANT,  # CORRECTION
            specialite="Test",
            date_naissance=date(1980, 1, 1),
            lieu_naissance="Dakar",
            date_entree=date.today()
        )
        enseignant.set_password("123456")
        
        db.session.add(enseignant)
        db.session.commit()
        
        # Vérifier que c'est bien une instance d'Enseignant
        assert isinstance(enseignant, Enseignant)
        
        # Vérifier les champs hérités
        assert hasattr(enseignant, 'matricule')
        assert hasattr(enseignant, 'nom')
        assert hasattr(enseignant, 'prenom')
        assert hasattr(enseignant, 'email')
        
        # Vérifier les champs spécifiques
        assert hasattr(enseignant, 'specialite')
        assert hasattr(enseignant, 'telephone')
        assert hasattr(enseignant, 'etat_civil')
        assert hasattr(enseignant, 'grade')
        
        print("✅ Héritage enseignant fonctionne")

def test_enseignant_update(app):
    """Test de mise à jour d'un enseignant"""
    with app.app_context():
        # Créer enseignant
        enseignant = Enseignant(
            matricule="ENS_UPDATE",
            nom="Update",
            prenom="Test",
            email="update_test@example.com",
            role=RoleEnum.ENSEIGNANT,  # CORRECTION
            specialite="Original",
            grade="Original",
            date_naissance=date(1980, 1, 1),
            lieu_naissance="Dakar",
            date_entree=date.today()
        )
        enseignant.set_password("123456")
        
        db.session.add(enseignant)
        db.session.commit()
        
        original_id = enseignant.id
        
        # Modifier les champs
        enseignant.specialite = "Nouvelle Spécialité"
        enseignant.grade = "Nouveau Grade"
        enseignant.telephone = "778765432"
        
        db.session.commit()
        
        # Recharger depuis la base
        from sqlalchemy.orm import Session
        session = Session.object_session(enseignant)
        enseignant_updated = session.get(Enseignant, original_id)  # CORRECTION: Utiliser session.get()
        
        # Vérifier les modifications
        assert enseignant_updated.specialite == "Nouvelle Spécialité"
        assert enseignant_updated.grade == "Nouveau Grade"
        assert enseignant_updated.telephone == "778765432"
        
        print("✅ Mise à jour enseignant fonctionne")

def test_enseignant_avec_cours(app):
    """Test relation enseignant-cours"""
    with app.app_context():
        # Créer enseignant
        enseignant = Enseignant(
            matricule="ENS_COURS",
            nom="Cours",
            prenom="Test",
            email="cours_test@example.com",
            role=RoleEnum.ENSEIGNANT,  # CORRECTION
            specialite="Test",
            date_naissance=date(1980, 1, 1),
            lieu_naissance="Dakar",
            date_entree=date.today()
        )
        enseignant.set_password("123456")
        
        # Créer cours
        cours1 = Cours(code="COURS1", libelle="Cours Test 1")
        cours2 = Cours(code="COURS2", libelle="Cours Test 2")
        
        db.session.add(enseignant)
        db.session.add(cours1)
        db.session.add(cours2)
        db.session.commit()
        
        # Associer les cours à l'enseignant
        enseignant.cours.append(cours1)
        enseignant.cours.append(cours2)
        db.session.commit()
        
        # Vérifier la relation
        assert len(enseignant.cours) == 2
        assert cours1 in enseignant.cours
        assert cours2 in enseignant.cours
        
        # Vérifier depuis la base
        from sqlalchemy.orm import Session
        session = Session.object_session(enseignant)
        enseignant_db = session.get(Enseignant, enseignant.id)  # CORRECTION
        
        assert len(enseignant_db.cours) == 2
        
        print("✅ Relation enseignant-cours fonctionne")

def test_enseignant_statistiques_simples(app):
    """Test des statistiques simples"""
    with app.app_context():
        # Compter les enseignants existants
        total_avant = Enseignant.query.count()
        
        # Créer un nouvel enseignant
        enseignant = Enseignant(
            matricule="ENS_STATS",
            nom="Stats",
            prenom="Test",
            email="stats_test@example.com",
            role=RoleEnum.ENSEIGNANT,  # CORRECTION
            specialite="Test",
            date_naissance=date(1980, 1, 1),
            lieu_naissance="Dakar",
            date_entree=date.today()
        )
        enseignant.set_password("123456")
        
        db.session.add(enseignant)
        db.session.commit()
        
        # Vérifier le comptage
        total_apres = Enseignant.query.count()
        assert total_apres == total_avant + 1
        
        print(f"✅ Statistiques simples: {total_avant} -> {total_apres} enseignants")