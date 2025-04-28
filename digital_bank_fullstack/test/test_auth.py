# tests/test_auth.py (Pytest test file)
import pytest
from app.auth import AuthService, User

@pytest.fixture
def auth_service():
    return AuthService({"testuser": User("testuser", "password123")})

def test_login_successful(auth_service):
    assert auth_service.login_user("testuser", "password123") is True

def test_login_incorrect_password(auth_service):
    assert auth_service.login_user("testuser", "wrongpassword") is False

def test_login_user_not_found(auth_service):
    assert auth_service.login_user("nonexistentuser", "anypassword") is False

def test_login_with_empty_credentials(auth_service):
    assert auth_service.login_user("", "") is False

def test_login_with_empty_password(auth_service):
    assert auth_service.login_user("testuser", "") is False

def test_login_with_empty_username(auth_service):
    assert auth_service.login_user("", "password123") is False

def test_login_case_sensitive_username(auth_service):
    assert auth_service.login_user("TestUser", "password123") is False

def test_login_case_sensitive_password(auth_service):
    auth_service.users["anothertest"] = User("anothertest", "Password123")
    assert auth_service.login_user("anothertest", "password123") is False