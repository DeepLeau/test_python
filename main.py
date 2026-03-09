from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from typing import List, Optional

app = FastAPI()

# Modèle Pydantic pour la création d'utilisateur
class UserCreate(BaseModel):
    name: str
    email: str
    
    @field_validator('email')
    @classmethod
    def email_must_contain_at(cls, v):
        if '@' not in v:
            raise ValueError('Email doit contenir @')
        return v

# Modèle User pour la réponse
class User(BaseModel):
    id: int
    name: str
    email: str

# Données mockées
mocked_users = [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "email": "bob@example.com"},
    {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
]

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

@app.post("/items")
def create_item(item: dict):
    return {"created": True, "item": item}

@app.get("/users", response_model=List[User])
def get_users():
    """Retourne la liste de tous les utilisateurs mockés"""
    return mocked_users

@app.post("/users", response_model=User, status_code=201)
def create_user(user: UserCreate):
    """Crée un nouvel utilisateur avec validation d'email"""
    new_id = max(u["id"] for u in mocked_users) + 1
    new_user = {
        "id": new_id,
        "name": user.name,
        "email": user.email
    }
    mocked_users.append(new_user)
    return new_user
