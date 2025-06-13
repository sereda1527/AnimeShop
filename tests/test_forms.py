import pytest
from werkzeug.datastructures import FileStorage, MultiDict
from app.forms import RegistrationForm, LoginForm, ProductForm, CheckoutForm
from app.models import Category
import os

def test_registration_form_valid(app):
    with app.app_context():
        form = RegistrationForm(
            data=dict(
                name='TestUser',
                email='test@example.com',
                password='password123',
                confirm_password='password123'
            )
        )
        assert form.validate()

def test_registration_form_invalid_email(app):
    with app.app_context():
        form = RegistrationForm(
            data=dict(
                name='TestUser',
                email='invalid-email',
                password='password123',
                confirm_password='password123'
            )
        )
        assert not form.validate()
        assert 'email' in form.errors

def test_registration_form_password_mismatch(app):
    with app.app_context():
        form = RegistrationForm(
            data=dict(
                name='TestUser',
                email='test@example.com',
                password='password123',
                confirm_password='password456'
            )
        )
        assert not form.validate()
        assert 'confirm_password' in form.errors

def test_login_form_valid(app):
    with app.app_context():
        form = LoginForm(
            data=dict(
                email='test@example.com',
                password='password123'
            )
        )
        assert form.validate()

def test_login_form_invalid_email(app):
    with app.app_context():
        form = LoginForm(
            data=dict(
                email='invalid-email',
                password='password123'
            )
        )
        assert not form.validate()
        assert 'email' in form.errors

def test_login_form_missing_data(app):
    with app.app_context():
        form = LoginForm(
            data=dict(
                email='',
                password=''
            )
        )
        assert not form.validate()
        assert 'email' in form.errors
        assert 'password' in form.errors

def test_product_form_valid(app, init_database):
    with app.app_context():
        # Create a category first
        category = Category(name="Test Category", description="A category for testing.")
        init_database.add(category)
        init_database.commit()

        # Simulate a file upload
        dummy_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'test_image.png')
        with open(dummy_file_path, 'wb') as f:
            f.write(b'dummy_image_content')

        with open(dummy_file_path, 'rb') as fp:
            form = ProductForm(
                MultiDict([
                    ('name', 'Test Product'),
                    ('description', 'This is a test description.'),
                    ('price', '100.00'),
                    ('stock', '10'),
                    ('manufacturer', 'Test Manufacturer'),
                    ('country_of_origin', 'Test Country'),
                    ('material', 'Plastic'),
                    ('length', 10.0),
                    ('weight', 500.0),
                    ('height', 20.0),
                    ('width', 15.0),
                    ('category_id', category.id),
                    ('images', fp)
                ])
            )
            assert form.validate(), form.errors
        os.remove(dummy_file_path)

def test_product_form_invalid_price(app):
    with app.app_context():
        form = ProductForm(
            data=dict(
                name='Test Product',
                description='Thi-s is a test description.',
                price= -10.00,
                stock='10',
                category_id=1 # Assuming category 1 exists
            )
        )
        assert not form.validate()
        assert 'price' in form.errors

def test_checkout_form_valid(app):
    with app.app_context():
        form = CheckoutForm(
            data=dict(
                full_name='John Doe',
                email='john.doe@example.com',
                phone='+380501234567',
                address='123 Main St',
                delivery_method='Нова Пошта',
                comment='Deliver carefully.'
            )
        )
        assert form.validate()

def test_checkout_form_invalid_email(app):
    with app.app_context():
        form = CheckoutForm(
            data=dict(
                full_name='John Doe',
                email='invalid-email',
                phone='+380501234567',
                address='123 Main St',
                delivery_method='Нова Пошта',
                comment=''
            )
        )
        assert not form.validate()
        assert 'email' in form.errors

def test_checkout_form_missing_data(app):
    with app.app_context():
        form = CheckoutForm(
            data=dict(
                full_name='',
                email='test@example.com',
                phone='',
                address='',
                delivery_method='Нова Пошта',
                comment=''
            )
        )
        assert not form.validate()
        assert 'full_name' in form.errors
        assert 'phone' in form.errors
        assert 'address' in form.errors