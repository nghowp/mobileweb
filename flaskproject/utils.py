import hashlib
import json
import random
from datetime import datetime, timedelta

from flask import current_app
from flask_login import current_user
from flaskproject import create_app, db
from flaskproject.models import (
    Category,
    FlashSale,
    Product,
    Receipt,
    ReceiptDetail,
    User,
)
from sqlalchemy.sql import func


def load_categories():
    return Category.query.all()


def load_products(
    cate_id=None, kw=None, from_price=None, to_price=None, page=1, sort_key=None
):
    products = Product.query.filter(Product.active.is_(True))
    if cate_id:
        try:
            cid = int(cate_id)
            products = products.filter(Product.category_id == cid)
        except ValueError:
            pass

    if kw:
        products = products.filter(Product.name.contains(kw))

    if from_price:
        try:
            fp = float(from_price)
            if fp > 0:
                products = products.filter(Product.price >= fp)
        except ValueError:
            pass

    if to_price:
        try:
            tp = float(to_price)
            if tp > 0:
                products = products.filter(Product.price <= tp)
        except ValueError:
            pass

    # Thêm logic sắp xếp
    ordering = Product.id.asc()

    if sort_key == "price_asc":
        ordering = Product.price.asc()
    elif sort_key == "price_desc":
        ordering = Product.price.desc()
    elif sort_key == "lastest":
        ordering = Product.id.desc()

    page_size = current_app.config["PAGE_SIZE"]
    pagination = products.order_by(ordering).paginate(  # desc: giảm dần, asc: tăng dần
        page=page, per_page=page_size, error_out=False
    )
    return pagination


def get_new_flash_sale_data(count=5):
    """
    Hàm này lấy 'count' sản phẩm, tính toán giá sale mới, trả về một list đầy đủ thông tin.
    """
    deals = (
        FlashSale.query.filter_by(is_active=True)
        .order_by(func.rand())
        .limit(count)
        .all()
    )

    products_list = []
    for deal in deals:
        if not deal.product:
            continue  # Bỏ qua nếu deal bị lỗi (không có sản phẩm)
        # lấy giá gốc từ product
        original_price = deal.product.price
        # tính % giảm giá
        discount_percent = random.uniform(
            deal.min_discount_percent, deal.max_discount_percent
        )
        # tính giá bán mới
        sale_price = original_price * (1 - (discount_percent / 100.0))
        # làm tròn giá
        sale_price = round(sale_price, -3)
        if original_price > 0:
            actual_discount_percent = (
                (original_price - sale_price) / original_price
            ) * 100
        else:
            actual_discount_percent = 0
        # làm tròn % thành số nguyên
        discount_percent_int = int(round(actual_discount_percent, 0))
        # thêm vào list kết quả
        products_list.append(
            {
                "product_id": deal.product_id,
                "name": deal.product.name,
                "image_url": deal.product.image,
                "original_price": int(original_price),
                "flash_sale_price": int(sale_price),
                "discount_percent": discount_percent_int,
            }
        )
    return products_list


def add_user(name, username, email, password):
    password = str(hashlib.md5(password.strip().encode("utf-8")).hexdigest())
    user = User(
        name=name.strip(),
        username=username.strip(),
        email=email.strip(),
        password=password,
    )
    db.session.add(user)
    db.session.commit()


def check_login(username, password):
    if username and password:
        password = str(hashlib.md5(password.strip().encode("utf-8")).hexdigest())

        return User.query.filter(
            User.username.__eq__(username.strip()), User.password.__eq__(password)
        ).first()


def get_user_by_id(user_id):
    return User.query.get(user_id)


# Tạo hàm thêm hóa đơn (receipt)
def add_receipt(cart_from_session, user_id, shipping_info=None):
    if shipping_info is None:
        shipping_info = {}
    try:
        new_receipt = Receipt(
            user_id=user_id,
            created_date=datetime.now(),
            customer_name=shipping_info.get("fullName", ""),
            shipping_phone=shipping_info.get("phone", ""),
            shipping_address=shipping_info.get("address", ""),
            payment_method=shipping_info.get("paymentMethod", "cod"),
        )
        db.session.add(new_receipt)

        total_price = 0
        total_quantity = 0
        product_ids_in_cart = cart_from_session.keys()

        products_in_db = Product.query.filter(Product.id.in_(product_ids_in_cart)).all()
        real_price_map = {str(p.id): p.price for p in products_in_db}

        for product_id_str, item_in_cart in cart_from_session.items():
            real_unit_price = real_price_map.get(product_id_str)
            quantity = int(item_in_cart["quantity"])
            # (Giả sử code của bạn đang làm điều này)
            rd = ReceiptDetail(
                receipt=new_receipt,
                product_id=int(product_id_str),
                quantity=quantity,
                unit_price=real_unit_price,
            )
            db.session.add(rd)
            total_price += real_unit_price * quantity
            total_quantity += quantity
        new_receipt.total_price = total_price
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e


def count_cart(cart):
    total_quantity, total_amount = 0, 0

    if cart:
        for c in cart.values():
            total_quantity += c["quantity"]
            total_amount += int(c["quantity"]) * float(c["price"])

    return {"total_quantity": total_quantity, "total_amount": total_amount}


def get_current_flash_sale_price(product_id):
    """
    Kiểm tra cache flash sale xem sản phẩm có đang được giảm giá không.
    Trả về giá sale nếu có và còn hạn, ngược lại trả về None.
    """
    cache_file_path = "flash_sale_cache.json"
    sale_duration_hours = 3
    now = datetime.now()

    try:
        with open(cache_file_path, "r") as f:
            cache = json.load(f)

        sale_start_time = datetime.fromisoformat(cache["start_time"])

        if now <= sale_start_time + timedelta(hours=sale_duration_hours):
            for sale_product in cache.get("products", []):
                if sale_product.get("product_id") == product_id:
                    return sale_product.get("flash_sale_price")

    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError):
        pass

    return None
