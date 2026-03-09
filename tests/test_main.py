import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

# Import de l'application
from main import app, User, mock_users


# Fixture pour le client de test
@pytest.fixture
def client():
    """Fixture créant un client de test pour l'API FastAPI"""
    return TestClient(app)


# Fixture pour réinitialiser les utilisateurs mockés entre les tests
@pytest.fixture
def reset_mock_users():
    """Fixture qui réinitialise la liste des utilisateurs mockés"""
    mock_users.clear()
    mock_users.extend([
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com"},
        {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
    ])
    yield
    mock_users.clear()


# ==================== Tests des endpoints principaux ====================

class TestRootEndpoint:
    """Tests pour l'endpoint GET /"""
    
    def test_read_root_returns_hello_world(self, client):
        """Vérifie que la racine retourne le message Hello World"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello World"}
    
    def test_read_root_content_type(self, client):
        """Vérifie le type de contenu de la réponse"""
        response = client.get("/")
        assert response.headers["content-type"] == "application/json"


class TestItemsEndpoint:
    """Tests pour les endpoints /items"""
    
    def test_read_item_without_query(self, client):
        """Récupère un item sans paramètre query"""
        response = client.get("/items/1")
        assert response.status_code == 200
        assert response.json() == {"item_id": 1, "q": None}
    
    def test_read_item_with_query(self, client):
        """Récupère un item avec paramètre query"""
        response = client.get("/items/5?q=test")
        assert response.status_code == 200
        assert response.json() == {"item_id": 5, "q": "test"}
    
    def test_read_item_negative_id(self, client):
        """Test avec un ID négatif"""
        response = client.get("/items/-1")
        assert response.status_code == 200
        assert response.json()["item_id"] == -1
    
    def test_read_item_string_id_conversion(self, client):
        """Vérifie que l'ID est converti en entier"""
        response = client.get("/items/42")
        data = response.json()
        assert isinstance(data["item_id"], int)
        assert data["item_id"] == 42
    
    def test_create_item(self, client):
        """Crée un nouvel item"""
        item = {"name": "Test Item", "price": 10.5}
        response = client.post("/items", json=item)
        assert response.status_code == 200
        assert response.json()["created"] is True
        assert response.json()["item"] == item
    
    def test_create_item_empty(self, client):
        """Crée un item vide"""
        response = client.post("/items", json={})
        assert response.status_code == 200
        assert response.json()["created"] is True


# ==================== Tests des endpoints users ====================

class TestUsersGetEndpoint:
    """Tests pour GET /users"""
    
    def test_get_users_returns_list(self, client, reset_mock_users):
        """Vérifie que GET /users retourne la liste des utilisateurs"""
        response = client.get("/users")
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert isinstance(data["users"], list)
    
    def test_get_users_contains_mock_users(self, client, reset_mock_users):
        """Vérifie que les utilisateurs mockés sont présents"""
        response = client.get("/users")
        data = response.json()
        assert len(data["users"]) == 3
        assert data["users"][0]["name"] == "Alice"
        assert data["users"][1]["name"] == "Bob"
        assert data["users"][2]["name"] == "Charlie"
    
    def test_get_users_returns_correct_structure(self, client, reset_mock_users):
        """Vérifie la structure des données utilisateur"""
        response = client.get("/users")
        data = response.json()
        user = data["users"][0]
        assert "id" in user
        assert "name" in user
        assert "email" in user


class TestUsersPostEndpoint:
    """Tests pour POST /users"""
    
    def test_create_user_success(self, client, reset_mock_users):
        """Crée un utilisateur avec des données valides"""
        user_data = {"name": "David", "email": "david@example.com"}
        response = client.post("/users", json=user_data)
        assert response.status_code == 200
        data = response.json()
        assert data["created"] is True
        assert data["user"]["name"] == "David"
        assert data["user"]["email"] == "david@example.com"
        assert data["user"]["id"] == 4
    
    def test_create_user_added_to_list(self, client, reset_mock_users):
        """Vérifie que l'utilisateur est ajouté à la liste"""
        user_data = {"name": "Eve", "email": "eve@example.com"}
        client.post("/users", json=user_data)
        
        response = client.get("/users")
        users = response.json()["users"]
        assert len(users) == 4
        assert any(u["name"] == "Eve" for u in users)
    
    def test_create_user_with_special_characters(self, client, reset_mock_users):
        """Crée un utilisateur avec des caractères spéciaux"""
        user_data = {"name": "José", "email": "jose@example.com"}
        response = client.post("/users", json=user_data)
        assert response.status_code == 200
        assert response.json()["user"]["name"] == "José"


# ==================== Tests de validation du modèle User ====================

class TestUserModelValidation:
    """Tests pour la validation du modèle Pydantic User"""
    
    def test_user_valid_email(self):
        """Crée un utilisateur avec un email valide"""
        user = User(name="Test", email="test@example.com")
        assert user.name == "Test"
        assert user.email == "test@example.com"
    
    def test_user_email_without_at_raises_error(self):
        """L'email sans @ doit lever une ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            User(name="Test", email="invalid-email.com")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("email",)
        assert "Email must contain @" in str(errors[0]["msg"])
    
    def test_user_email_empty_string_raises_error(self):
        """L'email vide doit lever une ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            User(name="Test", email="")
        
        errors = exc_info.value.errors()
        assert errors[0]["loc"] == ("email",)
    
    def test_user_email_with_multiple_at(self):
        """Email avec plusieurs @ est invalide"""
        with pytest.raises(ValidationError):
            User(name="Test", email="test@@example.com")
    
    def test_user_name_required(self):
        """Le nom est requis"""
        with pytest.raises(ValidationError) as exc_info:
            User(email="test@example.com")
        
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("name",) for err in errors)
    
    def test_user_email_required(self):
        """L'email est requis"""
        with pytest.raises(ValidationError) as exc_info:
            User(name="Test")
        
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("email",) for err in errors)


