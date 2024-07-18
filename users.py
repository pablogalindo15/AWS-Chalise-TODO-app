import os
import json
import getpass
import argparse
import hashlib
import hmac

import boto3

from boto3.dynamodb.types import Binary

"""
This module provides functions to manage users in a DynamoDB table, including creating users,
listing users, and verifying passwords. It also includes a command-line interface (CLI) for
interacting with these functions.
"""

def get_table_name(stage):
    """
    Get the DynamoDB table name for a given stage.

    This function reads the Chalice configuration file to get the table name based on the stage.

    :param stage: The deployment stage (e.g., 'dev', 'prod').
    :return: The DynamoDB table name.
    """
    # We might want to use the Chalice modules to load the config.
    # For now we'll just load it directly.
    with open(os.path.join('.chalice', 'config.json')) as f:
        data = json.load(f)
    return data['stages'][stage]['environment_variables']['USERS_TABLE_NAME']

def create_user(stage):
    """
    Create a new user in the DynamoDB table.

    This function prompts the user for a username and password, encodes the password,
    and stores the user information in the DynamoDB table.

    :param stage: The deployment stage (e.g., 'dev', 'prod').
    """
    table_name = get_table_name(stage)
    table = boto3.resource('dynamodb').Table(table_name)
    username = input('Username: ').strip()
    password = input('Password: ').strip().encode()
    password_fields = encode_password(password)
    item = {
        'username': username,
        'hash': password_fields['hash'],
        'salt': Binary(password_fields['salt']),
        'rounds': password_fields['rounds'],
        'hashed': Binary(password_fields['hashed']),
    }
    table.put_item(Item=item)

def encode_password(password, salt=None):
    """
    Encode a password using PBKDF2-HMAC-SHA256.

    This function generates a salt if one is not provided, and uses it to hash the password.

    :param password: The password to encode.
    :param salt: Optional. The salt to use for hashing. If not provided, a new salt is generated.
    :return: A dictionary containing the hash algorithm, salt, number of rounds, and hashed password.
    """
    password = password.encode()
    if salt is None:
        salt = os.urandom(16)
    rounds = 100000
    hashed = hashlib.pbkdf2_hmac('sha256', password, salt, rounds)
    return {
        'hash': 'sha256',
        'salt': salt,
        'rounds': rounds,
        'hashed': hashed,
    }

def list_users(stage):
    """
    List all users in the DynamoDB table.

    This function retrieves and prints all usernames from the DynamoDB table.

    :param stage: The deployment stage (e.g., 'dev', 'prod').
    """
    table_name = get_table_name(stage)
    table = boto3.resource('dynamodb').Table(table_name)
    for item in table.scan()['Items']:
        print(item['username'])

def test_password(stage):
    """
    Test a user's password.

    This function prompts for a username and password, retrieves the stored password information
    from the DynamoDB table, and verifies the provided password against the stored hash.

    :param stage: The deployment stage (e.g., 'dev', 'prod').
    """
    username = input('Username: ').strip()
    password = getpass.getpass('Password: ').strip()
    table_name = get_table_name(stage)
    table = boto3.resource('dynamodb').Table(table_name)
    item = table.get_item(Key={'username': username})['Item']
    encoded = encode_password(password, salt=item['salt'].value)
    if hmac.compare_digest(encoded['hashed'], item['hashed'].value):
        print("Password verified.")
    else:
        print("Password verification failed.")

def main():
    """
    Command-line interface for user management.

    This function parses command-line arguments and calls the appropriate function
    based on the provided arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--create-user', action='store_true', help='Create a new user')
    parser.add_argument('-t', '--test-password', action='store_true', help='Test a user\'s password')
    parser.add_argument('-s', '--stage', default='dev', help='The deployment stage (default: dev)')
    parser.add_argument('-l', '--list-users', action='store_true', help='List all users')
    args = parser.parse_args()
    if args.create_user:
        create_user(args.stage)
    elif args.list_users:
        list_users(args.stage)
    elif args.test_password:
        test_password(args.stage)

if __name__ == '__main__':
    main()