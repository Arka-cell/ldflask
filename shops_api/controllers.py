import models
from config import app, auth, CUSTOM_TO_ID_TOKEN_ENDPOINT
from flask import request, jsonify
from utils.logger import get_log
from firebase_jwt import create_custom_token, FirebaseAuthentication
import requests

log = get_log()


@app.route("/", methods=["GET"])
def home():
    return "<h1>Welcome to Shop App</p>"


@app.route("/api/v1/shops", methods=["POST"])
def create_shop():
    data = request.json
    log.warning(data)
    shop = models.Shop(
        name=data.get("name"),
        email=data.get("email"),
        address=data.get("address"),
        phone_number=data.get("phone_number"),
        password=data.get("password"),
    )
    err = shop.validate()
    if err:
        return err
    err = shop.hash_password()
    if err:
        return err
    err = shop.save()
    if err:
        return err
    return jsonify({"message": "Congratulation, Shop created"}), 201


@app.route("/api/v1/login", methods=["POST"])
def login():
    data = request.json
    shop = models.Shop.query.filter_by(email=(data.get("email"))).first()
    log.info(f"Successfully retrieved Shop - Email is: {shop.email}")
    if not shop.check_password(data.get("password")):
        log.warning(f"Incorrect password - {shop.email}")
        return jsonify({"message": "Congratulation, Shop created"}), 401
    custom_token = create_custom_token(shop.firebase_uid, shop.id).decode("utf-8")
    res = requests.post(CUSTOM_TO_ID_TOKEN_ENDPOINT, json={"token": custom_token, "returnSecureToken": True})
    id_token = res.json()["idToken"]
    return jsonify({"token": f"Token {id_token}"})


@app.route("/api/v1/products", methods=["POST"])
def create_product():
    keyword, token = request.headers.get("Authorization").split()
    firebase_authenticator = FirebaseAuthentication(token)
    if not firebase_authenticator.verify_custom_token():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    shop = models.Shop.query.filter_by(firebase_uid=firebase_authenticator.firebase_uid).first()
    product = models.Product(
        name=data.get("name"),
        price=data.get("price"),
        shop_id=shop.id,
        shop=shop,
    )
    err = product.save()
    if err:
        return err
    categories = models.Category.query.filter(models.Category.id.in_(data.get("categories")))
    [models.ProductsCategories(product_id=product.id, category_id=category.id).save() for category in categories]
    return jsonify({"message": "Created product successfully"}), 200

@app.route("/api/v1/products", methods=["GET"])
def get_products():
    products = models.Product.query.all()
    return jsonify({"products": [product.serialize() for product in products]})


@app.route("/api/v1/products/<int:product_id>")
def get_product(product_id):
    product = models.Product.query.filter_by(id=product_id).first()
    return jsonify({"product": product.serialize()}), 200


@app.route("/api/v1/shops")
def get_shops():
    shops = models.Shop.query.all()
    return jsonify({"shops": [shop.serialize() for shop in shops]})

@app.route("/api/v1/shops/<int:shop_id>")
def get_shop(shop_id):
    shop = models.Shop.query.filter_by(id=shop_id).first()
    return jsonify({"shop": shop.serialize()})
