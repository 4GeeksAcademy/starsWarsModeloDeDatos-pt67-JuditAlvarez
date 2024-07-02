"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, Users, Characters, Vehicles, Planets, FavouritesCharacters, FavouritesPlanets, FavouritesVehicles

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code


@app.route('/')
def sitemap():
    return generate_sitemap(app)

# GET route for Users
@app.route('/user', methods=['GET'])
def get_users():
    users = Users.query.all()
    users_list = [user.serialize() for user in users]
    return jsonify({"users": users_list}), 200


@app.route('/user', methods=['POST'])
def create_user():
    body = request.get_json()
    if not body or 'name' not in body or 'email' not in body or 'password' not in body:
        return jsonify({"msg": "Request body is missing required fields"}), 400

    new_user = Users(name=body['name'], email=body['email'], password=body['password'])
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"user": new_user.serialize()}), 201


@app.route('/user', methods=['DELETE'])
def delete_user():
    user_id = request.args.get('id')
    if not user_id:
        return jsonify({"msg": "User ID is required"}), 400

    user = Users.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({"msg": "User deleted successfully"}), 200


@app.route('/user', methods=['PUT'])
def update_user():
    body = request.get_json()
    if not body or 'id' not in body:
        return jsonify({"msg": "Request body is missing required fields"}), 400

    user_id = body['id']
    user = Users.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    user.name = body.get('name', user.name)
    user.email = body.get('email', user.email)
    user.password = body.get('password', user.password)
    db.session.commit()

    return jsonify({"user": user.serialize()}), 200

@app.route('/favourites/characters', methods=['POST'])
def add_favourite_character():
    body = request.get_json()
    if not body or 'user_id' not in body or 'character_id' not in body:
        return jsonify({"msg": "Request body is missing required fields"}), 400

    new_favourite = FavouritesCharacters(user_id=body['user_id'], id=body['character_id'])
    db.session.add(new_favourite)
    db.session.commit()

    return jsonify({"favourite": new_favourite.serialize()}), 201

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=True)
