from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import enum
from datetime import datetime, timezone

# Créer l'instance SQLAlchemy SANS l'initialiser immédiatement
db = SQLAlchemy()

class RoleEnum(enum.Enum):
    ADMIN = "ADMIN"
    ENSEIGNANT = "ENSEIGNANT"
    TALIBE = "TALIBE"

class EtatCivilEnum(enum.Enum):
    CELIBATAIRE = "CELIBATAIRE"
    MARIE = "MARIE"
    DIVORCE = "DIVORCE" 
    VEUF = "VEUF"
    

class CoursCategorie(enum.Enum):
  CORAN = 'Coran',
  HADITH = 'Hadith',
  FIQH = 'Fiqh',
  TAFSIR = 'Tafsir',
  LANGUE_ARABE = 'Langue Arabe',
  SCIENCES_ISLAMIQUES = 'Sciences Islamiques',
  AUTRE = 'Autre'


class CoursNiveau (enum.Enum):
  DEBUTANT = 'Débutant',
  INTERMEDIAIRE = 'Intermédiaire',
  AVANCE = 'Avancé',
  TOUS_NIVEAUX = 'Tous niveaux'

class CoursPrerequis(enum.Enum):
  AUCUN = "",
  ALPHABETISATION_ARABE = 'Alphabétisation arabe',
  NIVEAU_PRECEDENT = 'Niveau précédent validé',
  AUTORISATION_ENSEIGNANT = 'Autorisation enseignant'


class Utilisateur(db.Model):
    __tablename__ = 'utilisateurs'
    
    id = db.Column(db.Integer, primary_key=True)
    matricule = db.Column(db.String(20), unique=True, nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    adresse = db.Column(db.Text)
    date_naissance = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    lieu_naissance = db.Column(db.String(100), nullable=False)
    # SUPPRIMER les colonnes age et nb_annees - on les calcule dynamiquement
    date_entree = db.Column(db.Date, default=datetime.utcnow)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(RoleEnum), nullable=False)
    photo_profil = db.Column(db.String(255))
    type = db.Column(db.String(20))
    sexe = db.Column(db.String(20))
    nationalite = db.Column(db.String(20))
    
    __mapper_args__ = {
        'polymorphic_identity': 'utilisateur',
        'polymorphic_on': type
    }
    
    def __init__(self, **kwargs):
        if 'type' not in kwargs:
            kwargs['type'] = 'utilisateur'
        super().__init__(**kwargs)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def age(self):
        """Calcule l'âge dynamiquement à chaque appel"""
        if self.date_naissance:
            today = datetime.now().date()
            return today.year - self.date_naissance.year - (
                (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day)
            )
        return None
    
    @property
    def nb_annees(self):
        """Calcule le nombre d'années dynamiquement à chaque appel"""
        if self.date_entree:
            today = datetime.now().date()
            return today.year - self.date_entree.year - (
                (today.month, today.day) < (self.date_entree.month, self.date_entree.day)
            )
        return None
    
    def to_dict(self):
        return {
            'id': self.id,
            'matricule': self.matricule,
            'nom': self.nom,
            'prenom': self.prenom,
            'adresse': self.adresse,
            'date_naissance': self.date_naissance.isoformat() if self.date_naissance else None,
            'lieu_naissance': self.lieu_naissance,
            'age': self.age,  # Appel dynamique de la property
            'date_entree': self.date_entree.isoformat() if self.date_entree else None,
            'nb_annees': self.nb_annees,  # Appel dynamique de la property
            'email': self.email,
            'sexe': self.sexe,
            'nationalite': self.nationalite,
            'role': self.role.value,
            'photo_profil': self.photo_profil,
            'type': self.type,
            'photo_profil_url': f'https://gestiondaaras-2.onrender.com/api/uploads/{self.photo_profil}' if self.photo_profil else None
        }
        
class Talibe(Utilisateur):
    __tablename__ = 'talibes'
    
    id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), primary_key=True)
    pere = db.Column(db.String(100))
    mere = db.Column(db.String(100))
    niveau = db.Column(db.String(50))
    extrait_naissance = db.Column(db.Boolean, default=False)
    
    daara_id = db.Column(db.Integer, db.ForeignKey('daaras.id'))
    chambre_id = db.Column(db.Integer, db.ForeignKey('chambres.id'))
    
    cours = db.relationship(
        'Cours', 
        secondary='inscriptions',
        backref=db.backref('talibes_inscrits', lazy=True),
        viewonly=True  # Important pour éviter les conflits
    )
    
    __mapper_args__ = {
        'polymorphic_identity': 'talibe',
    }
    
    @property
    def cours_inscrits(self):
        return [inscription.cours for inscription in self.inscriptions_assoc]
    
    def __init__(self, **kwargs):
        kwargs['type'] = 'talibe'
        super().__init__(**kwargs)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'pere': self.pere,
            'mere': self.mere,
            'niveau': self.niveau,
            'extrait_naissance': self.extrait_naissance,
            'daara_id': self.daara_id,
            'chambre_id': self.chambre_id,
            'cours': [cours.to_dict() for cours in self.cours] if self.cours else []
        })
        return data

