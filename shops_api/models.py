from config import db, app, auth, bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from typing import Dict, Union
from email_validator import validate_email, EmailNotValidError
import phonenumbers
import datetime
from phonenumbers import carrier
from phonenumbers.phonenumberutil import number_type, NumberParseException
from flask import request, jsonify
from sqlalchemy.orm import backref
from utils.logger import get_log

log = get_log()


class Shop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    address = db.Column(db.String(120), unique=True, nullable=True)
    phone_number = db.Column(db.String(120), unique=True, nullable=True)
    firebase_uid = db.Column(db.String(255), unique=True, nullable=True)
    password = db.Column(db.String(255), unique=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    def validate(self) -> Union[None, jsonify]:
        try:
            log.info("Email Validation")
            validate_email(self.email)
        except EmailNotValidError as e:
            log.error(f"Email is not valid - Exception raised {e}")
            return jsonify({"error": str(e)}, 500)
        try:
            if not carrier._is_mobile(
                number_type(phonenumbers.parse(self.phone_number))
            ):
                return jsonify({"error": "Phone number is not valid"}), 500
        except NumberParseException as e:
            log.error(f"Incorrect Phone Parsing - Exception raised {e}")
            return jsonify({"error": str(e)}), 500

    def serialize(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "address": self.address,
            "phone_number": self.phone_number,
        }

    def hash_password(self) -> Union[None, jsonify]:
        log.warning(f"Will be hashing the following password: {self.password}")
        try:
            self.password = bcrypt.generate_password_hash(self.password).decode('utf-8')
            #self.password = bcrypt.generate_password_hash(self.password)
            '''self.password = bcrypt.hashpw(
                bytes(self.password, "utf-8"), bcrypt.gensalt()
            )'''
            log.warning(f"Hashing {self.password}")
        except Exception as e:
            log.error(f"Unable to hash password {self.password}")
            return jsonify({"error": str(e)}), 500

    def check_password(self, password: Union[bytes, str]) -> bool:
        return bcrypt.check_password_hash(self.password, password)
        '''if not isinstance(password, bytes):
            password = bytes(password, "utf-8")
        return bcrypt.checkpw(password, bytes(self.password, "utf-8"))'''

    def _create_firebase_user(self):
        try:
            shop = auth.create_user(
                email=self.email,
                email_verified=False,
                phone_number=self.phone_number,
                password=str(self.password),
                display_name=self.name,
                disabled=False,
            )
            self.firebase_uid = shop.uid
            log.info(f"Successfully created Firebase User with UID {self.firebase_uid}")
        except Exception as e:
            log.error(f"Exception raised - {e}")
            return jsonify({"error": str(e)}), 500

    def save(self) -> Union[None, jsonify]:
        try:
            err = self._create_firebase_user()
            if err:
                return err
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            log.error(f"Exception raised during commit - {e}")
            auth.delete_user(self.firebase_uid)
            db.session.rollback()
            return (
                jsonify({"error": f"Incorrect data sent - Unknown Exception raised"}),
                500,
            )

    def __repr__(self) -> str:
        return f"{self.name} - {self.id}"


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False, nullable=False)
    description = db.Column(db.String(80), unique=False, nullable=True)
    price = db.Column(db.Float, default=0.00)
    shop_id = db.Column(db.Integer, db.ForeignKey("shop.id"))
    shop = db.relationship("Shop", backref=backref("shop", uselist=False))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except:
            db.session.rollback()
            return jsonify({"error": "Internal Server Error"}), 500

    def serialize(self) -> Dict:
        categories = self._get_categories()
        log.error(categories)
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "shop_id": self.shop_id,
            "categories": categories,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    def _get_categories(self) -> list:
        categories = ProductsCategories.query.with_entities(ProductsCategories.category_id).filter_by(product_id=self.id)
        return [c.serialize() for c in Category.query.join(ProductsCategories, Category.id==ProductsCategories.category_id).filter(ProductsCategories.product_id==self.id)]
        #return [category.serialize() for category in Category.query.join(categories, Category.id==categories.id).filter(Category.id==categories.category_id)]

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True, nullable=False)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def serialize(self) -> Dict:
        return {"id": self.id, "title": self.title}


class ProductsCategories(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))

    def save(self):
        db.session.add(self)
        db.session.commit()

    def serialize(self) -> Dict:
        return dict(
            (str(key), value)
            for key, value in self.__dict__.items()
            if not callable(value) and not key.startswith("__")
        )

db.create_all()
