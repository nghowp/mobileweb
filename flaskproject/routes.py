# import json
import logging
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Blueprint,
    abort,
    json,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from flaskproject import db, login, utils
from flaskproject.models import (
    Category,
    Product,
    Receipt,
    ReceiptDetail,
    User,
    UserRole,
)
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func
from sqlalchemy.sql.functions import coalesce

bp = Blueprint("main", __name__)


@bp.context_processor
def common_response():
    return {"cart_stats": utils.count_cart(session.get("cart"))}


def admin_required(f):
    """
    Decorator tùy chỉnh để đảm bảo người dùng là ADMIN.
    Phải được đặt SAU @login_required.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.userrole != UserRole.ADMIN:
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


@bp.route("/")
def home():
    css_file = [
        "css/style.css",
        "css/topnav.css",
        "css/header.css",
        "css/banner.css",
        "css/taikhoan.css",
        "css/trangchu.css",
        "css/home_products.css",
        "css/pagination_phantrang.css",
        "css/footer.css",
    ]
    cate_id = request.args.get("category_id", type=int)
    cates = utils.load_categories()
    kw = request.args.get("keyword")
    from_price = request.args.get("from_price")
    to_price = request.args.get("to_price")
    page = request.args.get("page", 1, type=int)
    price_range = request.args.get("price_range")
    sort_key = request.args.get("sort")

    if price_range:
        try:
            parts = price_range.split("-")
            if len(parts) == 2:
                from_price = parts[0]
                to_price = parts[1]
        except Exception as e:
            print(f"Error parsing price_range: {e}")

    pagination = utils.load_products(
        cate_id=cate_id,
        kw=kw,
        from_price=from_price,
        to_price=to_price,
        page=page,
        sort_key=sort_key,
    )
    products = pagination.items
    if "HX-Request" in request.headers:
        return render_template(
            "partials/_htmx_response.html",
            products=products,
            pagination=pagination,
            categories=cates,
            current_category_id=cate_id,
        )
    return render_template(
        "blog/index.html",
        title="Thế giới di động",
        css_file=css_file,
        categories=cates,
        products=products,
        pagination=pagination,
        current_category_id=cate_id,
    )


@bp.route("/login", methods=["GET", "POST"])
def user_login():
    err_msg = ""
    if request.method.__eq__("POST"):
        username = request.form.get("username")
        password = request.form.get("password")

        user = utils.check_login(username=username, password=password)
        if user:
            login_user(user=user)
            print(
                f"DEBUG: Đăng nhập thành công! User: {user.username}, Vai trò: {user.userrole}"
            )
            # Kiểm tra vào trò khi login
            if user.userrole == UserRole.ADMIN:
                return redirect(url_for("main.admin"))

            next = request.args.get("next", "main.home")
            return redirect(url_for(next))
        else:
            err_msg = "Username hoặc Password không chính xác!"
    return render_template("auth/login.html", err_msg=err_msg)


@bp.route("/user-logout")
def user_signout():
    logout_user()
    return redirect(url_for("main.home"))


@login.user_loader
def user_load(user_id):
    return utils.get_user_by_id(user_id=user_id)


@bp.route("/register", methods=["GET", "POST"])
def register():
    err_msg = ""
    if request.method.__eq__("POST"):
        name = request.form.get("name")
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm = request.form.get("confirm")
        try:
            if password.strip().__eq__(confirm.strip()):
                utils.add_user(
                    name=name, username=username, email=email, password=password
                )
                return redirect(url_for("main.home"))
            else:
                err_msg = "Mật khẩu không khớp!!!"
        except Exception as e:
            err_msg = "Hệ thống có lỗi" + str(e)

    return render_template("auth/register.html", err_msg=err_msg)


@bp.route("/cart")
def cart():
    return render_template(
        "blog/cart.html", stats=utils.count_cart(session.get("cart", {}))
    )


@bp.route("/api/add-cart", methods=["POST"])
def add_to_cart():
    data = request.json
    id = str(data.get("id"))
    name = data.get("name")
    price = float(data.get("price"))
    img = data.get("img")
    quantity = int(data.get("quantity"))

    cart = session.get("cart")
    if not cart:
        cart = {}

    if id in cart:

        cart[id]["quantity"] = cart[id]["quantity"] + quantity
    else:

        cart[id] = {
            "id": id,
            "name": name,
            "price": price,
            "quantity": quantity,
            "img": img,
        }

    session["cart"] = cart

    return jsonify(utils.count_cart(cart=cart))


@bp.route("/api/remove-cart", methods=["POST"])
def remove_from_cart():
    try:
        data = request.json
        id_to_remove = str(data.get("id"))

        cart = session.get("cart")
        if cart and id_to_remove in cart:
            cart.pop(id_to_remove, None)
            session["cart"] = cart
            return (
                jsonify(
                    {
                        "code": 200,
                        "message": "Xóa thành công",
                        "stats": utils.count_cart(cart),
                    }
                ),
                200,
            )
        else:
            return (
                jsonify({"code": 404, "error": "Sản phẩm không tìm thấy trong giỏ"}),
                404,
            )

    except Exception as e:
        print(f"Lỗi khi xóa giỏ hàng: {e}")
        return jsonify({"code": 500, "error": "Lỗi máy chủ nội bộ"}), 500


@bp.route("/pay")
@login_required
def methods_pay():
    product_id = request.args.get("product_id", type=int)

    if product_id:
        product = Product.query.get(product_id)

        if product:
            cart_data = {
                str(product.id): {
                    "id": str(product.id),
                    "name": product.name,
                    "price": product.price,
                    "quantity": 1,
                    "img": product.image,
                }
            }
            session["cart"] = cart_data
            session.modified = True
        else:
            session["cart"] = {}
            session.modified = True
    cart_data = session.get("cart", {})
    return render_template("blog/pay.html", cart_items=cart_data)


@bp.route("/process-order", methods=["POST"])
@login_required
def process_order():
    # data = request.get_json()
    cart = session.get("cart", {})

    if not cart:
        return jsonify({"success": False, "error": "Giỏ hàng của bạn trống."}), 400

    try:
        data = request.get_json() or {}
        current_user_id = current_user.id
        utils.add_receipt(
            cart_from_session=cart, user_id=current_user_id, shipping_info=data
        )
        # Xóa giỏ hàng sau khi lưu thành công
        session["cart"] = {}
        session.modified = True

        return jsonify(
            {
                "success": True,
                "fullName": data.get("fullName"),
                "phone": data.get("phone"),
            }
        )
    except Exception as e:
        logging.error(f"LỖI khi xử lý đơn hàng: {e}")
        return (
            jsonify({"success": False, "error": f"Không thể xử lý đơn hàng: {str(e)}"}),
            500,
        )


@bp.route("/product/<int:product_id>")
def products_details(product_id):
    product = Product.query.get_or_404(product_id)
    flash_price = utils.get_current_flash_sale_price(product_id)

    if flash_price is not None:

        product.old_price = product.price

        product.price = flash_price
    return render_template("blog/products_details.html", product=product)


@bp.route("/api/get-flash-sale")
def get_flash_sale():
    cache_file_path = "flash_sale_cache.json"
    now = datetime.now()
    sale_duration_hours = 3

    try:
        with open(cache_file_path, "r") as f:
            cache = json.load(f)
        sale_start_time = datetime.fromisoformat(cache["start_time"])
    except FileNotFoundError:
        cache = {}
        sale_start_time = now - timedelta(days=1)

    if now > sale_start_time + timedelta(hours=sale_duration_hours):

        new_products_list = utils.get_new_flash_sale_data(count=5)

        if new_products_list:
            sale_start_time = now
            cache = {
                "products": new_products_list,
                "start_time": sale_start_time.isoformat(),
            }

            with open(cache_file_path, "w") as f:
                json.dump(cache, f, indent=4)
        else:
            return jsonify({"error": "No active flash sale products"}), 404

    sale_end_time = sale_start_time + timedelta(hours=sale_duration_hours)

    return jsonify(
        {
            "products": cache.get("products", []),
            "sale_end_time": sale_end_time.isoformat(),
        }
    )


@bp.route("/admin")
@login_required
@admin_required
def admin():
    return render_template("admin/admin_panel.html")


@bp.route("/api/admin/dashboard_stats")
@login_required
def get_dashboard_stats():
    """
    API cung cấp số liệu thống kê bằng cách truy vấn database.
    """
    try:
        total_revenue = (
            db.session.query(func.sum(coalesce(Receipt.total_price, 0))).scalar() or 0
        )
        new_orders = db.session.query(func.count(Receipt.id)).scalar() or 0

        new_users = db.session.query(func.count(User.id)).scalar() or 0

        visits = 0

        display_revenue = f"{total_revenue:,.0f}đ"

        return jsonify(
            {
                "total_revenue": display_revenue,
                "new_orders": new_orders,
                "new_users": new_users,
                "visits": visits,
            }
        )

    except Exception as e:
        print(f"LỖI khi lấy admin stats: {e}")
        return jsonify({"error": "Không thể tải dữ liệu thống kê"}), 500


@bp.route("/api/admin/recent_orders")
@login_required
@admin_required
def get_recent_orders():
    """
    API cung cấp 5 đơn hàng gần nhất bằng cách truy vấn database.
    """
    try:
        recent_orders_db = (
            db.session.query(Receipt, User)
            .join(User, Receipt.user_id == User.id)
            .order_by(Receipt.created_date.desc())
            .limit(5)
            .all()
        )

        orders_list = []
        for receipt, user in recent_orders_db:
            status = getattr(receipt, "status", "Đang xử lý")
            status_color = "yellow"
            if status == "Đã giao":
                status_color = "green"
            elif status == "Đã hủy":
                status_color = "red"
            total_display = (
                f"{receipt.total_price:,.0f}đ"
                if receipt.total_price is not None
                else "0đ"
            )
            date_display = (
                receipt.created_date.strftime("%d/%m/%Y")
                if receipt.created_date is not None
                else "Không rõ"
            )
            orders_list.append(
                {
                    "id": f"#{receipt.id}",
                    "customer": user.name,
                    "date": date_display,
                    "total": total_display,
                    "status": status,
                    "status_color": status_color,
                }
            )

        return jsonify(orders=orders_list)

    except Exception as e:
        print(f"LỖI khi lấy recent orders: {e}")
        return jsonify({"error": "Không thể tải đơn hàng gần đây"}), 500


@bp.route("/admin/orders")
@login_required
@admin_required
def admin_orders():
    return render_template("admin/admin_orders.html")


@bp.route("/api/admin/all_orders")
@login_required
@admin_required
def get_all_orders():
    """
    API cung cấp TẤT CẢ đơn hàng với phân trang, tìm kiếm và lọc.
    """
    try:
        page = request.args.get("page", 1, type=int)
        search_term = request.args.get("search", "")
        status_term = request.args.get("status", "")

        query = db.session.query(Receipt, User).join(User, Receipt.user_id == User.id)

        if search_term:
            search_like = f"%{search_term}%"
            try:
                search_id = int(search_term.lstrip("#"))
                query = query.filter(
                    db.or_(User.name.ilike(search_like), Receipt.id == search_id)
                )
            except ValueError:
                query = query.filter(User.name.ilike(search_like))

        if status_term:
            query = query.filter(Receipt.status == status_term)

        pagination = query.order_by(Receipt.created_date.desc()).paginate(
            page=page, per_page=10, error_out=False
        )

        orders_on_page = pagination.items

        orders_list = []
        for receipt, user in orders_on_page:
            status = receipt.status
            status_color = "yellow"
            if status == "Đã giao":
                status_color = "green"
            elif status == "Đã hủy":
                status_color = "red"

            total_display = (
                f"{receipt.total_price:,.0f}đ"
                if receipt.total_price is not None
                else "0đ"
            )
            date_display = (
                receipt.created_date.strftime("%d/%m/%Y")
                if receipt.created_date is not None
                else "Không rõ"
            )

            orders_list.append(
                {
                    "id": f"#{receipt.id}",
                    "id_raw": receipt.id,
                    "customer": user.name,
                    "date": date_display,
                    "total": total_display,
                    "status": status,
                    "status_color": status_color,
                }
            )

        pagination_info = {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_pages": pagination.pages,
            "total_items": pagination.total,
            "has_prev": pagination.has_prev,
            "prev_page": pagination.prev_num,
            "has_next": pagination.has_next,
            "next_page": pagination.next_num,
            "iter_pages": [
                p
                for p in pagination.iter_pages(
                    left_edge=1, right_edge=1, left_current=2, right_current=2
                )
            ],
        }

        return jsonify(orders=orders_list, pagination=pagination_info)

    except Exception as e:
        print(f"LỖI khi lấy all orders: {e}")
        return jsonify({"error": "Không thể tải danh sách đơn hàng"}), 500


@bp.route("/api/admin/update_order_status/<int:order_id>", methods=["POST"])
@login_required
@admin_required
def update_order_status(order_id):
    """
    API để admin cập nhật trạng thái của một đơn hàng (ví dụ: Đã giao, Đã hủy).
    """
    try:
        data = request.get_json()
        new_status = data.get("status")

        if not new_status:
            return jsonify({"success": False, "error": "Thiếu trạng thái mới"}), 400

        order = Receipt.query.get(order_id)
        if not order:
            return jsonify({"success": False, "error": "Không tìm thấy đơn hàng"}), 404

        # Cập nhật trạng thái
        order.status = new_status
        db.session.commit()

        return jsonify({"success": True, "message": "Cập nhật trạng thái thành công"})

    except Exception as e:
        print(f"LỖI khi cập nhật status: {e}")
        return jsonify({"success": False, "error": "Lỗi máy chủ"}), 500


@bp.route("/admin/products")
@login_required
@admin_required
def admin_products():
    """Render trang quản lý sản phẩm"""
    try:
        categories = utils.load_categories()
    except Exception as e:
        print(f"LỖI khi tải categories cho admin: {e}")
        categories = []

    return render_template("admin/admin_products.html", categories=categories)


@bp.route("/api/admin/all_products")
@login_required
@admin_required
def get_all_products():
    """
    API cung cấp TẤT CẢ sản phẩm với phân trang, tìm kiếm và lọc.
    """
    try:
        page = request.args.get("page", 1, type=int)
        search_term = request.args.get("search", "")
        category_id = request.args.get("category_id", type=int)

        query = db.session.query(Product, Category).join(
            Category, Product.category_id == Category.id
        )

        # Áp dụng bộ lọc tìm kiếm
        if search_term:
            query = query.filter(Product.name.ilike(f"%{search_term}%"))

        # Áp dụng bộ lọc danh mục
        if category_id:
            query = query.filter(Product.category_id == category_id)

        # Phân trang
        pagination = query.order_by(Product.id.asc()).paginate(
            page=page, per_page=10, error_out=False
        )

        products_on_page = pagination.items

        # Định dạng dữ liệu trả về giống như JS mong đợi
        products_list = []
        for product, category in products_on_page:
            products_list.append(
                {
                    "id": product.id,
                    "image": (
                        url_for("static", filename=product.image)
                        if product.image
                        else url_for("static", filename="img/default.png")
                    ),
                    "name": product.name,
                    "price": f"{product.price:,.0f}đ",
                    "category": category.name,
                }
            )

        # Tạo thông tin phân trang (giống hệt trang đơn hàng)
        pagination_info = {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_pages": pagination.pages,
            "total_items": pagination.total,
            "has_prev": pagination.has_prev,
            "prev_page": pagination.prev_num,
            "has_next": pagination.has_next,
            "next_page": pagination.next_num,
            "iter_pages": [
                p
                for p in pagination.iter_pages(
                    left_edge=1, right_edge=1, left_current=2, right_current=2
                )
            ],
        }

        return jsonify(products=products_list, pagination=pagination_info)

    except Exception as e:
        print(f"LỖI khi lấy all products: {e}")
        return jsonify({"error": "Không thể tải danh sách sản phẩm"}), 500


@bp.route("/api/admin/delete_product/<int:product_id>", methods=["DELETE"])
@login_required
@admin_required
def delete_product(product_id):
    """
    API để admin XÓA một sản phẩm.
    """
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({"success": False, "error": "Không tìm thấy sản phẩm"}), 404

        # Thử xóa
        db.session.delete(product)
        db.session.commit()

        return jsonify({"success": True, "message": "Xóa sản phẩm thành công"})

    except IntegrityError:
        db.session.rollback()
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Không thể xóa. Sản phẩm này đã tồn tại trong một đơn hàng đã đặt.",
                }
            ),
            400,
        )  # 400 Bad Request

    except Exception as e:
        db.session.rollback()
        print(f"LỖI khi xóa sản phẩm: {e}")
        return jsonify({"success": False, "error": "Lỗi máy chủ không xác định"}), 500


@bp.route("/admin/product/add", methods=["GET", "POST"])
@login_required
@admin_required
def admin_product_add():
    """
    Route để HIỂN THỊ (GET) và XỬ LÝ (POST) form thêm sản phẩm mới.
    """

    try:
        categories = utils.load_categories()
    except Exception as e:
        print(f"LỖI khi tải categories cho form: {e}")
        categories = []

    if request.method == "POST":
        try:
            name = request.form.get("name")
            price = request.form.get("price", 0, type=float)
            description = request.form.get("description", "")
            screen = request.form.get("screen", "")
            operating = request.form.get("operating", "")
            camera_f = request.form.get("camera_f", "")
            camera_a = request.form.get("camera_a", "")
            cpu = request.form.get("cpu", "")
            ram = request.form.get("ram", "")
            store = request.form.get("store", "")
            battery = request.form.get("battery", "")
            image_path = request.form.get("image", "")
            stock = request.form.get("stock_quantity", 0, type=int)
            category_id = request.form.get("category_id", type=int)

            new_product = Product(
                name=name,
                price=price,
                description=description,
                screen=screen,
                operating=operating,
                camera_f=camera_f,
                camera_a=camera_a,
                CPU=cpu,
                RAM=ram,
                store=store,
                battery=battery,
                image=image_path,
                stock_quantity=stock,
                category_id=category_id,
            )

            db.session.add(new_product)
            db.session.commit()

            return redirect(url_for("main.admin_products"))

        except Exception as e:
            db.session.rollback()
            print(f"LỖI khi thêm sản phẩm mới: {e}")

            return render_template(
                "admin/admin_product_form.html",
                categories=categories,
                error=str(e),
                product=request.form,
            )

    return render_template(
        "admin/admin_products_form.html", categories=categories, product={}
    )


@bp.route("/admin/user")
@login_required
@admin_required
def admin_user():
    """
    Route để render trang HTML Quản lý Người dùng.
    """
    return render_template("admin/admin_user.html")


@bp.route("/api/admin/all_users")
@login_required
@admin_required
def get_all_users():
    """
    API cung cấp TẤT CẢ người dùng với phân trang, tìm kiếm và lọc.
    """
    try:
        page = request.args.get("page", 1, type=int)
        search_term = request.args.get("search", "")
        role = request.args.get("role", "")

        query = User.query

        if search_term:
            search_like = f"%{search_term}%"
            query = query.filter(
                or_(
                    User.name.ilike(search_like),
                    User.username.ilike(search_like),
                    User.email.ilike(search_like),
                )
            )

        if role:
            if role.lower() == "admin":
                query = query.filter(User.userrole == UserRole.ADMIN)
            elif role.lower() == "user":
                query = query.filter(User.userrole == UserRole.USER)

        pagination = query.order_by(User.id.asc()).paginate(
            page=page, per_page=10, error_out=False
        )

        users_on_page = pagination.items

        users_list = []
        for user in users_on_page:
            users_list.append(
                {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "role": "Admin" if user.userrole == UserRole.ADMIN else "User",
                    "join_date": user.joined_date.strftime("%d/%m/%Y"),
                }
            )

        pagination_info = {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_pages": pagination.pages,
            "total_items": pagination.total,
            "has_prev": pagination.has_prev,
            "prev_page": pagination.prev_num,
            "has_next": pagination.has_next,
            "next_page": pagination.next_num,
            "iter_pages": [
                p
                for p in pagination.iter_pages(
                    left_edge=1, right_edge=1, left_current=2, right_current=2
                )
            ],
        }

        return jsonify(users=users_list, pagination=pagination_info)

    except Exception as e:
        print(f"LỖI khi lấy all users: {e}")
        return jsonify({"error": "Không thể tải danh sách người dùng"}), 500


@bp.route("/api/admin/delete_user/<int:user_id>", methods=["DELETE"])
@login_required
@admin_required
def delete_user(user_id):
    """
    API để admin XÓA một người dùng.
    """
    try:
        if user_id == current_user.id:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Bạn không thể tự xóa tài khoản của mình.",
                    }
                ),
                400,
            )

        user = User.query.get(user_id)
        if not user:
            return (
                jsonify({"success": False, "error": "Không tìm thấy người dùng"}),
                404,
            )

        if user.receipt:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Không thể xóa. Người dùng này đã có đơn hàng.",
                    }
                ),
                400,
            )

        db.session.delete(user)
        db.session.commit()

        return jsonify({"success": True, "message": "Xóa người dùng thành công"})

    except IntegrityError:
        db.session.rollback()
        return (
            jsonify(
                {"success": False, "error": "Không thể xóa do ràng buộc cơ sở dữ liệu."}
            ),
            400,
        )

    except Exception as e:
        db.session.rollback()
        print(f"LỖI khi xóa user: {e}")
        return jsonify({"success": False, "error": "Lỗi máy chủ không xác định"}), 500
