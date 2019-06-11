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

def get_item(client, kind, message_id):
    """Get a specific item from Datastore by id"""
    # Code to get an item in Datastore ;)

    query = client.query(kind)
    message = query.fetch(message_id)
    return message

# to indicate the task is complete or pending 
""" def mark_done(client, data):
    with client.transaction():
        key = client.key('message', ds_id)
        task = client.get(key)

        if not task:
            raise ValueError(
                'Task {} does not exist.'.format(ds_id))
        else:

            if task['done'] = False:
                print("Pending") 

            else:
                client.put(task)
                print("Saved") """


