from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from models import db, User, Organization

auth_routes = Blueprint('auth_routes', __name__)

@auth_routes.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    org_name = data.get('org_name')  # Organization name is required

    # Validate input
    if not email or not password or not org_name:
        return jsonify({'error': 'Email, password, and organization name are required'}), 400

    # Check if the organization exists
    organization = Organization.query.filter_by(name=org_name).first()
    if not organization:
        return jsonify({'error': 'Organization does not exist'}), 400

    # Check if the user exists under this organization
    user = User.query.filter_by(email=email, org_id=organization.id).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({'error': 'Invalid credentials'}), 401

    # Login successful
    return jsonify({
        'message': 'Login successful',
        'role': user.role,
        'username': user.username,
        'org_name': organization.name
    })
