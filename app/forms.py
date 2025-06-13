from flask import current_app
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, MultipleFileField
from wtforms import (
    StringField, PasswordField, SubmitField, DecimalField,
    IntegerField, TextAreaField, SelectField
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange


class RegistrationForm(FlaskForm):
    name = StringField("Ім’я", validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Пароль", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField("Підтвердіть пароль", validators=[
        DataRequired(), EqualTo('password', message='Паролі не співпадають')])
    submit = SubmitField("Зареєструватися")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    submit = SubmitField("Увійти")


class ProductForm(FlaskForm):
    name = StringField("Назва товару", validators=[DataRequired(), Length(min=2, max=120)])
    description = TextAreaField("Опис", validators=[DataRequired(), Length(min=10)])
    price = DecimalField("Ціна", validators=[DataRequired(), NumberRange(min=0)])
    stock = IntegerField("Кількість на складі", validators=[DataRequired(), NumberRange(min=0)])
    manufacturer = StringField("Виробник", validators=[Length(max=100)])
    country_of_origin = StringField("Країна виробництва", validators=[Length(max=100)])
    material = StringField("Матеріал", validators=[Length(max=100)])
    length = DecimalField("Довжина (см)", places=2, validators=[NumberRange(min=0)], default=0, render_kw={"step": "1"})
    weight = DecimalField("Вага (г)", places=1, validators=[NumberRange(min=0)], default=0.0, render_kw={"step": "0.1"})
    height = DecimalField("Висота (см)", places=2, validators=[NumberRange(min=0)], default=0, render_kw={"step": "1"})
    width = DecimalField("Ширина (см)", places=2, validators=[NumberRange(min=0)], default=0, render_kw={"step": "1"})
    category_id = SelectField("Категорія", coerce=int)
    images = MultipleFileField("Зображення", validators=[
        FileAllowed(["jpg", "jpeg", "png", "webp"], "Дозволені лише зображення!")
    ])
    submit = SubmitField("Додати товар")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Динамічно завантажуємо категорії з бази даних.
        # Це повинно бути зроблено в контексті додатка.
        try:
            from app.models import Category
            with current_app.app_context():
                categories = Category.query.all()
                self.category_id.choices = [(c.id, c.name) for c in categories]
        except RuntimeError:
            # Це може статися під час ініціалізації додатку або в тестовому середовищі
            # без активного контексту додатка. Для тестів або первинного запуску,
            # можемо використовувати статичні значення або завантажити пізніше.
            # Якщо ви впевнені, що завжди буде активний контекст, цей блок можна прибрати.
            self.category_id.choices = [
                (1, "Фігурки з аніме"),
                (2, "Фігурки з комп'ютерних ігор"),
                (3, "Брелоки"),
                (4, "Світильники"),
            ]


class CheckoutForm(FlaskForm):
    full_name = StringField("ПІБ", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    phone = StringField("Телефон", validators=[DataRequired()])
    address = TextAreaField("Адреса доставки", validators=[DataRequired()])
    delivery_method = SelectField("Метод доставки", choices=[
        ("Нова Пошта", "Нова Пошта"),
        ("УкрПошта", "УкрПошта"),
        ("Кур'єр", "Кур'єр")
    ], validators=[DataRequired()])
    comment = TextAreaField("Коментар до замовлення")
    submit = SubmitField("Оформити замовлення")