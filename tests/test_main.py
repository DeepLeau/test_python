import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Import de l'application et des dépendances
from main import app, UserCreate, User, mocked_users


client = TestClient(app)


class TestRootEndpoint:
    """Tests pour l'endpoint GET /"""

    def test_read_root_returns_hello_world(self):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello World"}

    def test_read_root_content_type(self):
        response = client.get("/")
        assert response.headers["content-type"] == "application/json"


class TestItemsEndpoint:
    """Tests pour les endpoints /items"""

    def test_read_item_with_id(self):
        response = client.get("/items/42")
        assert response.status_code == 200
        data = response.json()
        assert data["item_id"] == 42
        assert data["q"] is None

    def test_read_item_with_query_param(self):
        response = client.get("/items/1?q=test")
        assert response.status_code == 200
        data = response.json()
        assert data["item_id"] == 1
        assert data["q"] == "test"

    def test_read_item_with_different_id(self):
        response = client.get("/items/999")
        assert response.status_code == 200
        assert response.json()["item_id"] == 999

    def test_create_item(self):
        test_item = {"name": "Test Item", "price": 10.99}
        response = client.post("/items", json=test_item)
        assert response.status_code == 200
        data = response.json()
        assert data["created"] is True
        assert data["item"] == test_item

    def test_create_item_empty_body(self):
        response = client.post("/items", json={})
        assert response.status_code == 200
        assert response.json()["created"] is True


class TestUsersEndpoint:
    """Tests pour les endpoints /users"""

    def setup_method(self):
        """Réinitialiser les utilisateurs mockés avant chaque test"""
        mocked_users.clear()
        mocked_users.extend([
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
            {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
        ])

    def test_get_users_returns_list(self):
        response = client.get("/users")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3

    def test_get_users_returns_correct_users(self):
        response = client.get("/users")
        data = response.json()
        assert data[0]["id"] == 1
        assert data[0]["name"] == "Alice"
        assert data[0]["email"] == "alice@example.com"

    def test_get_users_response_model(self):
        response = client.get("/users")
        # Vérifie que la réponse respecte le modèle User
        for user in response.json():
            assert "id" in user
            assert "name" in user
            assert "email" in user

    def test_create_user_success(self):
        new_user = {"name": "David", "email": "david@example.com"}
        response = client.post("/users", json=new_user)
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 4
        assert data["name"] == "David"
        assert data["email"] == "david@example.com"

    def test_create_user_added_to_list(self):
        new_user = {"name": "Eve", "email": "eve@example.com"}
        client.post("/users", json=new_user)
        response = client.get("/users")
        assert len(response.json()) == 4

    def test_create_user_increments_id(self):
        new_user = {"name": "Frank", "email": "frank@example.com"}
        response = client.post("/users", json=new_user)
        assert response.json()["id"] == 4

        # Créer un second utilisateur
        new_user2 = {"name": "Grace", "email": "grace@example.com"}
        response2 = client.post("/users", json=new_user2)
        assert response2.json()["id"] == 5


class TestEmailValidation:
    """Tests pour la validation de l'email"""

    def test_email_with_at_is_valid(self):
        user = UserCreate(name="Test", email="test@example.com")
        assert user.email == "test@example.com"

    def test_email_without_at_raises_error(self):
        with pytest.raises(ValueError) as exc_info:
            UserCreate(name="Test", email="invalid-email")
        assert "Email doit contenir @" in str(exc_info.value)

    def test_email_with_multiple_at_raises_error(self):
        with pytest.raises(ValueError):
            UserCreate(name="Test", email="test@@example.com")

    def test_email_empty_string_raises_error(self):
        with pytest.raises(ValueError):
            UserCreate(name="Test", email="")

    def test_email_only_at_raises_error(self):
        with pytest.raises(ValueError):
            UserCreate(name="Test", email="@")

    def test_email_with_subdomain_is_valid(self):
        user = UserCreate(name="Test", email="test@mail.example.com")
        assert user.email == "test@mail.example.com"


class TestUserCreateModel:
    """Tests pour le modèle UserCreate"""

    def test_user_create_with_valid_data(self):
        user = UserCreate(name="John", email="john@doe.com")
        assert user.name == "John"
        assert user.email == "john@doe.com"

    def test_user_create_name_is_required(self):
        with pytest.raises(ValueError):
            UserCreate(email="test@example.com")

    def test_user_create_email_is_required(self):
        with pytest.raises(ValueError):
            UserCreate(name="Test")


class TestUserModel:
    """Tests pour le modèle User"""

    def test_user_model_with_all_fields(self):
        user = User(id=1, name="Test", email="test@example.com")
        assert user.id == 1
        assert user.name == "Test"
        assert user.email == "test@example.com"

    def test_user_model_from_dict(self):
        data = {"id": 5, "name": "Test", "email": "test@example.com"}
        user = User(**data)
        assert user.id == 5


class TestMockedUsersData:
    """Tests pour les données mockées"""

    def test_mocked_users_initial_count(self):
        assert len(mocked_users) == 3

    def test_mocked_users_structure(self):
        for user in mocked_users:
            assert "id" in user
            assert "name" in user
            assert "email" in user

    def test_mocked_users_ids_are_unique(self):
        ids = [user["id"] for user in mocked_users]
        assert len(ids) == len(set(ids))


class TestWithMocks:
    """Tests utilisant des mocks pour isoler la logique"""

    @patch('main.mocked_users', [{"id": 1, "name": "Mocked", "email": "mocked@test.com"}])
    def test_get_users_with_mock(self):
        response = client.get("/users")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_create_user_with_mocked_max_id(self):
        with patch('main.max', return_value=3):
            new_user = {"name": "Test", "email": "test@example.com"}
            response = client.post("/users", json=new_user)
            assert response.status_code == 201
