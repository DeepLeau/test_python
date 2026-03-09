"""
Configuration pytest pour les tests FastAPI
"""
import pytest
import sys
import os

# Ajout du répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def anyio_backend():
    """Fixture pour les tests asynchrones (si nécessaire)"""
    return "asyncio"
