from google.cloud import datastore
import datetime
import uuid


# project_id="alfred-dev-1"
def create_client(project_id):
    """
    Creates the one and only Datastore client (there should only be one of these in use)
    :param project_id: your GCP project name
    :return:
    """
    return datastore.Client(project_id)


def get_item(client, kind, id):
    """Get a specific item from Datastore by id"""
    # Code to get an item in Datastore ;)
    pass  # Replace this with `return "whatever you want to return when done"`


def add_item(client, kind, data):
    """
    Adds an item to Datastore
    :param client: the Datastore client object
    :param kind: the entity type in Datastore
    :param data: `dict` of item to store in Datastore
    :return:
    """
    ds_id = str(uuid.uuid4())  # Generate a unique id for each entry
    key = client.key(kind, ds_id)

    entity = datastore.Entity(key)

    entity.update(data)

    client.put(entity)

    return entity.key


# to indicate the task is complete
def mark_done(client, task_id):
    with client.transaction():
        key = client.key('Task', task_id)
        task = client.get(key)

        if not task:
            raise ValueError(
                'Task {} does not exist.'.format(task_id))

        task['done'] = True

        client.put(task)

# Code in this scope will be run when you import this as a module, to avoid this, you can place it in a __main__ statement like so
if __name__ == '__main__':
    # Now this code will ONLY be executed when you run `datastore.py` instead of when you run `app.py` and import this file
    # alternatively, we could use this?
    datastore_client = datastore.Client()
    # The kind for the new entity
    kind = 'Task'
    # The name/ID for the new entity
    name = 'sampletask'
    # The Cloud Datastore key for the new entity
    task_key = datastore_client.key(kind, name)

    # Prepares the new entity
    task = datastore.Entity(key=task_key)
    task['description'] = 'message'

    # Saves the entity
    datastore_client.put(task)

    print('Saved {}: {}'.format(task.key.name, task['description']))
