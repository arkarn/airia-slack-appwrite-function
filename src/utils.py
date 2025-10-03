import os
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.query import Query

def get_db_client():
    client = Client()
    client.set_endpoint(os.environ.get("APPWRITE_FUNCTION_API_ENDPOINT"))
    client.set_project(os.environ.get("APPWRITE_FUNCTION_PROJECT_ID"))
    client.set_key(os.environ.get("APPWRITE_API_KEY"))
    return Databases(client)

def save_scheduled_message(thread_ts, channel, scheduled_message_id, post_at):
    db = get_db_client()
    db_id = os.environ.get("APPWRITE_DATABASE_ID")
    collection_id = os.environ.get("APPWRITE_COLLECTION_ID")
    
    db.create_document(db_id, collection_id, "unique()", {
        "thread_ts": thread_ts,
        "channel": channel,
        "scheduled_message_id": scheduled_message_id,
        "scheduled_post_at": post_at,
        "status": "pending"
    })

def get_pending_schedule(thread_ts):
    db = get_db_client()
    db_id = os.environ.get("APPWRITE_DATABASE_ID")
    collection_id = os.environ.get("APPWRITE_COLLECTION_ID")
    
    result = db.list_documents(db_id, collection_id, [
        Query.equal("thread_ts", thread_ts),
        Query.equal("status", "pending")
    ])
    return result["documents"][0] if result["documents"] else None

def mark_cancelled(doc_id):
    db = get_db_client()
    db_id = os.environ.get("APPWRITE_DATABASE_ID")
    collection_id = os.environ.get("APPWRITE_COLLECTION_ID")
    
    db.update_document(db_id, collection_id, doc_id, {"status": "cancelled"})

