from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import jsonify
from models import Utilisateur

def role_required(required_role):
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            try:
                user_email = get_jwt_identity()
                user = Utilisateur.query.filter_by(email=user_email).first()
                
                if not user or user.role.value != required_role:
                    return jsonify({'error': 'Accès non autorisé'}), 403
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        return decorated_function
    return decorator