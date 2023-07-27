from flask import Flask, request, jsonify, make_response
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta
from flask_cors import CORS
from werkzeug.security import generate_password_hash
from models import db, User, Comic, UserComic,Review


import hashlib
import secrets
import os
import time

public_key = '1f2440e3320ab3d9b466c2c1699cc76a'
private_key = 'c717b70ce1da6ea17908f2803eb728b3610d1af6'
url = 'https://gateway.marvel.com/v1/public/comics'

app = Flask(__name__)
CORS(app, supports_credentials=True)  # Enable CORS with credentials support

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
        serialized_comics = []
        for comic in comics:
            serialized_comic = {
                'id': comic.id,
                'title': comic.title,
                'image': comic.image_url,
                # Add other fields as needed for comic details
            }
            serialized_comics.append(serialized_comic)

        return serialized_comics, 200


api.add_resource(Comics, '/comics')


@app.route('/comics/<int:comic_id>', methods=['GET'])
def get_comic(comic_id):
    comic = Comic.query.get(comic_id)
    if not comic:
        return jsonify({'message': 'Comic not found'}), 404

    serialized_comic = {
        'id': comic.id,
        'title': comic.title,
        'comic_description': comic.comic_description,
        'image': comic.image_url,
        'release_date': comic.release_date
        # Add other fields as needed for comic details
    }

    return jsonify(serialized_comic), 200


class Registration(Resource):
    def post(self):
        data = request.get_json()

        # Extract user information from the request data
        name = data['name']
        email = data['email']
        password = data['password']

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
        response = make_response(jsonify({'message': 'User registered successfully'}), 201)
        response.set_cookie('user_id', str(user.id),
                            expires=datetime.utcnow() + timedelta(hours=24),
                            secure=True, samesite='None')
        response.set_cookie('cookie_value', cookie_value,
                            expires=datetime.utcnow() + timedelta(hours=24),
                            secure=True, samesite='None')

        user.cookie_value = cookie_value
        user.cookie_expiration = datetime.utcnow() + timedelta(hours=24)  # Set the expiration time

        db.session.add(user)
        db.session.commit()

        # Redirect to the home page after successful registration
        response.headers['Location'] = '/'
        return response


# Use a different route for the Registration resource
api.add_resource(Registration, '/register')  # Change the route to '/register'


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    # Extract user information from the request data
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email and password are required'}), 400

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

    # Debug statements to verify cookie is being set correctly
    print(f"User ID: {user.id}")
    print(f"Cookie value: {cookie_value}")

    return response, 200

@app.route('/comics/<int:comic_id>/add-review', methods=['POST'])
def add_review(comic_id):
    data = request.get_json()
    user_id = request.user_id  

    if not user_id:
        return jsonify({"error": "User not authenticated."}), 401

    if 'review' in data:
        review_text = data['review']

        # Check if the comic exists in comics_data
        comic = Comic.query.get(comic_id)
        if not comic:
            return jsonify({"error": "Comic not found."}), 404

        # Add the review to the database
        review = Review(user_id=user_id, comic_id=comic_id, review_text=review_text)
        db.session.add(review)
        db.session.commit()

        return jsonify({"message": "Review added successfully."}), 200
    else:
        return jsonify({"error": "Review data is missing."}), 400


@app.route('/collection/<int:user_id>', methods=['GET', 'POST'])
def collection(user_id):
    if request.method == 'GET':
        user = User.query.get(user_id)
        if user:
            user_comics = user.comics
            serialized_comics = [{
                'id': comic.id,
                'title': comic.title,
                'description': comic.comic_description,
                'image': comic.image_url
            } for comic in user_comics]
            return jsonify(serialized_comics), 200
        else:
            return jsonify({'message': 'User not found'}), 404

    if request.method == 'POST':
        data = request.get_json()
        comic_id = data.get('comic_id')  # Update the key to 'comic_id'

        user = User.query.get(user_id)
        comic = Comic.query.get(comic_id)

        if not user:
            return jsonify({'message': 'User not found'}), 404

        if not comic:
            return jsonify({'message': 'Comic not found'}), 404

        if comic in user.comics:
            return jsonify({
                'message': 'Comic already in collection',
            }), 400  # Return 400 (Bad Request) with custom message

        user.comics.append(comic)
        db.session.commit()

        return jsonify({'message': 'Comic added to collection'}), 201



@app.route('/collection/<int:user_id>/<int:comic_id>', methods=['DELETE'])
def delete_comic_from_collection(user_id, comic_id):
    # Check if the user exists in the database
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Check if the comic exists in the database
    comic = Comic.query.get(comic_id)
    if not comic:
        return jsonify({'message': 'Comic not found'}), 404

    # Check if the comic is in the user's collection
    if comic not in user.comics:
        return jsonify({'message': 'Comic not found in the user\'s collection'}), 404

    # Remove the comic from the user's collection and commit the changes to the database
    user.comics.remove(comic)
    db.session.commit()

    return jsonify({'message': 'Comic successfully removed from the user\'s collection'}), 200


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


@app.route('/collection/<int:user_id>/edit-name', methods=['PATCH'])
def edit_user_name(user_id):
    data = request.get_json()
    new_name = data.get('name')

    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Update the user's name
    user.name = new_name
    db.session.commit()

    return jsonify({'message': 'User name updated successfully', 'name': new_name}), 200


@app.route('/collection/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    # Check if the user exists in the database
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Delete the user from the database
    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': 'User deleted successfully'}), 200
    


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5555)