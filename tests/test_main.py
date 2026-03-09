import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app, users_db, UserCreate, User

client = TestClient(app)


class TestRoot:
    """Tests pour l'endpoint GET /"""

    def test_read_root(self):
        """Test que la racine retourne le bon message"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello World"}


class TestItems:
    """Tests pour les endpoints /items"""

    def test_read_item_without_query(self):
        """Test GET /items/{item_id} sans paramètre q"""
        response = client.get("/items/5")
        assert response.status_code == 200
        assert response.json() == {"item_id": 5, "q": None}

    def test_read_item_with_query(self):
        """Test GET /items/{item_id} avec paramètre q"""
        response = client.get("/items/3?q=test")
        assert response.status_code == 200
        assert response.json() == {"item_id": 3, "q": "test"}

    def test_create_item(self):
        """Test POST /items pour créer un item"""
        item_data = {"name": "Test Item", "price": 10.99}
        response = client.post("/items", json=item_data)
        assert response.status_code == 200
        assert response.json()["created"] is True
        assert response.json()["item"] == item_data


class TestUsers:
    """Tests pour les endpoints /users"""

    def test_get_users(self):
        """Test GET /users retourne la liste des utilisateurs"""
        response = client.get("/users")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
        assert data[0]["id"] == 1
        assert data[0]["name"] == "Alice"
        assert data[0]["email"] == "alice@example.com"

    def test_get_users_returns_user_objects(self):
        """Test que les utilisateurs ont tous les champs requis"""
        response = client.get("/users")
        assert response.status_code == 200
        users = response.json()
        for user in users:
            assert "id" in user
            assert "name" in user
            assert "email" in user

    @patch("main.users_db", new_callable=list)
    def test_create_user(self, mock_db):
        """Test POST /users pour créer un nouvel utilisateur"""
        # Pré-remplir le mock avec les utilisateurs initiaux
        mock_db.extend([
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
            {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
        ])
        
        new_user = {"name": "David", "email": "david@example.com"}
        response = client.post("/users", json=new_user)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "David"
        assert data["email"] == "david@example.com"
        assert data["id"] == 4  # Premier utilisateur ajouté

    def test_create_user_invalid_email(self):
        """Test que la validation de l'email rejette les emails sans @"""
        invalid_user = {"name": "Test", "email": "invalid-email.com"}
        response = client.post("/users", json=invalid_user)
        assert response.status_code == 422  # Validation Error


class TestUserCreateValidator:
    """Tests unitaires pour le validator d'email Pydantic"""

    def test_valid_email(self):
        """Test qu'un email valide est accepté"""
        user = UserCreate(name="Test", email="test@example.com")
        assert user.email == "test@example.com"

    def test_email_without_at_raises_error(self):
        """Test qu'un email sans @ lève une ValueError"""
        with pytest.raises(ValueError) as exc_info:
            UserCreate(name="Test", email="invalid-email.com")
        assert "Email must contain @" in str(exc_info.value)

    def test_email_with_at_passes(self):
        """Test que plusieurs emails valides passent la validation"""
        valid_emails = ["a@b.com", "test@domain.org", "user@sub.domain.io"]
        for email in valid_emails:
            user = UserCreate(name="Test", email=email)
            assert user.email == email


class TestUserModel:
    """Tests pour le modèle User"""

    def test_user_model_creation(self):
        """Test la création d'un objet User complet"""
        user = User(id=1, name="Alice", email="alice@example.com")
        assert user.id == 1
        assert user.name == "Alice"
        assert user.email == "alice@example.com"

    def test_user_inherits_from_usercreate(self):
        """Test que User hérite de UserCreate"""
        user = User(id=5, name="Test", email="test@test.com")
        assert isinstance(user, UserCreate)
