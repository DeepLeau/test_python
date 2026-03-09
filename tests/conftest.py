import pytest
import sys
import os

# Ajoute le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
def reset_mocked_users():
    """Fixture pour réinitialiser les utilisateurs mockés avant chaque test"""
    from main import mocked_users
    # Sauvegarde l'état initial
    initial_users = mocked_users.copy() if mocked_users else []
    # Nettoie la liste
    mocked_users.clear()
    # Remet les utilisateurs initiaux
    mocked_users.extend([
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com"},
        {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
    ])
    yield
    # Nettoie après le test
    mocked_users.clear()
    mocked_users.extend(initial_users)
