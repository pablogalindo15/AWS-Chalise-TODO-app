import os
import boto3
from chalice import Chalice, AuthResponse
from chalicelib.db import InMemoryTodoDB
from chalicelib import db
from chalicelib import auth

# Create a Chalice app
app = Chalice(app_name='mytodo')
app.debug = True

# Initialize global variables for database connections
_DB = None
_USER_DB = None

@app.authorizer()
def jwt_auth(auth_request):
    """
    JWT authorizer function.

    This function checks the validity of a JWT token using the existing code in the auth module.
    If the token is valid, it returns a policy that allows access to all routes and sets the
    principal_id to the username in the JWT token.

    :param auth_request: The authorization request containing the JWT token.
    :return: AuthResponse object with access policy and principal_id.
    """
    token = auth_request.token
    decoded = auth.decode_jwt_token(token)
    return AuthResponse(routes=['*'], principal_id=decoded['sub'])

def get_app_db():
    """
    Get the application database connection.

    This function initializes the database connection if it hasn't been initialized yet,
    and returns the database connection object.

    :return: Database connection object.
    """
    global _DB
    if (_DB is None):
        _DB = db.DynamoDBTodo(
            boto3.resource('dynamodb').Table(
                os.environ['APP_TABLE_NAME'])
        )
    return _DB

@app.route('/todos', methods=['GET'], authorizer=jwt_auth)
def get_todos():
    """
    Get all TODO items.

    This route retrieves all TODO items from the database.

    :return: List of TODO items.
    """
    return get_app_db().list_items()

@app.route('/todos', methods=['POST'])
def add_new_todo():
    """
    Add a new TODO item.

    This route adds a new TODO item to the database.

    :return: The newly added TODO item.
    """
    body = app.current_request.json_body
    return get_app_db().add_item(description=body['description'], metadata=body.get('metadata'))

@app.route('/todos/{uid}', methods=['GET'], authorizer=jwt_auth)
def get_todo(uid):
    """
    Get a specific TODO item.

    This route retrieves a specific TODO item by its unique identifier (UID).

    :param uid: The unique identifier of the TODO item.
    :return: The TODO item with the given UID.
    """
    return get_app_db().get_item(uid)

@app.route('/todos/{uid}', methods=['DELETE'], authorizer=jwt_auth)
def delete_todo(uid):
    """
    Delete a specific TODO item.

    This route deletes a specific TODO item by its unique identifier (UID).

    :param uid: The unique identifier of the TODO item.
    :return: Result of the delete operation.
    """
    return get_app_db().delete_item(uid)

@app.route('/todos/{uid}', methods=['PUT'], authorizer=jwt_auth)
def update_todo(uid):
    """
    Update a specific TODO item.

    This route updates a specific TODO item by its unique identifier (UID).

    :param uid: The unique identifier of the TODO item.
    :return: Result of the update operation.
    """
    body = app.current_request.json_body
    get_app_db().update_item(uid, description=body.get('description'), state=body.get('state'), metadata=body.get('metadata'))

def get_users_db():
    """
    Get the users database connection.

    This function initializes the users database connection if it hasn't been initialized yet,
    and returns the database connection object.

    :return: Users database connection object.
    """
    global _USER_DB
    if (_USER_DB is None):
        _USER_DB = boto3.resource('dynamodb').Table(
            os.environ['USERS_TABLE_NAME'])
    return _USER_DB

@app.route('/login', methods=['POST'])
def login():
    """
    User login route.

    This route handles user login and returns a JWT token if the credentials are valid.

    :return: JWT token.
    """
    body = app.current_request.json_body
    record = get_users_db().get_item(
        Key={'username': body['username']})['Item']
    jwt_token = auth.get_jwt_token(
        body['username'], body['password'], record)
    return {'token': jwt_token}