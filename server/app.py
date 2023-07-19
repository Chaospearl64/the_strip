from flask import Flask, request, jsonify, make_response
from flask_restful import Resource, Api
import uuid
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta
from flask_cors import CORS
from werkzeug.security import generate_password_hash
from models import db, User, Comic
import hashlib
import secrets
import time
import os

public_key = '1f2440e3320ab3d9b466c2c1699cc76a'
private_key = 'c717b70ce1da6ea17908f2803eb728b3610d1af6'
url = 'https://gateway.marvel.com/v1/public/comics'

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

api = Api(app)
timestamp = str(time.time())
hash_str = hashlib.md5(
    (timestamp + private_key + public_key).encode()).hexdigest()
migrate = Migrate(app, db)
secret_key = os.urandom(24)
db.init_app(app)
app.secret_key = secret_key


@app.route('/')
def hello():
    return "I love Marvel!"


class Comics(Resource):
    def get(self):
        comics = Comic.query.all()
        serialized_comics = [{
            'id': comic.id,
            'title': comic.title,
            'description': comic.description,
            'image': comic.image_url
        } for comic in comics]
        return serialized_comics, 200


api.add_resource(Comics, '/comics')


class Registration(Resource):
    def post(self):
        data = request.get_json()

        # Extract user information from the request data
        name = data['name']
        email = data['email']
        password = data['password']

        # Validate the input data using the validation schema or any other validation method

        # Check if a user with the same email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return {'message': 'User with the same email already exists'}, 409

        # Hash the password
        password_hash = generate_password_hash(password, method='sha256')

        # Create a new User object and save it to the database
        user = User(name=name, email=email, password_hash=password_hash)

        # Generate a random cookie value
        cookie_value = secrets.token_hex(16)

        # Set the user's cookie value and expiration time
        response = jsonify({'message': 'User registered successfully'})
        response.set_cookie('user_id', str(user.id),
                            expires=datetime.utcnow() + timedelta(hours=24))

        # Store the cookie value in local storage
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Expose-Headers', 'Set-Cookie')
        response.headers.add(
            'Set-Cookie', f'cookie_value={cookie_value}; Secure; SameSite=None; Expires={datetime.utcnow() + timedelta(hours=24)}')

        user.cookie_value = cookie_value
        user.cookie_expiration = datetime.utcnow(
        ) + timedelta(hours=24)  # Set the expiration time

        db.session.add(user)
        db.session.commit()

        return response, 201


api.add_resource(Registration, '/register')


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    # Extract user information from the request data
    email = data['email']
    password = data['password']

    # Validate the input data using the validation schema or any other validation method

    # Check if a user with the given email exists
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'message': 'Invalid email or password'}), 400

    # Check if the password is correct
    if not user.check_password(password):
        return jsonify({'message': 'Invalid email or password'}), 400

    # Generate a new cookie value
    cookie_value = secrets.token_hex(16)

    # Set the cookie in the response with an expiration time of 24 hours
    response = jsonify({
        'message': 'Login successful',
        'id': f"{user.id}"
    })

    response.set_cookie('user_id', str(user.id),
                        expires=datetime.utcnow() + timedelta(hours=24),
                        secure=True, samesite='None')
    response.set_cookie('cookie_value', cookie_value,
                        expires=datetime.utcnow() + timedelta(hours=24),
                        secure=True, samesite='None')

    # Update the user's cookie value in the database
    user.cookie_value = cookie_value
    user.cookie_expiration = datetime.utcnow() + timedelta(hours=24)
    db.session.commit()

    return response, 200

@app.route('/collection', methods=['GET', 'POST'])
def collection():
    if request.method == 'GET':
        # Check if the user's cookie exists and is valid
        cookie_value = request.cookies.get('cookie_value')

        if cookie_value:
            user = User.query.filter_by(cookie_value=cookie_value).first()

            if user:
                saved_comics = user.comics

                serialized_comics = [{
                    'id': comic.id,
                    'title': comic.title,
                    'description': comic.description
                } for comic in saved_comics]

                return jsonify(serialized_comics), 200

        # User is not logged in or the cookie is invalid, return an error message or redirect to the login page
        return jsonify({'message': 'Unauthorized'}), 401

    if request.method == 'POST':
        data = request.get_json()
        id = data.get('id')
        comic_id = data.get('comicId')

        user = User.query.filter_by(id=id).first()
        comic = Comic.query.get(comic_id)

        if not user:
            return jsonify({'message': 'User not found'}), 404

        if not comic:
            return jsonify({'message': 'Comic not found'}), 404

        if comic in user.comics:
            return jsonify({
                'message': 'Comic already in collection',
            }), 400

        # Add the comic to the user's collection
        user.comics.append(comic)
        db.session.commit()

        # Get the updated collection from the database
        updated_collection = User.query.filter_by(id=id).first().comics

        # Serialize the updated collection
        serialized_collection = [{
            'id': comic.id,
            'title': comic.title,
            'description': comic.description
        } for comic in updated_collection]

        return jsonify({
            'message': 'Comic added to collection',
            'collection': serialized_collection
        }), 201



@app.route('/comics/<comic_id>')
def get_comic_details(comic_id):
    comic = Comic.query.get(comic_id)
    if not comic:
        return jsonify({'message': 'Comic not found'}), 404

    serialized_comic = {
        'id': comic.id,
        'title': comic.title,
        'description': comic.description,
        'image_url': comic.image_url,
    }

    return jsonify(serialized_comic), 200


@app.route('/user', methods=['POST'])
def get_user_data():
    data = request.get_json()

    email = data.get('email')

    if email:
        user = User.query.filter_by(email=email).first()
        if user:
            serialized_user = {
                "email": user.email,
                "name": user.name,
                # Add more fields as needed
            }
            return jsonify(serialized_user), 200
        else:
            return jsonify({"error": "User not found"}), 404
    else:
        return jsonify({"error": "Email parameter missing"}), 400


if __name__ == "__main__":
    app.run(port=5555, debug=True)