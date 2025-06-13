import os
import shutil
import pytest
from werkzeug.security import generate_password_hash
from app import db
from app.models import User, Category, Product


@pytest.fixture(scope='session')
def app():
    from app import app as real_app  # Імпортуємо вже створений app з app/routes.py

    test_static_dir = os.path.join(os.getcwd(), 'test_static')
    test_product_img_dir = os.path.join(test_static_dir, 'img', 'products')
    os.makedirs(test_product_img_dir, exist_ok=True)

    real_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'UPLOAD_FOLDER': test_product_img_dir,
        'SECRET_KEY': 'test_secret_key'
    })

    with real_app.app_context():
        db.create_all()
        if not Category.query.first():
            categories = [
                Category(name="Фігурки з аніме", description="Колекційні фігурки за мотивами аніме."),
                Category(name="Фігурки з комп'ютерних ігор", description="Колекційні фігурки за мотивами відеоігор."),
                Category(name="Брелоки", description="Яскраві брелоки для шанувальників."),
                Category(name="Світильники", description="Оригінальні світильники для дому.")
            ]
            db.session.add_all(categories)
            db.session.commit()
        yield real_app

        db.drop_all()

    shutil.rmtree(test_static_dir, ignore_errors=True)


@pytest.fixture(scope='function')
def client(app):
    return app.test_client()


@pytest.fixture(scope='function')
def init_database(app):
    with app.app_context():
        db.session.begin_nested()
        yield db.session
        db.session.rollback()


@pytest.fixture(autouse=True)
def clean_all_tables(init_database):
    for table in reversed(db.metadata.sorted_tables):
        init_database.execute(table.delete())
    init_database.commit()


@pytest.fixture
def new_user(init_database):
    user = User(
        name='Test User',
        email='test_user@example.com',
        password_hash=generate_password_hash('password123'),
        role='customer'
    )
    init_database.add(user)
    init_database.commit()
    return user


@pytest.fixture
def admin_user(init_database):
    user = User(
        name='Test Admin',
        email='test_admin@example.com',
        password_hash=generate_password_hash('adminpassword'),
        role='admin'
    )
    init_database.add(user)
    init_database.commit()
    return user


@pytest.fixture
def db_session(init_database):
    return init_database


@pytest.fixture
def create_test_user(init_database):
    user = User(
        name='Test User',
        email='testuser@example.com',
        password_hash=generate_password_hash('password123'),
        role='customer'
    )
    init_database.add(user)
    init_database.commit()
    return user


@pytest.fixture
def login_user(client):
    def do_login(email, password):
        return client.post('/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)
    return do_login


@pytest.fixture
def create_test_product(init_database):
    category = Category.query.first()
    if not category:
        category = Category(name="Test Category", description="A category for testing.")
        init_database.add(category)
        init_database.commit()

    product = Product(
        name='Test Product',
        description='Test Description',
        price=100.0,
        stock=10,
        category_id=category.id,
        manufacturer='Test Manufacturer'
    )
    init_database.add(product)
    init_database.commit()
    return product


@pytest.fixture
def create_test_admin(init_database):
    admin = User(
        name='Test Admin',
        email='test_admin@example.com',
        password_hash=generate_password_hash('adminpassword'),
        role='admin'
    )
    init_database.add(admin)
    init_database.commit()
    return admin
