import hashlib
import hmac
import datetime
from uuid import uuid4

import jwt
from chalice import UnauthorizedError

"""
This module handles JWT token generation and validation for user authentication.

It provides functions to create JWT tokens upon successful login and to decode
these tokens for authorization purposes.
"""

# TODO: Figure out what we want to do with this.
# We can either move this out to env vars in config.json,
# use KMS to encrypt/decrypt this value, or store this in SSM.
# Until we figure it out I'll store it here.
_SECRET = b'\xf7\xb6k\xabP\xce\xc1\xaf\xad\x86\xcf\x84\x02\x80\xa0\xe0'

def get_jwt_token(username, password, record):
    """
    Generate a JWT token for a user upon successful authentication.

    This function verifies the provided password against the stored hash and,
    if valid, generates a JWT token for the user.

    :param username: The username of the user.
    :param password: The password provided by the user.
    :param record: The user's record from the database, containing hash information.
    :return: A JWT token string if authentication is successful.
    :raises UnauthorizedError: If the password is invalid.
    """
    password = password.encode()
    actual = hashlib.pbkdf2_hmac(
        record['hash'],
        password,
        record['salt'].value,
        record['rounds']
    )
    expected = record['hashed'].value
    if hmac.compare_digest(actual, expected):
        now = datetime.datetime.utcnow()
        unique_id = str(uuid4())
        payload = {
            'sub': username,
            'iat': now,
            'nbf': now,
            'jti': unique_id,
            # NOTE: We can also add 'exp' if we want tokens to expire.
        }
        return jwt.encode(payload, _SECRET, algorithm='HS256')
    raise UnauthorizedError('Invalid password')

def decode_jwt_token(token):
    """
    Decode and validate a JWT token.

    This function decodes the provided JWT token and verifies its signature.

    :param token: The JWT token string to decode and validate.
    :return: The decoded payload of the JWT token.
    :raises jwt.InvalidTokenError: If the token is invalid or has expired.
    """
    return jwt.decode(token, _SECRET, algorithms=['HS256'])