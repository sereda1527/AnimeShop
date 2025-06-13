import os
from functools import wraps
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import func

from app import app, db
from app.forms import RegistrationForm, LoginForm, ProductForm, CheckoutForm  # Імпортуємо CheckoutForm
from app.models import (
    User,
    Product,
    Category,
    ProductImage,
    Review,
    CartItem,
    Favorite,
    Order,
    OrderItem
)

# Константа для збереження зображень
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'img', 'products')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# Декоратор для перевірки адміністратора
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_role") != "admin":
            flash("Доступ лише для адміністратора", "danger")
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return decorated_function


@app.route("/")
def index():
    products = Product.query.limit(8).all()  # Showing some products on the main page
    return render_template("index.html", products=products)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(name=form.name.data, email=form.email.data, password_hash=hashed_password, role="customer")
        db.session.add(new_user)
        db.session.commit()
        flash("Реєстрація успішна! Тепер ви можете увійти.", "success")
        return redirect(url_for("login"))
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password.data, form.password.data):
            session["user_id"] = user.id
            session["user_name"] = user.name
            session["user_role"] = user.role
            flash("Ви успішно увійшли!", "success")
            return redirect(url_for("index"))
        else:
            flash("Неправильний Email або пароль.", "danger")
    return render_template("login.html", form=form)


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("user_name", None)
    session.pop("user_role", None)
    flash("Ви вийшли з системи.", "info")
    return redirect(url_for("index"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    return render_template("admin/dashboard.html")


@app.route("/admin/products")
@admin_required
def admin_products():
    products = Product.query.all()
    return render_template("admin/products.html", products=products)


@app.route("/admin/add_product", methods=["GET", "POST"])
@admin_required
def admin_add_product():
    form = ProductForm()
    # Заповнюємо вибір категорій
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]

    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            stock=form.stock.data,
            manufacturer=form.manufacturer.data,
            country_of_origin=form.country_of_origin.data,
            material=form.material.data,
            length=form.length.data,
            weight=form.weight.data,
            height=form.height.data,
            width=form.width.data,
            category_id=form.category_id.data
        )
        db.session.add(product)
        db.session.commit()

        # Зберігаємо зображення
        if form.images.data:
            for image_file in request.files.getlist('images'):
                if image_file:
                    filename = secure_filename(image_file.filename)
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    image_file.save(file_path)
                    product_image = ProductImage(product_id=product.id, url=f"/static/img/products/{filename}",
                                                 filename=filename)
                    db.session.add(product_image)
        db.session.commit()
        flash("Товар успішно додано!", "success")
        return redirect(url_for("admin_products"))
    return render_template("admin/add_product.html", form=form)


@app.route("/admin/edit_product/<int:product_id>", methods=["GET", "POST"])
@admin_required
def admin_edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]

    if form.validate_on_submit():
        form.populate_obj(product)
        # Оновлення зображень
        if form.images.data:
            # Видаляємо старі зображення
            for old_image in product.images:
                try:
                    os.remove(os.path.join(UPLOAD_FOLDER, old_image.filename))
                except OSError as e:
                    print(f"Error deleting old image: {e}")
                db.session.delete(old_image)
            product.images.clear()  # Очищаємо зв'язок у колекції

            # Додаємо нові зображення
            for image_file in request.files.getlist('images'):
                if image_file:
                    filename = secure_filename(image_file.filename)
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    image_file.save(file_path)
                    product_image = ProductImage(product_id=product.id, url=f"/static/img/products/{filename}",
                                                 filename=filename)
                    db.session.add(product_image)

        product.updated_at = datetime.utcnow()
        db.session.commit()
        flash("Товар успішно оновлено!", "success")
        return redirect(url_for("admin_products"))
    return render_template("admin/edit_product.html", form=form, product=product)


@app.route("/admin/delete_product/<int:product_id>", methods=["POST"])
@admin_required
def admin_delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    # Видаляємо зображення з файлової системи
    for image in product.images:
        try:
            os.remove(os.path.join(UPLOAD_FOLDER, image.filename))
        except OSError as e:
            print(f"Error deleting image file: {e}")
    db.session.delete(product)
    db.session.commit()
    flash("Товар успішно видалено!", "success")
    return redirect(url_for("admin_products"))


@app.route("/products")
def products():
    category_id = request.args.get('category_id', type=int)
    search_query = request.args.get('search', type=str)

    products_query = Product.query

    if category_id:
        products_query = products_query.filter_by(category_id=category_id)

    if search_query:
        products_query = products_query.filter(
            func.lower(Product.name).contains(func.lower(search_query)) |
            func.lower(Product.description).contains(func.lower(search_query))
        )

    products = products_query.all()
    categories = Category.query.all()
    return render_template("products.html", products=products, categories=categories,
                           selected_category=category_id, search_query=search_query)


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    reviews = Review.query.filter_by(product_id=product_id).order_by(Review.created_at.desc()).all()
    return render_template("product_detail.html", product=product, reviews=reviews)


@app.route("/add_to_cart/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    if "user_id" not in session:
        flash("Будь ласка, увійдіть, щоб додати товар до кошика.", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get("quantity", 1))

    cart_item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()

    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)
    db.session.commit()
    flash(f"{quantity} x {product.name} додано до кошика!", "success")
    return redirect(url_for("cart"))


