from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
from typing import List, Optional

app = FastAPI()

# Modèle Pydantic pour la validation
class UserCreate(BaseModel):
    name: str
    email: str

    @validator('email')
    def email_must_contain_at(cls, v):
        if '@' not in v:
            raise ValueError('Email must contain @')
        return v

class User(UserCreate):
    id: int

# Données mockées en mémoire
users_db: List[User] = [
    User(id=1, name="Alice", email="alice@example.com"),
    User(id=2, name="Bob", email="bob@example.com"),
    User(id=3, name="Charlie", email="charlie@example.com"),
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

# Nouveaux endpoints /users
@app.get("/users", response_model=List[User])
def get_users():
    return users_db

@app.post("/users", response_model=User)
def create_user(user: UserCreate):
    new_id = len(users_db) + 1
    new_user = User(id=new_id, name=user.name, email=user.email)
    users_db.append(new_user)
    return new_user
