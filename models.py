from flask_sqlalchemy import SQLAlchemy
import secrets

db = SQLAlchemy()

class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    invite_code = db.Column(db.String(10), unique=True, default=lambda: secrets.token_hex(5))  # Auto-generate invite code

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'admin' or 'user'
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
