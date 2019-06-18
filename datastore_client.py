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


ds_id = str(uuid.uuid4())
def add_item(client, kind, data):
    """
    Adds an item to Datastore
    :param client: the Datastore client object
    :param kind: the entity type in Datastore
    :param data: `dict` of item to store in Datastore
    :return:
    """
      # Generate a unique id for each entry
    key = client.key(kind, ds_id)

    entity = datastore.Entity(key)

    entity.update(data)

    client.put(entity)

    return entity.key

def get_message(client, kind, id):
    """Get a specific item from Datastore by id"""
    # Code to get an item in Datastore ;)

    print(id)
    key = client.key('message', id)
    message = client.get(key)
    return message.get("message")