@app.route("/cart")
def cart():
    if "user_id" not in session:
        return render_template("cart.html", cart_items=[])  # Empty cart for guests or redirect
    user_id = session["user_id"]
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    return render_template("cart.html", cart_items=cart_items)


@app.route("/update_cart/<int:item_id>", methods=["POST"])
def update_cart(item_id):
    if "user_id" not in session:
        flash("Будь ласка, увійдіть.", "warning")
        return redirect(url_for("login"))

    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.user_id != session["user_id"]:
        flash("Несанкціонований доступ.", "danger")
        return redirect(url_for("cart"))

    quantity = int(request.form.get("quantity"))
    if quantity <= 0:
        db.session.delete(cart_item)
        flash("Товар видалено з кошика.", "info")
    else:
        cart_item.quantity = quantity
        flash("Кількість оновлено.", "success")
    db.session.commit()
    return redirect(url_for("cart"))


@app.route("/remove_from_cart/<int:item_id>", methods=["POST"])
def remove_from_cart(item_id):
    if "user_id" not in session:
        flash("Будь ласка, увійдіть.", "warning")
        return redirect(url_for("login"))

    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.user_id != session["user_id"]:
        flash("Несанкціонований доступ.", "danger")
        return redirect(url_for("cart"))

    db.session.delete(cart_item)
    db.session.commit()
    flash("Товар видалено з кошика.", "info")
    return redirect(url_for("cart"))


@app.route("/add_to_favorites/<int:product_id>", methods=["POST"])
def add_to_favorites(product_id):
    if "user_id" not in session:
        flash("Будь ласка, увійдіть, щоб додати товар до обраних.", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    favorite = Favorite.query.filter_by(user_id=user_id, product_id=product_id).first()

    if not favorite:
        new_favorite = Favorite(user_id=user_id, product_id=product_id)
        db.session.add(new_favorite)
        db.session.commit()
        flash("Товар додано до обраних!", "success")
    else:
        flash("Товар вже є у вашому списку обраних.", "info")
    return redirect(url_for("product_detail", product_id=product_id))


@app.route("/remove_from_favorites/<int:product_id>", methods=["POST"])
def remove_from_favorites(product_id):
    if "user_id" not in session:
        flash("Будь ласка, увійдіть.", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    favorite = Favorite.query.filter_by(user_id=user_id, product_id=product_id).first()

    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        flash("Товар видалено з обраних.", "info")
    else:
        flash("Товару немає у вашому списку обраних.", "warning")
    return redirect(url_for("favorites"))


@app.route("/favorites")
def favorites():
    if "user_id" not in session:
        flash("Будь ласка, увійдіть, щоб переглянути обрані товари.", "warning")
        return redirect(url_for("login"))
    user_id = session["user_id"]
    favorite_items = Favorite.query.filter_by(user_id=user_id).all()
    return render_template("favorites.html", favorite_items=favorite_items)


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    form = CheckoutForm()
    cart_items = []
    total_price = 0

    if "user_id" in session:
        user_id = session["user_id"]
        cart_items = CartItem.query.filter_by(user_id=user_id).all()
        # Заповнюємо форму даними користувача, якщо він залогінений
        user = User.query.get(user_id)
        if user:
            form.full_name.data = user.name
            form.email.data = user.email
            # Телефон та адреса можуть бути додані до моделі User, якщо вони постійно зберігаються

    if not cart_items:
        flash("Ваш кошик порожній.", "warning")
        return redirect(url_for("index"))

    for item in cart_items:
        total_price += item.product.price * item.quantity

    if form.validate_on_submit():
        user_id = session.get("user_id")
        order = Order(
            user_id=user_id,
            full_name=form.full_name.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            delivery_method=form.delivery_method.data,
            comment=form.comment.data,
            status="очікує"
        )
        db.session.add(order)
        db.session.flush()  # To get order.id before committing

        for item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.product.price
            )
            db.session.add(order_item)
            # Зменшуємо кількість товару на складі
            item.product.stock -= item.quantity
            if item.product.stock < 0:
                item.product.stock = 0  # Не допускаємо від'ємної кількості

        # Очищаємо кошик після оформлення замовлення
        for item in cart_items:
            db.session.delete(item)

        db.session.commit()
        flash("Замовлення успішно оформлено!", "success")
        return redirect(url_for("index"))

    return render_template("checkout.html", form=form, cart_items=cart_items, total_price=total_price)


@app.route("/admin/orders")
@admin_required
def admin_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template("admin/orders.html", orders=orders)


@app.route("/admin/orders/<int:order_id>")
@admin_required
def admin_order_view(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template("admin/order_view.html", order=order)


@app.route("/admin/orders/<int:order_id>/status", methods=["POST"])
@admin_required
def admin_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get("status")

    if new_status in ["очікує", "обробляється", "доставлено"]:
        order.status = new_status
        db.session.commit()
        flash("Статус оновлено", "success")
    else:
        flash("Недійсний статус", "danger")

    return redirect(url_for("admin_order_view", order_id=order_id))