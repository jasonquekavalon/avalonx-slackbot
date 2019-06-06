from google.cloud import datastore
import datetime 

#project_id="alfred-dev-1" 
def create_client(project_id):
    return datastore.Client(project_id)

#to create new entity and store in database
def add_task(client, description):
    key = client.key('Task')

    task = datastore.Entity(
        key, exclude_from_indexes=['description'])

    task.update({
        'created': datetime.datetime.utcnow(),
        'description': description,
        'done': False
    })

    client.put(task)

    return task.key

#to indicate the task is complete
def mark_done(client, task_id):
    with client.transaction():
        key = client.key('Task', task_id)
        task = client.get(key)

        if not task:
            raise ValueError(
                'Task {} does not exist.'.format(task_id))

        task['done'] = True

        client.put(task)


#alternatively, we could use this?
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
