import flask
from flask import request, jsonify
from flask_sqlalchemy import SQLAlchemy
import firebase_admin
from firebase_admin import credentials, auth
from email_validator import validate_email, EmailNotValidError
import phonenumbers
from phonenumbers import carrier
from phonenumbers.phonenumberutil import number_type
from flask_migrate import Migrate
from typing import Dict
from flask_bcrypt import Bcrypt

cred = credentials.Certificate("serviceAccountKey.json")

firebase_admin.initialize_app(cred)

API_KEY = "AIzaSyBVs9gmaRFXYrpQrDWYJ7z6G3dN59iWhvM"

CUSTOM_TO_ID_TOKEN_ENDPOINT = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={API_KEY}"

app = flask.Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://sammy:password@localhost/flask_db"
app.config["DEBUG"] = True

bcrypt = Bcrypt(app)

db = SQLAlchemy(app)

migrate = Migrate(app, db)
