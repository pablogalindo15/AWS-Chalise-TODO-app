from uuid import uuid4
from boto3.dynamodb.conditions import Key

"""
This module provides classes for managing TODO items in different types of databases.
It includes an abstract base class `TodoDB`, and concrete implementations for in-memory
storage (`InMemoryTodoDB`) and DynamoDB storage (`DynamoDBTodo`).
"""

DEFAULT_USERNAME = 'default'

class TodoDB(object):
    """
    Abstract base class for a TODO database.
    
    This class defines the interface for managing TODO items.
    """

    def list_items(self):
        """
        List all TODO items.

        This method should be implemented by subclasses to return a list of TODO items.
        """
        pass

    def add_item(self, description, metadata=None):
        """
        Add a new TODO item.

        This method should be implemented by subclasses to add a new TODO item.

        :param description: The description of the TODO item.
        :param metadata: Optional metadata for the TODO item.
        """
        pass

    def get_item(self, uid):
        """
        Get a specific TODO item by its unique identifier (UID).

        This method should be implemented by subclasses to return a TODO item.

        :param uid: The unique identifier of the TODO item.
        """
        pass

    def delete_item(self, uid):
        """
        Delete a specific TODO item by its unique identifier (UID).

        This method should be implemented by subclasses to delete a TODO item.

        :param uid: The unique identifier of the TODO item.
        """
        pass

    def update_item(self, uid, description=None, state=None, metadata=None):
        """
        Update a specific TODO item by its unique identifier (UID).

        This method should be implemented by subclasses to update a TODO item.

        :param uid: The unique identifier of the TODO item.
        :param description: Optional new description for the TODO item.
        :param state: Optional new state for the TODO item.
        :param metadata: Optional new metadata for the TODO item.
        """
        pass

class InMemoryTodoDB(TodoDB):
    """
    In-memory implementation of the TODO database.

    This class provides an in-memory storage for TODO items, useful for testing and development.
    """

    def __init__(self, state=None):
        """
        Initialize the in-memory TODO database.

        :param state: Optional initial state for the database. If not provided, an empty state is used.
        """
        if state is None:
            state = {}
        self._state = state

    def list_all_items(self):
        """
        List all TODO items for all users.

        :return: A list of all TODO items.
        """
        all_items = []
        for username in self._state:
            all_items.extend(self.list_items(username))
        return all_items

    def list_items(self, username=DEFAULT_USERNAME):
        """
        List all TODO items for a specific user.

        :param username: The username of the user. Defaults to 'default'.
        :return: A list of TODO items for the user.
        """
        return self._state.get(username, {}).values()

    def add_item(self, description, metadata=None, username=DEFAULT_USERNAME):
        """
        Add a new TODO item for a specific user.

        :param description: The description of the TODO item.
        :param metadata: Optional metadata for the TODO item.
        :param username: The username of the user. Defaults to 'default'.
        :return: The unique identifier (UID) of the newly added TODO item.
        """
        if username not in self._state:
            self._state[username] = {}
        uid = str(uuid4())
        self._state[username][uid] = {
            'uid': uid,
            'description': description,
            'state': 'unstarted',
            'metadata': metadata if metadata is not None else {},
            'username': username
        }
        return uid

    def get_item(self, uid, username=DEFAULT_USERNAME):
        """
        Get a specific TODO item for a specific user by its unique identifier (UID).

        :param uid: The unique identifier of the TODO item.
        :param username: The username of the user. Defaults to 'default'.
        :return: The TODO item with the given UID.
        """
        return self._state[username][uid]

    def delete_item(self, uid, username=DEFAULT_USERNAME):
        """
        Delete a specific TODO item for a specific user by its unique identifier (UID).

        :param uid: The unique identifier of the TODO item.
        :param username: The username of the user. Defaults to 'default'.
        """
        del self._state[username][uid]

    def update_item(self, uid, description=None, state=None, metadata=None, username=DEFAULT_USERNAME):
        """
        Update a specific TODO item for a specific user by its unique identifier (UID).

        :param uid: The unique identifier of the TODO item.
        :param description: Optional new description for the TODO item.
        :param state: Optional new state for the TODO item.
        :param metadata: Optional new metadata for the TODO item.
        :param username: The username of the user. Defaults to 'default'.
        """
        item = self._state[username][uid]
        if description is not None:
            item['description'] = description
        if state is not None:
            item['state'] = state
        if metadata is not None:
            item['metadata'] = metadata

class DynamoDBTodo(TodoDB):
    """
    DynamoDB implementation of the TODO database.

    This class provides a DynamoDB storage for TODO items.
    """

    def __init__(self, table_resource):
        """
        Initialize the DynamoDB TODO database.

        :param table_resource: The DynamoDB table resource.
        """
        self._table = table_resource

    def list_all_items(self):
        """
        List all TODO items for all users.

        :return: A list of all TODO items.
        """
        response = self._table.scan()
        return response['Items']

    def list_items(self, username=DEFAULT_USERNAME):
        """
        List all TODO items for a specific user.

        :param username: The username of the user. Defaults to 'default'.
        :return: A list of TODO items for the user.
        """
        response = self._table.query(
            KeyConditionExpression=Key('username').eq(username)
        )
        return response['Items']

    def add_item(self, description, metadata=None, username=DEFAULT_USERNAME):
        """
        Add a new TODO item for a specific user.

        :param description: The description of the TODO item.
        :param metadata: Optional metadata for the TODO item.
        :param username: The username of the user. Defaults to 'default'.
        :return: The unique identifier (UID) of the newly added TODO item.
        """
        uid = str(uuid4())
        self._table.put_item(
            Item={
                'username': username,
                'uid': uid,
                'description': description,
                'state': 'unstarted',
                'metadata': metadata if metadata is not None else {},
            }
        )
        return uid

    def get_item(self, uid, username=DEFAULT_USERNAME):
        """
        Get a specific TODO item for a specific user by its unique identifier (UID).

        :param uid: The unique identifier of the TODO item.
        :param username: The username of the user. Defaults to 'default'.
        :return: The TODO item with the given UID.
        """
        response = self._table.get_item(
            Key={
                'username': username,
                'uid': uid,
            },
        )
        return response['Item']

    def delete_item(self, uid, username=DEFAULT_USERNAME):
        """
        Delete a specific TODO item for a specific user by its unique identifier (UID).

        :param uid: The unique identifier of the TODO item.
        :param username: The username of the user. Defaults to 'default'.
        """
        self._table.delete_item(
            Key={
                'username': username,
                'uid': uid,
            }
        )

    def update_item(self, uid, description=None, state=None, metadata=None, username=DEFAULT_USERNAME):
        """
        Update a specific TODO item for a specific user by its unique identifier (UID).

        :param uid: The unique identifier of the TODO item.
        :param description: Optional new description for the TODO item.
        :param state: Optional new state for the TODO item.
        :param metadata: Optional new metadata for the TODO item.
        :param username: The username of the user. Defaults to 'default'.
        """
        # We could also use update_item() with an UpdateExpression.
        item = self.get_item(uid, username)
        if description is not None:
            item['description'] = description
        if state is not None:
            item['state'] = state
        if metadata is not None:
            item['metadata'] = metadata
        self._table.put_item(Item=item)