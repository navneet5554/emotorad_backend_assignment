# save this file as q1_final.py
from flask import Flask, request, jsonify
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from datetime import datetime
import uuid

app = Flask(_name_)

# Initialize MongoDB connection
def initialize_db():
    try:
        client = MongoClient('mongodb://admin:adminpassword@mongo1:27017,mongo2:27018,mongo3:27019/admin?replicaSet=rs0')
        client.admin.command('ping')  # Check if the connection is successful
        return client['contacts_db']
    except ConnectionFailure:
        print("Error: Unable to connect to the database.")
        return None

db = initialize_db()

# Endpoint to handle incoming requests
@app.route('/identify', methods=['POST'])
def process_payload():
    data = request.get_json()

    if not "email" and not "phoneNumber":
        return jsonify({'error': 'Email and phoneNumber must be provided in the payload'}), 400

    email = data.get('email')
    phone_number = data.get('phoneNumber')

    # Check if there's an existing contact with linkPrecedence 'primary' for the given email or phone number
    existing_contact = find_existing_primary_contact(email, phone_number)

    current_time = datetime.now()

    if existing_contact:
        # Convert existing 'primary' contact to 'secondary'
        linked_id = existing_contact.get('linkedId') or str(uuid.uuid4())  # Generate a new UUID if linkedId is None
        update_contact(existing_contact['id'], email, phone_number, "secondary", linked_id, current_time)

        # Create a new 'primary' contact
        new_contact_id = create_contact(email, phone_number, current_time)

        matching_records = find_records_by_email_or_phone(email, phone_number)
        emails = []
        phone_numbers = []
        for record in matching_records:
            emails.extend(record.get('emails', []))
            phone_numbers.extend(record.get('phoneNumbers', []))

        return jsonify({
            'primaryContactId': new_contact_id,
            'secondaryContactIds': existing_contact['id'],
            'emails': list(set(emails)),
            'phoneNumbers': list(set(phone_numbers))
        }), 200
    else:
        contact_id = create_contact(email, phone_number, current_time)
        return jsonify({
            'linkPrecedence': 'primary',
            'primaryContactId': contact_id,
            'secondaryContactIds': [],
            'emails': [email],
            'phoneNumbers': [phone_number]
        }), 200

# Endpoint to print all data in the database
@app.route('/all', methods=['GET'])
def get_all_data():
    contacts = list(db.contacts.find())

    # Convert ObjectId to string and UUID to string for each document
    for contact in contacts:
        contact['_id'] = str(contact['_id'])
        contact['id'] = str(contact['id'])

    return jsonify({
        'contacts': contacts,
    }), 200

# Endpoint to handle unavailable path
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return jsonify({"error": "Not Found", "message": f"The requested path '{path}' does not exist."}), 404

# Helper functions for MongoDB operations
def find_existing_primary_contact(email, phone_number):
    try:
        return db.contacts.find_one({"$or": [{"emails": email, "linkPrecedence": "primary"},
                                         {"phoneNumbers": phone_number, "linkPrecedence": "primary"}]})
    except Exception as e:
        print(f"Error while finding existing primary contact: {e}")
        return None

def update_contact(contact_id, email, phone_number, link_precedence, linked_id, updated_at):
    db.contacts.update_one(
        {"id": contact_id},
        {"$addToSet": {"emails": email, "phoneNumbers": phone_number},
         "$set": {"updatedAt": updated_at, "linkPrecedence": link_precedence, "linkedId": linked_id}}
    )

def create_contact(email, phone_number, created_at):
    contact_id = str(uuid.uuid4())  # Generate a new UUID for the contact ID
    result = db.contacts.insert_one({
        "id": contact_id,
        "emails": [email],
        "phoneNumbers": [phone_number],
        "createdAt": created_at,
        "updatedAt": created_at,
        "linkPrecedence": "primary",
        "linkedId": ""
    })
    return contact_id

def find_records_by_email_or_phone(email, phone_number):
    return list(db.contacts.find({"$or": [{"emails": email}, {"phoneNumbers": phone_number}]}))

if _name_ == '_main_':
    app.run(host='0.0.0.0', port=5000)
