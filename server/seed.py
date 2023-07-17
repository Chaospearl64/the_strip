from app import app, db, public_key, timestamp, hash_str, url, private_key
from models import User, Comic, Review
import requests
from sqlalchemy import func


def seed_user():
    user = User(name='John Doe', email='john@example.com')
    user.set_password('password')  # Set the password using the set_password() method
    db.session.add(user)
    db.session.commit()


def seed_comics(num_fetches):
    limit = 100  # Number of comics to retrieve per request
    total_comics = num_fetches * limit
    offset = 0  # Initial offset for pagination
    number = 0

    while number < total_comics:
        # Make API request to Marvel API
        params = {
            'apikey': public_key,
            'ts': timestamp,
            'hash': hash_str,
            'limit': limit,
            'offset': offset
        }
        response = requests.get(url, params=params)
        
        data = response.json()
        print(data)
        if 'data' not in data or 'results' not in data['data']:
            print('Error: Invalid response format.')
            return

        results = data['data']['results']
        for comic_data in results:
            title = comic_data.get('title')
            description = comic_data.get('description', '')
            user = User.query.order_by(func.random()).first()
            user_id = user.id if user else None
            thumbnail = comic_data.get('thumbnail', {})
            image_url = f"{thumbnail.get('path', '')}/portrait_uncanny.{thumbnail.get('extension', '')}"
            comic = Comic(title=title, description=description,
                          user_id=user_id, image_url=image_url)
            db.session.add(comic)
            number += 1

        offset += limit  # Increment offset for the next pagination

        print(db.session, number)
    db.session.commit()




def seed_reviews():
    # Create review objects and add them to the session
    reviews = [
        Review(rating=4, comment='Great comic!', user_id=1, comic_id=1),
        Review(rating=5, comment='Awesome artwork!', user_id=2, comic_id=1),
        # Add more reviews as needed
    ]
    for review in reviews:
        db.session.add(review)
    db.session.commit()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_user()
        seed_comics(num_fetches=50)
        seed_reviews()
