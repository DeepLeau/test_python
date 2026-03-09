import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

# Import de l'application depuis main.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app, User, users_db, UsersDatabase


@pytest.fixture
def client():
    """Fixture pour le client de test FastAPI"""
    return TestClient(app)


@pytest.fixture
def mock_users_db():
    """Fixture pour mocker la base de données utilisateurs"""
    with patch('main.users_db') as mock_db:
        # Configurer le mock pour retourner des données
        mock_db.__iter__ = lambda self: iter([
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
            {"id": 3, "name": "Charlie", "email": "charlie@example.com"}
        ])
        mock_db.__len__ = lambda self: 3
        mock_db.append = MagicMock()
        yield mock_db


class TestRootEndpoint:
    """Tests pour l'endpoint GET /"""

    def test_read_root_returns_hello_world(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello World"}

    def test_read_root_content_type(self, client):
        response = client.get("/")
        assert response.headers["content-type"] == "application/json"


class TestItemsEndpoint:
    """Tests pour les endpoints /items"""

    def test_read_item_with_id(self, client):
        response = client.get("/items/5")
        assert response.status_code == 200
        assert response.json() == {"item_id": 5, "q": None}

    def test_read_item_with_query_param(self, client):
        response = client.get("/items/3?q=test")
        assert response.status_code == 200
        assert response.json() == {"item_id": 3, "q": "test"}

    def test_read_item_zero_id(self, client):
        response = client.get("/items/0")
        assert response.status_code == 200
        assert response.json() == {"item_id": 0, "q": None}

    def test_create_item(self, client):
        item_data = {"name": "Test Item", "price": 10.99}
        response = client.post("/items", json=item_data)
        assert response.status_code == 200
        assert response.json()["created"] is True
        assert response.json()["item"] == item_data


class TestUserModel:
    """Tests pour le modèle User et ses validateurs"""

    def test_valid_user_creation(self):
        user = User(name="John", email="john@example.com")
        assert user.name == "John"
        assert user.email == "john@example.com"

    def test_name_validator_strips_whitespace(self):
        user = User(name="  John  ", email="john@example.com")
        assert user.name == "John"

    def test_name_validator_raises_on_empty_string(self):
        with pytest.raises(ValueError) as exc_info:
            User(name="", email="john@example.com")
        assert "Name must not be empty" in str(exc_info.value)

    def test_name_validator_raises_on_whitespace_only(self):
        with pytest.raises(ValueError) as exc_info:
            User(name="   ", email="john@example.com")
        assert "Name must not be empty" in str(exc_info.value)

    def test_email_validator_raises_without_at(self):
        with pytest.raises(ValueError) as exc_info:
            User(name="John", email="john.example.com")
        assert "Email must contain @" in str(exc_info.value)

    def test_email_validator_accepts_valid_email(self):
        user = User(name="John", email="john.doe+test@example.co.uk")
        assert user.email == "john.doe+test@example.co.uk"


class TestUsersDatabase:
    """Tests pour la classe UsersDatabase"""

    def test_users_database_append(self):
        db = UsersDatabase()
        initial_len = len(db)
        db.append({"id": 4, "name": "Test", "email": "test@example.com"})
        assert len(db) == initial_len + 1

    def test_users_database_iter(self):
        db = UsersDatabase()
        users_list = list(db)
        assert len(users_list) == 3
        assert users_list[0]["name"] == "Alice"

    def test_users_database_getitem(self):
        db = UsersDatabase()
        assert db[0]["name"] == "Alice"
        assert db[1]["name"] == "Bob"


class TestUsersEndpoints:
    """Tests pour les endpoints /users"""

    def test_get_users_returns_list(self, client, mock_users_db):
        response = client.get("/users")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == 3

    def test_get_users_returns_correct_data(self, client, mock_users_db):
        response = client.get("/users")
        users = response.json()
        assert users[0]["name"] == "Alice"
        assert users[0]["email"] == "alice@example.com"
        assert users[1]["name"] == "Bob"
        assert users[2]["name"] == "Charlie"

    def test_create_user_success(self, client, mock_users_db):
        user_data = {"name": "David", "email": "david@example.com"}
        response = client.post("/users", json=user_data)
        assert response.status_code == 201
        assert response.json()["created"] is True
        assert response.json()["user"]["name"] == "David"
        assert response.json()["user"]["email"] == "david@example.com"

    def test_create_user_validates_email_without_at(self, client):
        user_data = {"name": "David", "email": "davidexample.com"}
        response = client.post("/users", json=user_data)
        assert response.status_code == 422  # Validation Error

    def test_create_user_validates_empty_name(self, client):
        user_data = {"name": "", "email": "david@example.com"}
        response = client.post("/users", json=user_data)
        assert response.status_code == 422  # Validation Error

    def test_create_user_validates_whitespace_name(self, client):
        user_data = {"name": "   ", "email": "david@example.com"}
        response = client.post("/users", json=user_data)
        assert response.status_code == 422  # Validation Error

    def test_create_user_missing_email_field(self, client):
        user_data = {"name": "David"}
        response = client.post("/users", json=user_data)
        assert response.status_code == 422

    def test_create_user_missing_name_field(self, client):
        user_data = {"email": "david@example.com"}
        response = client.post("/users", json=user_data)
        assert response.status_code == 422


class TestIntegration:
    """Tests d'intégration complète"""

    def test_full_user_workflow(self, client, mock_users_db):
        # Vérifier que la liste initiale contient 3 utilisateurs
        response = client.get("/users")
        assert len(response.json()) == 3

        # Créer un nouvel utilisateur
        new_user = {"name": "Eve", "email": "eve@example.com"}
        response = client.post("/users", json=new_user)
        assert response.status_code == 201

        # Vérifier que l'utilisateur a été créé avec un ID
        created_user = response.json()["user"]
        assert created_user["id"] == 4
        assert created_user["name"] == "Eve"

    def test_root_and_items_endpoints_work_together(self, client):
        # Test de l'endpoint root
        response = client.get("/")
        assert response.status_code == 200

        # Test de l'endpoint items
        response = client.get("/items/1?q=test")
        assert response.status_code == 200
        assert response.json()["item_id"] == 1