class Enseignant(Utilisateur):
    __tablename__ = 'enseignants'
    
    id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), primary_key=True)
    specialite = db.Column(db.String(100))
    telephone = db.Column(db.String(20))
    etat_civil = db.Column(db.Enum(EtatCivilEnum))
    grade = db.Column(db.String(50))
    diplome = db.Column(db.String(50))
    diplome_origine = db.Column(db.String(50))
    statut = db.Column(db.String(50))
    
    daara_id = db.Column(db.Integer, db.ForeignKey('daaras.id'))
    
    cours = db.relationship('Cours', secondary='enseignant_cours', back_populates='enseignants')
    
    __mapper_args__ = {
        'polymorphic_identity': 'enseignant',
    }
    
    def __init__(self, **kwargs):
        kwargs['type'] = 'enseignant'
        super().__init__(**kwargs)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'specialite': self.specialite,
            'telephone': self.telephone,
            'etat_civil': self.etat_civil.value if self.etat_civil else None,
            'grade': self.grade,
            'diplome': self.diplome,
            'diplome_origine' :self.diplome_origine,
            'statut' : self.statut,
            'nationalite': self.nationalite,
            'daara_id': self.daara_id,
            'cours': [cours.to_dict() for cours in self.cours] if self.cours else []
        })
        return data

# CORRECTION: Ajouter la classe Admin
class Admin(Utilisateur):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), primary_key=True)
    niveau_acces = db.Column(db.String(50), default='complet')
    
    __mapper_args__ = {
        'polymorphic_identity': 'admin',
    }
    
    def __init__(self, **kwargs):
        kwargs['type'] = 'admin'
        super().__init__(**kwargs)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'niveau_acces': self.niveau_acces
        })
        return data

# ... le reste de vos modèles (Daara, Batiment, etc.) reste inchangé ...

class Daara(db.Model):
    __tablename__ = 'daaras'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    proprietaire = db.Column(db.String(100))
    nb_talibes = db.Column(db.Integer, default=0)
    nb_enseignants = db.Column(db.Integer, default=0)
    lieu = db.Column(db.String(100))
    nb_batiments = db.Column(db.Integer, default=0)
    
    talibes = db.relationship('Talibe', backref='daara', lazy=True)
    enseignants = db.relationship('Enseignant', backref='daara', lazy=True)
    batiments = db.relationship('Batiment', backref='daara', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nom': self.nom,
            'proprietaire': self.proprietaire,
            'nb_talibes': self.nb_talibes,
            'nb_enseignants': self.nb_enseignants,
            'lieu': self.lieu,
            'nb_batiments': self.nb_batiments
        }

# Tables d'association (conservées telles quelles)
talibe_cours = db.Table('talibe_cours',
    db.Column('talibe_id', db.Integer, db.ForeignKey('talibes.id'), primary_key=True),
    db.Column('cours_id', db.Integer, db.ForeignKey('cours.id'), primary_key=True)
)

enseignant_cours = db.Table('enseignant_cours',
    db.Column('enseignant_id', db.Integer, db.ForeignKey('enseignants.id'), primary_key=True),
    db.Column('cours_id', db.Integer, db.ForeignKey('cours.id'), primary_key=True),
    db.Column('role', db.String(50), default='titulaire'),  # ⬅️ Ajouter un rôle
    db.Column('date_assignation', db.DateTime, default=datetime.utcnow)
)

