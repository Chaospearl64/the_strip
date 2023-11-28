
# The Strip - Backend

Welcome to the backend of "The Strip" project! This repository contains the backend code for the application. "The Strip" is a web application that allows users to browse and manage their comic book collections. The backend provides the necessary API endpoints and database interactions to support the frontend application.

## Backend Overview

The backend of "The Strip" is built using Flask, a lightweight and flexible Python web framework. It provides the necessary API endpoints for the frontend to fetch and update data from the database. The backend uses Flask-RESTful for building RESTful APIs and Flask-SQLAlchemy for database interactions.

### Getting Started

To run the backend locally, follow these steps:

1. Clone this repository to your local machine.
2. Make sure you have Python and pip installed.
3. Navigate to the project directory in the terminal.
4. Install the required dependencies with the following command:

```
pip install -r requirements.txt
```

5. Run the Flask development server:

```
python app.py
```

6. The backend server will start running on http://127.0.0.1:5555

### Features

- Provide API endpoints for fetching and managing comic data.
- User registration and login functionality with JWT-based authentication.
- Allow users to add, remove, and view comics in their collections.
- Enable users to write and submit reviews for comics.

### Technologies Used

- Flask: A micro web framework written in Python for building web applications.
- Flask-RESTful: An extension for Flask that adds support for building RESTful APIs.
- Flask-SQLAlchemy: An extension for Flask that simplifies database interactions using SQLAlchemy.
- Flask-Migrate: An extension for Flask that handles database migrations.
- Flask-CORS: An extension for Flask that enables Cross-Origin Resource Sharing (CORS) support.
- JWT: JSON Web Tokens for secure user authentication.

### Directory Structure

The backend follows this directory structure:

- `app.py`: The main entry point of the Flask application.
- `models.py`: Contains the SQLAlchemy models for the database tables.
- `database.db`: The SQLite database file.
- `requirements.txt`: Lists the required Python packages for the project.

## Contributing

We welcome contributions to improve and expand "The Strip" project! If you'd like to contribute, please follow our [contribution guidelines](CONTRIBUTING.md) for more information.

## License

This project is licensed under the [MIT License](LICENSE).
```

This version focuses solely on the backend part of "The Strip" project and provides instructions for setting up and running the backend locally.