import pytest
from app import app, db
from flask.testing import FlaskClient

@pytest.fixture(scope='module')
def test_client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

def test_index(test_client: FlaskClient):
    response = test_client.get('/')
    assert response.status_code == 200
    assert "AnimeShop" in response.data.decode("utf-8")

def test_register_get(test_client: FlaskClient):
    response = test_client.get('/register')
    assert response.status_code == 200
    assert "Зареєструватися" in response.data.decode("utf-8")

def test_login_get(test_client: FlaskClient):
    response = test_client.get('/login')
    assert response.status_code == 200
    assert "Увійти" in response.data.decode("utf-8")

def test_logout_redirect(test_client: FlaskClient):
    response = test_client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert "Ви вийшли з системи." in response.data.decode("utf-8")

def test_cart_get(test_client: FlaskClient):
    response = test_client.get('/cart')
    assert response.status_code == 200
    assert "кошик" in response.data.decode("utf-8").lower()

def test_favorites_redirect(test_client: FlaskClient):
    response = test_client.get('/favorites', follow_redirects=True)
    assert response.status_code == 200
    assert "увійдіть" in response.data.decode("utf-8").lower()

def test_products_get(test_client: FlaskClient):
    response = test_client.get('/products')
    assert response.status_code == 200
    assert "категорії" in response.data.decode("utf-8").lower()

def test_checkout_redirect(test_client: FlaskClient):
    response = test_client.get('/checkout', follow_redirects=True)
    assert response.status_code == 200
    assert "Ваш кошик порожній." in response.data.decode("utf-8")