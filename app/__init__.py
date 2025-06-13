from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from werkzeug.security import generate_password_hash # <-- Ця строка повинна бути тут, поруч з іншими імпортами на початку файла

app = Flask(__name__)

# Секретний ключ для сесій (необхідно для session, flash тощо)
app.config['SECRET_KEY'] = 'dev_1234567890_animeshop' # замінити у продакшені на безпечний

# Шлях до SQLite бази даних
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, '../anime.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Ініціалізація SQLAlchemy та Flask-Migrate
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Імпорт маршрутів та моделей тут, після ініціалізації app та db
from app import routes, models

# --- Нова функція для створення адміністратора ---
def _create_admin_user_if_not_exists(app_instance):
    """
    Створює користувача-адміністратора, якщо він ще не існує.
    Ця функція повинна викликатися тільки після того, як таблиця 'User' буде створена.
    """
    with app_instance.app_context():
        # Якщо ви хочете, щоб ця логіка працювала тільки коли додаток не в режимі тестування
        # (щоб тести могли самі створювати користувачів, не перетинаючись з цією логікою)
        if not app_instance.config.get('TESTING', False):
            from app.models import User # Імпортуємо User тут, щоб уникнути цилічних імпортів на верхньому рівні
            admin_email = "animeshop_admin@gmail.com"
            admin = User.query.filter_by(email=admin_email).first()
            if not admin:
                admin = User(
                    email=admin_email,
                    name="Admin",
                    password_hash=generate_password_hash("admin_password"), # Змініть на надійний пароль
                    role="admin"
                )
                db.session.add(admin)
                db.session.commit()
                print(f"Адміністратор {admin_email} створений.")
            else:
                print(f"Адміністратор {admin_email} вже існує.")

# Цей блок виконається під час запуску додатку
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        _create_admin_user_if_not_exists(app)
    app.run(debug=True)

