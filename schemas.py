from marshmallow import Schema, fields, validate, validates, ValidationError
import re

class CoursSchema(Schema):
    id = fields.Int(dump_only=True)
    
    # Étape 1: Informations de base
    code = fields.Str(
        required=True,
        validate=[
            validate.Length(min=1, max=20),
            validate.Regexp(r'^[A-Z]{3}\d{3}$', error="Format invalide (ex: COR101)")
        ]
    )
    libelle = fields.Str(
        required=True,
        validate=validate.Length(min=5, max=200)
    )
    description = fields.Str(
        validate=validate.Length(max=500)
    )
    
    # Étape 2: Configuration
    categorie = fields.Str(
        required=True,
        validate=validate.OneOf([
            'Coran', 'Hadith', 'Fiqh', 'Tafsir', 
            'Langue Arabe', 'Sciences Islamiques', 'Autre'
        ])
    )
    niveau = fields.Str(
        required=True,
        validate=validate.OneOf([
            'Débutant', 'Intermédiaire', 'Avancé', 'Tous niveaux'
        ])
    )
    duree = fields.Int(
        required=True,
        validate=validate.Range(min=1, max=40)
    )
    capacite_max = fields.Int(
        required=True,
        validate=validate.Range(min=1)
    )
    prerequis = fields.Str(allow_none=True)
    is_active = fields.Bool(load_default=True)
    is_certificat = fields.Bool(load_default=False)
    is_online = fields.Bool(load_default=False)
    
    # Étape 3: Objectifs et contenu
    objectifs = fields.Str(allow_none=True)
    programme = fields.Str(allow_none=True)
    supports = fields.Str(allow_none=True)
    
    # Métadonnées
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class CoursCreateSchema(CoursSchema):
    pass

class CoursUpdateSchema(CoursSchema):
    code = fields.Str(required=False)  # Optionnel pour l'update