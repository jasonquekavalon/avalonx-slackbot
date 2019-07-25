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

def get_message(client, kind, id):
    """Get a specific message from Datastore by id"""
    key = client.key('message', id)
    message = client.get(key)
    return message.get("message")

def get_filename(client, kind, id):
    key = client.key('message', id)
    filename = client.get(key)
    return filename.get('file name')

def get_status(client, kind, id):

    key = client.key('message', id)
    status = client.get(key)
    return status.get("status")

def get_channelname(client, kind, id):
    key = client.key('message', id)
    channel_name = client.get(key)
    return channel_name.get("channel_name")

def get_saved_messages(client, kind, id):
    key = client.key('message', id)
    saved_messages = client.get(key)
    return saved_messages.get("text")

def get_saved_responses(client, kind, id):
    key = client.key('message', id)
    saved_responses = client.get(key)
    return saved_responses.get("response")

def update_status(client, kind, data, id):
    key = client.key(kind, id)
    message = client.get(key)
    for status in message:
        message[status] = message[status]
    message["status"] = data
    client.put(message)
   
    return message["status"]

def update_message(client, kind, data, id):
    key = client.key(kind, id)
    Entity = client.get(key)
    for message in Entity:
        Entity[message] = Entity[message]
    Entity["text"] = data
    client.put(Entity)

    return Entity["text"]

def update_response(client, kind, data, id):
    key = client.key(kind, id) 
    message = client.get(key)
    for response in message:
        message[response] = message[response]
    message["response"] = data
    client.put(message)
   
    return message["response"]

def update_filename(client, kind, data, id):
    key = client.key(kind, id)
    Entity = client.get(key)
    for message in Entity:
        Entity[message] = Entity[message]
    Entity["file name"] = data
    client.put(Entity)

    return Entity["file name"]    
