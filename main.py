from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
from typing import List, Optional

app = FastAPI()

# Modèle utilisateur avec validation
class User(BaseModel):
    name: str
    email: str
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Name must not be empty')
        return v.strip()
    
    @validator('email')
    def email_must_contain_at(cls, v):
        if '@' not in v:
            raise ValueError('Email must contain @')
        return v

# Classe wrapper pour mocker la base de données
class UsersDatabase:
    def __init__(self):
        self._data = [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
            {"id": 3, "name": "Charlie", "email": "charlie@example.com"}
        ]
    
    def append(self, user):
        self._data.append(user)
    
    def __iter__(self):
        return iter(self._data)
    
    def __len__(self):
        return len(self._data)
    
    def __getitem__(self, index):
        return self._data[index]

# Instance de la base de données mockée
users_db = UsersDatabase()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

@app.post("/items")
def create_item(item: dict):
    return {"created": True, "item": item}

@app.get("/users", response_model=List[dict])
def get_users():
    """Retourne la liste des utilisateurs mockés"""
    return list(users_db)

@app.post("/users", response_model=dict, status_code=201)
def create_user(user: User):
    """Crée un nouvel utilisateur avec validation email"""
    new_id = len(users_db) + 1
    new_user = {"id": new_id, "name": user.name, "email": user.email}
    users_db.append(new_user)
    return {"created": True, "user": new_user}
