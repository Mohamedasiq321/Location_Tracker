from flask import request, jsonify
from models import User, Location, Organization

@app.route('/get_locations', methods=['GET'])
def get_locations():
    org_name = request.args.get('org_name')

    # Validate organization
    organization = Organization.query.filter_by(name=org_name).first()
    if not organization:
        return jsonify({'error': 'Organization not found'}), 400

    # Fetch locations for users in this organization
    locations = Location.query.filter(Location.user.has(org_id=organization.id)).all()

    return jsonify([{
        'username': loc.user.username,
        'latitude': loc.latitude,
        'longitude': loc.longitude
    } for loc in locations])
