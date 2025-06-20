from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from app.models import User
from app import db
import re
from sqlalchemy.exc import IntegrityError
from flasgger import swag_from

bp = Blueprint('auth', __name__, url_prefix='/auth')

# Helper functions
NAME_REGEX = re.compile(r'^[A-Za-z ]+$')
PASSWORD_REGEX = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')


def base_response(success, message, obj=None, errors=None):
    return jsonify({
        'Success': success,
        'Message': message,
        'Object': obj,
        'Errors': errors or None
    })

@bp.route('/signup', methods=['POST'])
@swag_from({
    'tags': ['Auth'],
    'summary': 'Sign up as a company or applicant',
    'description': 'Register a new user (company or applicant).',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'email': {'type': 'string'},
                    'password': {'type': 'string'},
                    'role': {'type': 'string', 'enum': ['company', 'applicant']}
                },
                'required': ['name', 'email', 'password', 'role']
            }
        }
    ],
    'responses': {
        201: {'description': 'Signup successful'},
        400: {'description': 'Validation failed'},
        409: {'description': 'Email already exists'}
    }
})
def signup():
    data = request.get_json()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    role = data.get('role', '')
    errors = []

    # Validation
    if not name or not NAME_REGEX.match(name):
        errors.append('Name is required and must contain only alphabets and spaces.')
    if not email or not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
        errors.append('A valid email is required.')
    if not password or not PASSWORD_REGEX.match(password):
        errors.append('Password must be at least 8 characters, include upper and lower case, a number, and a special character.')
    if role not in ['company', 'applicant']:
        errors.append('Role must be either "company" or "applicant".')
    if errors:
        return base_response(False, 'Validation failed', None, errors), 400

    hashed_pw = generate_password_hash(password)
    user = User(name=name, email=email, password=hashed_pw, role=role)
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return base_response(False, 'Email already exists', None, ['Email already exists']), 409

    user_obj = {'id': str(user.id), 'name': user.name, 'email': user.email, 'role': user.role}
    return base_response(True, 'Signup successful', user_obj), 201

@bp.route('/login', methods=['POST'])
@swag_from({
    'tags': ['Auth'],
    'summary': 'Login',
    'description': 'Login with email and password.',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'email': {'type': 'string'},
                    'password': {'type': 'string'}
                },
                'required': ['email', 'password']
            }
        }
    ],
    'responses': {
        200: {'description': 'Login successful'},
        401: {'description': 'Incorrect password'},
        404: {'description': 'User not found'}
    }
})
def login():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    user = User.query.filter_by(email=email).first()
    if not user:
        return base_response(False, 'User not found', None, ['User not found']), 404
    if not check_password_hash(user.password, password):
        return base_response(False, 'Incorrect password', None, ['Incorrect password']), 401
    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return base_response(True, 'Login successful', {'token': token, 'user': {'id': str(user.id), 'role': user.role}}) 