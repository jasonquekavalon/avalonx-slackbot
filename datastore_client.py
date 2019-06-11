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

def get_item(client, kind, id):
    """Get a specific item from Datastore by id"""
    # Code to get an item in Datastore ;)

    query = client.query(kind)
    message = query.fetch(id)
    return message

    #message_id = str(uuid.uuid4())
    #message_key = client.key(kind, message_id)
    #query = client.query(kind)
    #message_entity = datastore.Entity(query)
    #return message_entity.key
      # Replace this with `return "whatever you want to return when done"`
pass 

# to indicate the task is complete
def mark_done(client, task_id):
    with client.transaction():
        key = client.key('message', task_id)
        task = client.get(key)

        if not task:
            raise ValueError(
                'Task {} does not exist.'.format(task_id))

        task['done'] = True

        client.put(task)

