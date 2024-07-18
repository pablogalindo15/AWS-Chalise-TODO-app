import os
import uuid
import json
import argparse
import boto3

"""
This module provides functionality to create DynamoDB tables for a TODO application
and record the table names as environment variables in the Chalice configuration file.
"""

TABLES = {
    'app': {
        'prefix': 'todo-app',
        'env_var': 'APP_TABLE_NAME',
        'hash_key': 'username',
        'range_key': 'uid'
    },
    'users': {
        'prefix': 'users-app',
        'env_var': 'USERS_TABLE_NAME',
        'hash_key': 'username',
    }
}

def create_table(table_name_prefix, hash_key, range_key=None):
    """
    Create a DynamoDB table with the specified configuration.

    :param table_name_prefix: Prefix for the table name.
    :param hash_key: The hash key for the table.
    :param range_key: The range key for the table (optional).
    :return: The name of the created table.
    """
    table_name = f'{table_name_prefix}-{str(uuid.uuid4())}'
    client = boto3.client('dynamodb')
    key_schema = [
        {
            'AttributeName': hash_key,
            'KeyType': 'HASH',
        }
    ]
    attribute_definitions = [
        {
            'AttributeName': hash_key,
            'AttributeType': 'S',
        }
    ]
    if range_key is not None:
        key_schema.append({'AttributeName': range_key, 'KeyType': 'RANGE'})
        attribute_definitions.append(
            {'AttributeName': range_key, 'AttributeType': 'S'})
    client.create_table(
        TableName=table_name,
        KeySchema=key_schema,
        AttributeDefinitions=attribute_definitions,
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5,
        }
    )
    waiter = client.get_waiter('table_exists')
    waiter.wait(TableName=table_name, WaiterConfig={'Delay': 1})
    return table_name

def record_as_env_var(key, value, stage):
    """
    Record a key-value pair as an environment variable in the Chalice configuration file.

    :param key: The key of the environment variable.
    :param value: The value of the environment variable.
    :param stage: The deployment stage (e.g., 'dev', 'prod').
    """
    config_path = os.path.join('.chalice', 'config.json')
    with open(config_path) as f:
        data = json.load(f)
        data['stages'].setdefault(stage, {}).setdefault(
            'environment_variables', {}
        )[key] = value
    with open(config_path, 'w') as f:
        serialized = json.dumps(data, indent=2, separators=(',', ': '))
        f.write(serialized + '\n')

def main():
    """
    Main function to create a DynamoDB table and record its name as an environment variable.

    This function parses command-line arguments to determine the table type and deployment stage,
    creates the appropriate DynamoDB table, and records the table name in the Chalice configuration.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--stage', default='dev',
                        help='Deployment stage (default: dev)')
    parser.add_argument('-t', '--table-type', default='app',
                        choices=['app', 'users'],
                        help='Specify which type of table to create (default: app)')
    args = parser.parse_args()
    
    table_config = TABLES[args.table_type]
    table_name = create_table(
        table_config['prefix'], 
        table_config['hash_key'],
        table_config.get('range_key')
    )
    record_as_env_var(table_config['env_var'], table_name, args.stage)

if __name__ == '__main__':
    main()