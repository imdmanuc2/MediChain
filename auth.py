# auth.py
import hashlib
import json
import os
from flask_login import UserMixin

USER_DB = 'users.json'

if not os.path.exists(USER_DB):
    with open(USER_DB, 'w') as f:
        json.dump({}, f)

def load_users():
    with open(USER_DB, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USER_DB, 'w') as f:
        json.dump(users, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    users = load_users()
    if username in users:
        return False
    users[username] = {
        "password": hash_password(password),
        "admin": False
    }
    save_users(users)
    return True

def verify_user(username, password):
    users = load_users()
    return (
        username in users and
        users[username]["password"] == hash_password(password)
    )

def is_admin_user(username):
    users = load_users()
    return users.get(username, {}).get("admin", False)

class User(UserMixin):
    def __init__(self, username):
        self.id = username
