from google.cloud import datastore
import datetime
import uuid

from log import log

logger = log.get_logger()

# project_id="alfred-dev-1"
def create_client(project_id, http=None):
    """
    Creates the one and only Datastore client (there should only be one of these in use)
    :param project_id: your GCP project name
    :return:
    """
    if http:
        return datastore.Client(project_id, _http=http)
    return datastore.Client(project_id)


def add_item(client, kind, data, friendly_id):

    # ds_id = str(uuid.uuid4())

    """
    Adds an item to Datastore
    :param client: the Datastore client object
    :param kind: the entity type in Datastore
    :param data: `dict` of item to store in Datastore
    :return:
    """
    """ ds_id = str(uuid.uuid4()) """ # Generate a unique id for each entry
    key = client.key(kind, friendly_id)
    entity = datastore.Entity(key)
    entity.update(data)
    client.put(entity)
    return friendly_id

def get_item(client, kind, id, item):
    key = client.key('message', id)
    message = client.get(key)
    return message.get("message")

# def get_status(client, kind, id):
#     key = client.key('message', id)
#     status = client.get(key)
#     return status.get("status")

def update_item(client, kind, data, id, type):
    key = client.key(kind, id)
    entity = client.get(key)
    entity[type] = data
    client.put(entity)
    return entity[type]


# def update_status(client, kind, data, id):
#     key = client.key(kind, id)
#     message = client.get(key)
#     for status in message:
#         message[status] = message[status]
#     message["status"] = data
#     client.put(message)
   
#     return message["status"]

# def update_message(client, kind, data, id):
#     key = client.key(kind, id)
#     Entity = client.get(key)
#     for message in Entity:
#         Entity[message] = Entity[message]
#     Entity["text"] = data
#     client.put(Entity)

#     return Entity["text"]

# def update_response(client, kind, data, id):
#     key = client.key(kind, id) 
#     message = client.get(key)
#     for response in message:
#         message[response] = message[response]
#     message["response"] = data
#     client.put(message)
   
#     return message["response"]

# def update_filename(client, kind, data, id):
#     key = client.key(kind, id)
#     Entity = client.get(key)
#     for message in Entity:
#         Entity[message] = Entity[message]
#     Entity["file name"] = data
#     client.put(Entity)

#     return Entity["file name"]  