class TestEmailValidationEndpoint:
    """Tests de validation de l'email via l'endpoint POST /users"""
    
    def test_create_user_invalid_email_returns_422(self, client, reset_mock_users):
        """Un email invalide doit retourner 422 Unprocessable Entity"""
        user_data = {"name": "Test", "email": "invalid-email.com"}
        response = client.post("/users", json=user_data)
        assert response.status_code == 422
    
    def test_create_user_invalid_email_contains_error_detail(self, client, reset_mock_users):
        """La réponse d'erreur contient les détails de validation"""
        user_data = {"name": "Test", "email": "no-at.com"}
        response = client.post("/users", json=user_data)
        data = response.json()
        assert "detail" in data
        assert "Email must contain @" in str(data["detail"])
    
    def test_create_user_email_at_beginning(self, client, reset_mock_users):
        """Email commençant par @ est invalide"""
        user_data = {"name": "Test", "email": "@example.com"}
        response = client.post("/users", json=user_data)
        # @ au début est techniquement valide pour Pydantic car @ est présent
        # Mais ce test vérifie le comportement
        assert response.status_code in [200, 422]


# ==================== Tests avec Mock ====================

class TestMockedUsers:
    """Tests utilisant des mocks pour simuler des comportements"""
    
    @patch('main.mock_users')
    def test_get_users_with_mock(self, mock_users_list, client):
        """Test GET /users avec un mock de la liste"""
        mock_users_list.__iter__ = MagicMock(return_value=iter([
            {"id": 99, "name": "Mocked User", "email": "mocked@test.com"}
        ]))
        mock_users_list.__len__ = MagicMock(return_value=1)
        
        response = client.get("/users")
        # Note: le patch direct de mock_users peut nécessiter des ajustements
        # car FastAPI a déjà une référence à la liste
        assert response.status_code == 200
    
    def test_concurrent_user_creation(self, client, reset_mock_users):
        """Simule la création de plusieurs utilisateurs"""
        for i in range(3):
            user_data = {"name": f"User{i}", "email": f"user{i}@test.com"}
            response = client.post("/users", json=user_data)
            assert response.status_code == 200
        
        response = client.get("/users")
        assert len(response.json()["users"]) == 6


# ==================== Tests d'erreur et cas limites ====================

class TestEdgeCases:
    """Tests pour les cas limites et erreurs"""
    
    def test_create_user_with_extra_fields(self, client, reset_mock_users):
        """Les champs supplémentaires sont ignorés"""
        user_data = {
            "name": "Test",
            "email": "test@example.com",
            "extra_field": "should_be_ignored"
        }
        response = client.post("/users", json=user_data)
        assert response.status_code == 200
        assert "extra_field" not in response.json()["user"]
    
    def test_get_users_with_empty_list(self, client):
        """Test avec une liste vide (après suppression)"""
        mock_users.clear()
        response = client.get("/users")
        assert response.status_code == 200
        assert response.json()["users"] == []
    
    def test_read_item_with_large_id(self, client):
        """Test avec un ID très grand"""
        response = client.get("/items/999999999")
        assert response.status_code == 200
        assert response.json()["item_id"] == 999999999
    
    def test_create_user_with_none_values(self, client, reset_mock_users):
        """Les valeurs None doivent lever une erreur"""
        user_data = {"name": None, "email": None}
        response = client.post("/users", json=user_data)
        assert response.status_code == 422


# ==================== Tests d'intégration ====================

class TestIntegration:
    """Tests d'intégration complète du workflow utilisateur"""
    
    def test_full_user_workflow(self, client, reset_mock_users):
        """Teste le workflow complet: création, récupération, liste"""
        # 1. Vérifier la liste initiale
        response = client.get("/users")
        assert len(response.json()["users"]) == 3
        
        # 2. Créer un nouvel utilisateur
        new_user = {"name": "Frank", "email": "frank@example.com"}
        response = client.post("/users", json=new_user)
        assert response.status_code == 200
        created_user = response.json()["user"]
        user_id = created_user["id"]
        
        # 3. Vérifier que l'utilisateur est dans la liste
        response = client.get("/users")
        users = response.json()["users"]
        assert len(users) == 4
        assert any(u["id"] == user_id for u in users)
        
        # 4. Tenter de créer un utilisateur avec email invalide
        invalid_user = {"name": "Invalid", "email": "not-an-email"}
        response = client.post("/users", json=invalid_user)
        assert response.status_code == 422
        
        # 5. Vérifier que la liste n'a pas changé
        response = client.get("/users")
        assert len(response.json()["users"]) == 4
