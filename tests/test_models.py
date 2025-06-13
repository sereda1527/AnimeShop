import pytest
from app.models import User
from werkzeug.security import check_password_hash, generate_password_hash

def test_new_user(new_user):
    assert new_user.email == 'test_user@example.com'
    assert new_user.name == 'Test User'
    assert new_user.role == 'customer'
    assert check_password_hash(new_user.password_hash, 'password123')

def test_admin_user(admin_user):
    assert admin_user.email == 'test_admin@example.com'
    assert admin_user.name == 'Test Admin'
    assert admin_user.role == 'admin'
    assert check_password_hash(admin_user.password_hash, 'adminpassword')

def test_set_password(new_user, db_session):
    new_user.password_hash = generate_password_hash('new_secret_password')
    db_session.commit()  # Зберігаємо зміну в базі
    assert check_password_hash(new_user.password_hash, 'new_secret_password')
    assert not check_password_hash(new_user.password_hash, 'wrong_password')

