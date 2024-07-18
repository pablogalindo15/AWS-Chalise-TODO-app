# AWS Chalice Todo Application

This repository contains a serverless Todo application built using AWS Chalice. It serves as a learning project to explore AWS serverless architecture and the Chalice framework.

## Features

- RESTful API for managing Todo items (create, read, update, delete)
- DynamoDB integration for data persistence
- JWT-based authentication
- Sphinx documentation

## Project Structure

- `app.py`: Main application file containing route definitions and business logic
- `chalicelib/`: Directory containing additional modules
  - `db.py`: Database interaction layer
  - `auth.py`: Authentication and JWT handling
- `docs/`: Sphinx documentation
- `requirements.txt`: Project dependencies
- `.chalice/`: Chalice configuration files

## Documentation

This project is documented using Sphinx. The documentation covers:

- API endpoints and their usage
- Database schema and operations
- Authentication flow
- Deployment instructions

To build the documentation:

1. Navigate to the `docs/` directory
2. Run `make html`
3. Open `docs/_build/html/index.html` in a web browser

## Getting Started

1. Clone this repository
   ```sh
   git clone https://github.com/yourusername/todo-app.git
   cd todo-app
