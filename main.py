from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator

app = FastAPI()

# Modèle Pydantic pour la validation
class User(BaseModel):
    name: str
    email: str
    
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Email must contain @')
        return v

# Données mockées
mock_users = [
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

# Endpoints pour /users

@app.get("/users")
def get_users():
    """Retourne la liste de tous les utilisateurs mockés"""
    return {"users": mock_users}

@app.post("/users")
def create_user(user: User):
    """Crée un nouvel utilisateur avec validation de l'email"""
    new_id = len(mock_users) + 1
    new_user = {"id": new_id, "name": user.name, "email": user.email}
    mock_users.append(new_user)
    return {"created": True, "user": new_user}