class Cours(db.Model):
    __tablename__ = 'cours'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Étape 1: Informations de base (champs existants + nouveaux)
    code = db.Column(db.String(20), unique=True, nullable=False)
    libelle = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)  # Nouveau champ
    
    # Étape 2: Configuration (nouveaux champs)
    categorie = db.Column(db.String(50), nullable=False, default='Coran')
    niveau = db.Column(db.String(20), nullable=False, default='Débutant')
    duree = db.Column(db.Integer, nullable=False, default=2)  # heures/semaine
    capacite_max = db.Column(db.Integer, nullable=False, default=20)
    prerequis = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_certificat = db.Column(db.Boolean, default=False)
    is_online = db.Column(db.Boolean, default=False)
    
    # Étape 3: Objectifs et contenu (nouveaux champs)
    objectifs = db.Column(db.Text)
    programme = db.Column(db.Text)
    supports = db.Column(db.String(255))
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations existantes (conservées)
    enseignants = db.relationship('Enseignant', secondary=enseignant_cours, back_populates='cours')
    
    def __init__(self, **kwargs):
        super(Cours, self).__init__(**kwargs)
        # Générer un code si non fourni
        if not self.code and self.libelle:
            self.generate_code_suggestion()
            
    @property
    def talibes_inscrites(self):
        """Retourne la liste des talibes inscrits à ce cours"""
        return [inscription.talibe for inscription in self.inscriptions]
    
    def generate_code_suggestion(self):
        """Génère une suggestion de code basée sur le libellé"""
        if self.libelle and len(self.libelle) >= 3:
            prefix = self.libelle[:3].upper()
            # Vérifier si le code existe déjà
            existing = Cours.query.filter(Cours.code.like(f"{prefix}%")).count()
            self.code = f"{prefix}{101 + existing}"
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire pour JSON"""
        return {
            'id': self.id,
            'code': self.code,
            'libelle': self.libelle,
            'description': self.description,
            'categorie': self.categorie,
            'niveau': self.niveau,
            'duree': self.duree,
            'capacite_max': self.capacite_max,
            'prerequis': self.prerequis,
            'is_active': self.is_active,
            'is_certificat': self.is_certificat,
            'is_online': self.is_online,
            'objectifs': self.objectifs,
            'programme': self.programme,
            'supports': self.supports,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            # Informations sur les relations
            'nombre_talibes': len(self.talibes_inscrites),
            'nombre_enseignants': len(self.enseignants)
        }
    
    def update_from_dict(self, data):
        """Met à jour l'objet à partir d'un dictionnaire"""
        for key, value in data.items():
            if hasattr(self, key) and key not in ['id', 'created_at', 'updated_at']:
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
    
    def get_icon(self):
        """Retourne l'icône selon la catégorie"""
        icons = {
            'Coran': 'menu_book',
            'Hadith': 'history_edu',
            'Fiqh': 'gavel',
            'Tafsir': 'auto_stories',
            'Langue Arabe': 'translate',
            'Sciences Islamiques': 'school',
            'Autre': 'more_horiz'
        }
        return icons.get(self.categorie, 'book')
    
    def get_niveau_color(self):
        """Retourne la couleur selon le niveau"""
        colors = {
            'Débutant': 'primary',
            'Intermédiaire': 'accent',
            'Avancé': 'warn',
            'Tous niveaux': 'basic'
        }
        return colors.get(self.niveau, 'basic')
    
    def __repr__(self):
        return f'<Cours {self.code}: {self.libelle}>'

class Batiment(db.Model):
    __tablename__ = 'batiments'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    nb_chambres = db.Column(db.Integer, default=0)
    
    daara_id = db.Column(db.Integer, db.ForeignKey('daaras.id'))
    chambres = db.relationship('Chambre', backref='batiment', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nom': self.nom,
            'nb_chambres': self.nb_chambres,
            'daara_id': self.daara_id
        }

class Chambre(db.Model):
    __tablename__ = 'chambres'
    
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), nullable=False)
    nb_lits = db.Column(db.Integer, default=0)
    
    batiment_id = db.Column(db.Integer, db.ForeignKey('batiments.id'))
    talibes = db.relationship('Talibe', backref='chambre', lazy=True)
    lits = db.relationship('Lit', backref='chambre', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'numero': self.numero,
            'nb_lits': self.nb_lits,
            'batiment_id': self.batiment_id
        }

class Lit(db.Model):
    __tablename__ = 'lits'
    
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), nullable=False)
    
    chambre_id = db.Column(db.Integer, db.ForeignKey('chambres.id'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'numero': self.numero,
            'chambre_id': self.chambre_id
        }
        

class Inscription(db.Model):
    __tablename__ = 'inscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    talibe_id = db.Column(db.Integer, db.ForeignKey('talibes.id'), nullable=False)
    cours_id = db.Column(db.Integer, db.ForeignKey('cours.id'), nullable=False)
    date_inscription = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    note = db.Column(db.Float, nullable=True)
    
    # Relations
    talibe = db.relationship('Talibe', backref=db.backref('inscriptions', lazy=True, cascade='all, delete-orphan'))
    cours = db.relationship('Cours', backref=db.backref('inscriptions', lazy=True, cascade='all, delete-orphan'))
    
    # Contrainte d'unicité
    __table_args__ = (db.UniqueConstraint('talibe_id', 'cours_id', name='unique_inscription'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'talibe_id': self.talibe_id,
            'cours_id': self.cours_id,
            'date_inscription': self.date_inscription.isoformat() if self.date_inscription else None,
            'note': self.note,
            'talibe_nom': f"{self.talibe.prenom} {self.talibe.nom}" if self.talibe else None,
            'cours_libelle': self.cours.libelle if self.cours else None,
            'cours_code': self.cours.code if self.cours else None
        }
    
    def __repr__(self):
        return f'<Inscription Talibe:{self.talibe_id} Cours:{self.cours_id}>'